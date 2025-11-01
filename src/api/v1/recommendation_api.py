from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.auth import get_current_active_user
from ...db.database import get_db
from ...exceptions.api_exceptions import DatabaseError, NotFoundError
from ...models.user_model import User, UserRole
from ...schema.recommendation_schema import (
    RecommendationCreate,
    RecommendationResponse,
    RecommendationUpdate,
    RecommendationWithPlot,
)
from ...services.plot_service import PlotService
from ...services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post("/", response_model=RecommendationResponse, status_code=status.HTTP_201_CREATED)
async def create_recommendation(
    payload: RecommendationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    """Create a new recommendation. Only ADMIN and ADVISOR can create recommendations."""
    if current_user.role == UserRole.FARMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Farmers cannot create recommendations",
        )

    # Ensure advisor_id matches the current user if they're an advisor
    if current_user.role == UserRole.ADVISOR and payload.advisor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Advisors can only create recommendations as themselves",
        )

    service = RecommendationService(db)
    plot_service = PlotService(db)
    try:
        # Verify plot exists
        plot = await plot_service.get(payload.plot_id)
        if not plot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plot {payload.plot_id} not found",
            )

        # Create recommendation
        recommendation = await service.create(payload.model_dump())
        return RecommendationResponse.model_validate(recommendation, from_attributes=True)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/", response_model=list[RecommendationResponse])
async def list_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[RecommendationResponse]:
    """Get all recommendations. Only ADMIN has access to all recommendations."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can list all recommendations",
        )

    service = RecommendationService(db)
    try:
        recommendations = await service.get_all()
        return [
            RecommendationResponse.model_validate(rec, from_attributes=True)
            for rec in recommendations
        ]
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{recommendation_id}", response_model=RecommendationWithPlot)
async def get_recommendation(
    recommendation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RecommendationWithPlot:
    """Get a recommendation with plot details."""
    service = RecommendationService(db)
    try:
        recommendation = await service.get_recommendation_with_plot(recommendation_id)

        # Check permissions
        if current_user.role == UserRole.ADVISOR:
            if recommendation.advisor_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Advisors can only view their own recommendations",
                )
        elif current_user.role == UserRole.FARMER:
            # Check if recommendation is for farmer's plot
            plot_service = PlotService(db)
            plot = await plot_service.get(recommendation.plot_id)
            if plot.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Farmers can only view recommendations for their plots",
                )

        return RecommendationWithPlot.model_validate(recommendation, from_attributes=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.patch("/{recommendation_id}", response_model=RecommendationResponse)
async def update_recommendation(
    recommendation_id: int,
    payload: RecommendationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    """Update a recommendation. Only the creator or ADMIN can update."""
    service = RecommendationService(db)
    try:
        recommendation = await service.get(recommendation_id)
        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recommendation {recommendation_id} not found",
            )

        # Check permissions
        if current_user.role == UserRole.ADVISOR:
            if recommendation.advisor_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Advisors can only update their own recommendations",
                )
        elif current_user.role == UserRole.FARMER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Farmers cannot update recommendations",
            )

        updated_recommendation = await service.update(
            recommendation_id, payload.dict(exclude_unset=True)
        )
        return RecommendationResponse.model_validate(updated_recommendation, from_attributes=True)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.patch("/{recommendation_id}/implement", response_model=RecommendationResponse)
async def mark_as_implemented(
    recommendation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    """Mark a recommendation as implemented. Only the plot owner (FARMER) or ADMIN can do this."""
    service = RecommendationService(db)
    try:
        recommendation = await service.get_recommendation_with_plot(recommendation_id)
        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recommendation {recommendation_id} not found",
            )

        # Check permissions
        if current_user.role == UserRole.ADVISOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Advisors cannot mark recommendations as implemented",
            )
        elif current_user.role == UserRole.FARMER:
            # Verify plot ownership
            if recommendation.plot.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Farmers can only mark recommendations for their own plots",
                )

        updated_recommendation = await service.mark_as_implemented(recommendation_id)
        return RecommendationResponse.model_validate(updated_recommendation, from_attributes=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/plot/{plot_id}", response_model=list[RecommendationResponse])
async def get_plot_recommendations(
    plot_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[RecommendationResponse]:
    """Get all recommendations for a plot. Only ADMIN and plot owner can view."""
    service = RecommendationService(db)
    plot_service = PlotService(db)
    try:
        # Check plot access
        plot = await plot_service.get(plot_id)
        if not plot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plot {plot_id} not found",
            )

        # Get recommendations to check advisor access
        recommendations = await service.get_plot_recommendations(plot_id)

        # Check permissions based on role
        if current_user.role not in [UserRole.ADMIN]:
            if current_user.role == UserRole.ADVISOR:
                # Advisors can see recommendations if they made any of them
                advisor_made_recommendation = any(
                    rec.advisor_id == current_user.id for rec in recommendations
                )
                if not advisor_made_recommendation:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Advisors can only view recommendations they made",
                    )
            elif plot.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only plot owners can view their plot's recommendations",
                )

        recommendations = await service.get_plot_recommendations(plot_id)
        return [
            RecommendationResponse.model_validate(rec, from_attributes=True)
            for rec in recommendations
        ]
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/advisor/{advisor_id}", response_model=list[RecommendationResponse])
async def get_advisor_recommendations(
    advisor_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[RecommendationResponse]:
    """Get all recommendations made by an advisor. Only ADMIN and the advisor can view."""
    service = RecommendationService(db)

    # Only ADMIN and the advisor themselves can view their recommendations
    if current_user.role not in [UserRole.ADMIN]:
        if current_user.role == UserRole.FARMER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Farmers cannot view advisor recommendations directly",
            )
        if current_user.id != advisor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Advisors can only view their own recommendations",
            )

    try:
        recommendations = await service.get_advisor_recommendations(advisor_id)
        return [
            RecommendationResponse.model_validate(rec, from_attributes=True)
            for rec in recommendations
        ]
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
