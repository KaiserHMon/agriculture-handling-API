from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.auth import get_current_active_user
from ...db.database import get_db
from ...exceptions.api_exceptions import DatabaseError, NotFoundError
from ...models.user_model import User, UserRole
from ...schema.event_schema import (
    EventCreate,
    EventDateRange,
    EventInDB,
    EventResponse,
    EventUpdate,
)
from ...services.campaign_service import CampaignService
from ...services.event_service import EventService
from ...services.plot_service import PlotService

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> EventResponse:
    """
    Create a new event.
    - FARMER can create events for their own plots/campaigns
    - ADVISOR can create events for plots they advise
    - ADMIN can create events for any plot/campaign
    """
    service = EventService(db)
    plot_service = PlotService(db)
    campaign_service = CampaignService(db)

    try:
        # Verify plot exists and check access
        plot = await plot_service.get(payload.plot_id)
        if not plot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plot {payload.plot_id} not found",
            )

        # Verify campaign exists
        campaign = await campaign_service.get(payload.campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign {payload.campaign_id} not found",
            )

        # Check permissions based on role
        if current_user.role == UserRole.FARMER:
            if plot.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Farmers can only create events for their own plots",
                )
        elif current_user.role == UserRole.ADVISOR:
            # Verificar si el asesor tiene acceso a la parcela
            has_access = await plot_service.validate_advisor_plot_access(plot.id, current_user.id)
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Advisors can only create events for plots they advise",
                )

        # Set current user as creator
        event_data = EventInDB.model_validate(
            {
                **payload.model_dump(),
                "created_by_id": current_user.id,
            }
        )

        # Create event
        event = await service.create(event_data.model_dump())
        return EventResponse.model_validate(event, from_attributes=True)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/", response_model=list[EventResponse])
async def list_events(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[EventResponse]:
    """
    Get all events.
    - FARMER sees events for their plots
    - ADVISOR sees events for plots they advise
    - ADMIN sees all events
    """
    service = EventService(db)
    try:
        if current_user.role == UserRole.ADMIN:
            events = await service.get_all()
        else:
            events = await service.get_user_events(current_user.id)

        return [EventResponse.model_validate(event, from_attributes=True) for event in events]
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> EventResponse:
    """
    Get an event by ID.
    - Users can only view events they created or for plots they have access to
    """
    service = EventService(db)
    try:
        event = await service.validate_event_ownership(event_id, current_user.id, allow_admin=True)
        return EventResponse.model_validate(event, from_attributes=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    payload: EventUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> EventResponse:
    """
    Update an event.
    - Users can only update events they created
    - ADMIN can update any event
    """
    service = EventService(db)
    try:
        await service.validate_event_ownership(event_id, current_user.id, allow_admin=True)

        updated_event = await service.update(event_id, payload.model_dump(exclude_unset=True))
        return EventResponse.model_validate(updated_event, from_attributes=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete an event.
    - Users can only delete events they created
    - ADMIN can delete any event
    """
    service = EventService(db)
    try:
        await service.validate_event_ownership(event_id, current_user.id, allow_admin=True)
        await service.delete(event_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/plot/{plot_id}", response_model=list[EventResponse])
async def get_plot_events(
    plot_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[EventResponse]:
    """
    Get all events for a specific plot.
    - FARMER can only view events for their own plots
    - ADVISOR can view events for plots they advise
    - ADMIN can view events for any plot
    """
    service = EventService(db)
    plot_service = PlotService(db)
    try:
        # Verify plot exists and check access
        plot = await plot_service.get(plot_id)
        if not plot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plot {plot_id} not found",
            )

        if current_user.role == UserRole.FARMER and plot.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Farmers can only view events for their own plots",
            )
        elif current_user.role == UserRole.ADVISOR:
            # TODO: Implement check for advisor's assigned plots
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Advisors cannot view plot events yet",
            )

        events = await service.get_plot_events(plot_id)
        return [EventResponse.model_validate(event, from_attributes=True) for event in events]
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/campaign/{campaign_id}", response_model=list[EventResponse])
async def get_campaign_events(
    campaign_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[EventResponse]:
    """
    Get all events for a specific campaign.
    - FARMER can only view events for campaigns they participate in
    - ADVISOR can view events for campaigns they advise
    - ADMIN can view events for any campaign
    """
    service = EventService(db)
    campaign_service = CampaignService(db)
    try:
        # Verify campaign exists
        campaign = await campaign_service.get(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign {campaign_id} not found",
            )

        # TODO: Implement proper campaign access control
        events = await service.get_campaign_events(campaign_id)
        return [EventResponse.model_validate(event, from_attributes=True) for event in events]
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/upcoming/{days}", response_model=list[EventResponse])
async def get_upcoming_events(
    days: int = 7,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[EventResponse]:
    """
    Get upcoming events within the next X days.
    - Users will only see events they have access to
    - Default period is 7 days
    """
    service = EventService(db)
    try:
        events = await service.get_upcoming_events(days)

        # Filter events based on user role and access
        if current_user.role != UserRole.ADMIN:
            events = [e for e in events if e.created_by_id == current_user.id]

        return [EventResponse.model_validate(event, from_attributes=True) for event in events]
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/date-range", response_model=list[EventResponse])
async def get_events_by_date_range(
    date_range: EventDateRange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[EventResponse]:
    """
    Get all events within a date range.
    - Users will only see events they have access to
    """
    service = EventService(db)
    try:
        events = await service.get_events_by_date_range(date_range.start_date, date_range.end_date)

        # Filter events based on user role and access
        if current_user.role != UserRole.ADMIN:
            events = [e for e in events if e.created_by_id == current_user.id]

        return [EventResponse.model_validate(event, from_attributes=True) for event in events]
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
