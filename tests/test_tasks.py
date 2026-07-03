import pytest
from sqlalchemy import select

from src.models.campaign_model import Campaign
from src.models.notification_model import Notification
from src.models.plot_model import Plot
from src.models.user_model import User, UserRole
from src.tasks.calendar_tasks import sync_event_task
from src.tasks.weather_tasks import fetch_weather_alerts_task


@pytest.mark.anyio
async def test_sync_event_task(mock_calendar):
    """Verify that sync_event_task successfully calls the calendar client mock."""
    res = sync_event_task(123, "Test Event", "2026-07-01T08:00:00")
    assert res is True
    from datetime import datetime

    mock_calendar.sync_event.assert_called_once_with(
        event_id=123,
        title="Test Event",
        start_time=datetime.fromisoformat("2026-07-01T08:00:00"),
    )


@pytest.mark.anyio
async def test_fetch_weather_alerts_task(db_session, mock_weather):
    """Verify that fetch_weather_alerts_task correctly processes weather data and creates notifications for severe conditions."""
    # 1. Create an Admin user to act as sender
    admin = User(
        auth0_id="auth0|admin-task-test",
        email="admin-task@example.com",
        email_verified=True,
        full_name="Admin Test",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)

    # 2. Create Farmer user to receive alert
    farmer = User(
        auth0_id="auth0|farmer-task-test",
        email="farmer-task@example.com",
        email_verified=True,
        full_name="Farmer Test",
        role=UserRole.FARMER,
        is_active=True,
    )
    db_session.add(farmer)
    await db_session.commit()
    await db_session.refresh(admin)
    await db_session.refresh(farmer)

    # 3. Create Campaign and Plot with location
    from datetime import datetime, timedelta

    campaign = Campaign(
        name="Test Campaign Tasks",
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),
        user_id=farmer.id,
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)

    plot = Plot(
        name="Valley Plot Task",
        area=10.0,
        location="Coords: 12.34, 56.78",
        campaign_id=campaign.id,
        user_id=farmer.id,
    )
    db_session.add(plot)
    await db_session.commit()
    await db_session.refresh(plot)

    # 4. Trigger fetch_weather_alerts_task
    # mock_weather returns: {"temperature": 22.5, "precipitation": 5.0, "conditions": "rainy"}
    # This matches precipitation > 4.0 or rainy conditions, triggering the alert.
    alerts_sent = fetch_weather_alerts_task()
    assert alerts_sent == 1

    # 5. Check if notification was successfully created in the database
    stmt = select(Notification).where(Notification.user_id == farmer.id)
    res = await db_session.execute(stmt)
    notifications = res.scalars().all()
    assert len(notifications) == 1
    assert notifications[0].sender_id == admin.id
    assert "Valley Plot Task" in notifications[0].title
    assert "rainy" in notifications[0].content
