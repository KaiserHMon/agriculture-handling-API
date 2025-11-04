from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.auth import get_current_active_user
from ...db.database import get_db
from ...exceptions.api_exceptions import DatabaseError, NotFoundError
from ...models.user_model import User, UserRole
from ...schema.plot_schema import (
    PlotCreate,
    PlotResponse,
    PlotUpdate,
)
from ...services.plot_service import PlotService

router = APIRouter(prefix="/plots", tags=["Plots"])


@router.post("/", response_model=PlotResponse, status_code=status.HTTP_201_CREATED)
async def create_plot(
    payload: PlotCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PlotResponse:
    """Create a new plot. Farmers can only create plots for themselves."""
    # Farmers can only create plots for themselves
    if current_user.role == UserRole.FARMER and payload.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Farmers can only create plots for themselves",
        )

    # Advisors cannot create plots
    if current_user.role == UserRole.ADVISOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Advisors cannot create plots",
        )

    service = PlotService(db)
    try:
        plot = await service.create(payload.model_dump())
        return PlotResponse.model_validate(plot, from_attributes=True)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/", response_model=list[PlotResponse])
async def list_plots(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PlotResponse]:
    """Get all plots. Farmers only see their own plots."""
    service = PlotService(db)
    try:
        if current_user.role == UserRole.FARMER:
            plots = await service.get_user_plots(current_user.id)
        elif current_user.role == UserRole.ADVISOR:
            # Advisors can see plots they have made recommendations for
            # For now, return none until we implement advisor-plot relationship
            return []
        else:
            # Admin sees all
            plots = await service.get_all()
        return [PlotResponse.model_validate(plot, from_attributes=True) for plot in plots]
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{plot_id}", response_model=PlotResponse)
async def get_plot(
    plot_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PlotResponse:
    """Get a plot by id."""
    service = PlotService(db)
    try:
        plot = await service.get(plot_id)
        if current_user.role == UserRole.FARMER and plot.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this plot",
            )
        elif current_user.role == UserRole.ADVISOR:
            # Verificar si el asesor tiene acceso a través de recomendaciones
            has_access = await service.validate_advisor_plot_access(plot.id, current_user.id)
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Advisors can only access plots where they have made recommendations",
                )
        return PlotResponse.from_orm(plot)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.patch("/{plot_id}", response_model=PlotResponse)
async def update_plot(
    plot_id: int,
    payload: PlotUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PlotResponse:
    """Update a plot. Farmers can only update their own plots."""
    service = PlotService(db)
    try:
        # Check plot ownership
        plot = await service.get(plot_id)
        if current_user.role == UserRole.FARMER and plot.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update this plot",
            )
        elif current_user.role == UserRole.ADVISOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Advisors cannot modify plots",
            )
        updated_plot = await service.update(plot_id, payload.dict(exclude_unset=True))
        return PlotResponse.from_orm(updated_plot)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/{plot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plot(
    plot_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a plot. ADMIN can delete any plot, FARMER can delete their own plots."""
    service = PlotService(db)
    try:
        plot = await service.get(plot_id)
        if not plot:
            raise HTTPException(status_code=404, detail=f"Plot {plot_id} not found")

        # Check permissions
        if current_user.role == UserRole.FARMER:
            if plot.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Farmers can only delete their own plots",
                )
        elif current_user.role == UserRole.ADVISOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Advisors cannot delete plots",
            )

        await service.delete(plot_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{plot_id}/events", response_model=PlotResponse)
async def get_plot_with_events(
    plot_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PlotResponse:
    """Get a plot with all its events."""
    service = PlotService(db)
    try:
        plot = await service.get_plot_with_events(plot_id)
        if current_user.role == UserRole.FARMER and plot.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this plot",
            )
        elif current_user.role == UserRole.ADVISOR:
            # Verificar si el asesor tiene acceso a través de recomendaciones
            has_access = await service.validate_advisor_plot_access(plot.id, current_user.id)
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Advisors can only access plots where they have made recommendations",
                )
        return PlotResponse.from_orm(plot)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{plot_id}/recommendations", response_model=PlotResponse)
async def get_plot_with_recommendations(
    plot_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PlotResponse:
    """Get a plot with all its recommendations."""
    service = PlotService(db)
    try:
        plot = await service.get_plot_with_recommendations(plot_id)
        if current_user.role == UserRole.FARMER and plot.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this plot",
            )
        elif current_user.role == UserRole.ADVISOR:
            # Verificar si el asesor tiene acceso a través de recomendaciones
            has_access = await service.validate_advisor_plot_access(plot.id, current_user.id)
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Advisors can only access plots where they have made recommendations",
                )
        return PlotResponse.from_orm(plot)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/campaign/{campaign_id}", response_model=list[PlotResponse])
async def get_campaign_plots(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PlotResponse]:
    """Get all plots for a campaign."""
    service = PlotService(db)
    try:
        plots = await service.get_campaign_plots(campaign_id)
        filtered_plots = []
        if current_user.role == UserRole.FARMER:
            # Filter plots for farmer
            filtered_plots = [p for p in plots if p.user_id == current_user.id]
        elif current_user.role == UserRole.ADVISOR:
            # Filtrar parcelas donde el asesor ha hecho recomendaciones
            filtered_plots = [
                p
                for p in plots
                if await service.validate_advisor_plot_access(p.id, current_user.id)
            ]
        else:
            filtered_plots = plots
        return [PlotResponse.from_orm(p) for p in filtered_plots]
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/user/{user_id}", response_model=list[PlotResponse])
async def get_user_plots(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PlotResponse]:
    """Get all plots for a user. Only ADMIN can view other users' plots."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view plots by user",
        )

    service = PlotService(db)
    try:
        plots = await service.get_user_plots(user_id)
        return [PlotResponse.model_validate(plot, from_attributes=True) for plot in plots]
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/location/{location}", response_model=list[PlotResponse])
async def get_plots_by_location(
    location: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PlotResponse]:
    """Get all plots in a location."""
    service = PlotService(db)
    try:
        plots = await service.get_plots_by_location(location)
        filtered_plots = []
        if current_user.role == UserRole.FARMER:
            # Filter plots for farmer
            filtered_plots = [p for p in plots if p.user_id == current_user.id]
        elif current_user.role == UserRole.ADVISOR:
            # Filtrar parcelas donde el asesor ha hecho recomendaciones
            filtered_plots = [
                p
                for p in plots
                if await service.validate_advisor_plot_access(p.id, current_user.id)
            ]
        else:
            filtered_plots = plots
        return [PlotResponse.from_orm(p) for p in filtered_plots]
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
