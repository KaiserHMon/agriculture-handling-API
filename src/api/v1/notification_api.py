from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.auth import get_current_active_user
from ...db.database import get_db
from ...exceptions.api_exceptions import DatabaseError, NotFoundError
from ...models.user_model import User, UserRole
from ...schema.notification_schema import (
    NotificationCount,
    NotificationCreate,
    NotificationInDB,
    NotificationResponse,
)
from ...services.notification_service import NotificationService
from ...services.user_service import UserService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    payload: NotificationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationResponse:
    """
    Create a new notification (message).
    - FARMER can send messages to ADVISOR
    - ADVISOR can send messages to FARMER
    - ADMIN can send messages to anyone
    """
    service = NotificationService(db)
    user_service = UserService(db)

    try:
        # Verify recipient exists and check permissions
        recipient = await user_service.get(payload.user_id)
        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipient user {payload.user_id} not found",
            )

        # Check permissions based on roles
        if current_user.role == UserRole.FARMER:
            if recipient.role != UserRole.ADVISOR:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Farmers can only send messages to advisors",
                )
        elif current_user.role == UserRole.ADVISOR:
            if recipient.role != UserRole.FARMER:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Advisors can only send messages to farmers",
                )

        # Convert to InDB model first
        notification_data = NotificationInDB.model_validate(
            {
                **payload.model_dump(),
                "is_read": False,
            }
        )

        # Create notification
        notification = await service.create(notification_data.model_dump())
        return NotificationResponse.model_validate(notification, from_attributes=True)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/", response_model=list[NotificationResponse])
async def list_notifications(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationResponse]:
    """Get all notifications for the current user."""
    service = NotificationService(db)
    try:
        notifications = await service.get_user_notifications(current_user.id)
        return [NotificationResponse.model_validate(n, from_attributes=True) for n in notifications]
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/unread", response_model=list[NotificationResponse])
async def list_unread_notifications(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationResponse]:
    """Get all unread notifications for the current user."""
    service = NotificationService(db)
    try:
        notifications = await service.get_unread_notifications(current_user.id)
        return [NotificationResponse.model_validate(n, from_attributes=True) for n in notifications]
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationResponse:
    """Mark a notification as read. Users can only mark their own notifications."""
    service = NotificationService(db)
    try:
        # Verify ownership
        notification = await service.get(notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification {notification_id} not found",
            )

        if notification.user_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Users can only mark their own notifications as read",
            )

        marked_notification = await service.mark_as_read(notification_id)
        return NotificationResponse.model_validate(marked_notification, from_attributes=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.patch("/mark-all-read", response_model=int)
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> int:
    """Mark all notifications as read for the current user."""
    service = NotificationService(db)
    try:
        count = await service.mark_all_as_read(current_user.id)
        return count
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/read", response_model=int)
async def delete_read_notifications(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> int:
    """Delete all read notifications for the current user."""
    service = NotificationService(db)
    try:
        count = await service.delete_read_notifications(current_user.id)
        return count
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/count", response_model=NotificationCount)
async def get_notification_count(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationCount:
    """Get total and unread notification counts for the current user."""
    service = NotificationService(db)
    try:
        total = len(await service.get_user_notifications(current_user.id))
        unread = len(await service.get_unread_notifications(current_user.id))
        return NotificationCount(total=total, unread=unread)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/conversation/{other_user_id}", response_model=list[NotificationResponse])
async def get_conversation(
    other_user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationResponse]:
    """
    Get all notifications between current user and another user, ordered by date.
    This represents a chat conversation between two users.
    """
    service = NotificationService(db)
    user_service = UserService(db)

    try:
        # Verify other user exists
        other_user = await user_service.get(other_user_id)
        if not other_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {other_user_id} not found",
            )

        # Check permission to chat
        if current_user.role == UserRole.FARMER and other_user.role != UserRole.ADVISOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Farmers can only chat with advisors",
            )
        elif current_user.role == UserRole.ADVISOR and other_user.role != UserRole.FARMER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Advisors can only chat with farmers",
            )

        # Get messages in both directions
        received = await service.get_user_notifications(current_user.id)
        sent = await service.get_user_notifications(other_user_id)

        # Filter and sort messages
        conversation = [
            n
            for n in received + sent
            if (n.user_id == current_user.id and n.sender_id == other_user_id)
            or (n.user_id == other_user_id and n.sender_id == current_user.id)
        ]
        conversation.sort(key=lambda x: x.created_at)

        return [NotificationResponse.model_validate(n, from_attributes=True) for n in conversation]
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
