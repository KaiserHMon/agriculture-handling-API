# ruff: noqa: E402
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from sqlalchemy import select

from src.db.database import get_db_context
from src.models.campaign_model import Campaign
from src.models.event_model import Event
from src.models.plot_model import Plot
from src.models.recommendation_model import Recommendation
from src.models.user_model import User, UserRole


async def seed_data():
    print("Starting database seeding...")
    async with get_db_context() as session:
        # 1. Create Users
        # Admin
        stmt = select(User).where(User.email == "admin@agriculture-handling.com")
        res = await session.execute(stmt)
        admin = res.scalar_one_or_none()
        if not admin:
            admin = User(
                auth0_id="auth0|admin_seed_id",
                email="admin@agriculture-handling.com",
                email_verified=True,
                full_name="System Administrator",
                role=UserRole.ADMIN,
                is_active=True,
                last_login=datetime.utcnow(),
            )
            session.add(admin)
            print("Created Admin user.")
        else:
            print("Admin user already exists.")

        # Advisor
        stmt = select(User).where(User.email == "advisor@agriculture-handling.com")
        res = await session.execute(stmt)
        advisor = res.scalar_one_or_none()
        if not advisor:
            advisor = User(
                auth0_id="auth0|advisor_seed_id",
                email="advisor@agriculture-handling.com",
                email_verified=True,
                full_name="Dr. Julia Green (Advisor)",
                role=UserRole.ADVISOR,
                is_active=True,
                last_login=datetime.utcnow(),
            )
            session.add(advisor)
            print("Created Advisor user.")
        else:
            print("Advisor user already exists.")

        # Farmer
        stmt = select(User).where(User.email == "farmer@agriculture-handling.com")
        res = await session.execute(stmt)
        farmer = res.scalar_one_or_none()
        if not farmer:
            farmer = User(
                auth0_id="auth0|farmer_seed_id",
                email="farmer@agriculture-handling.com",
                email_verified=True,
                full_name="John Doe (Farmer)",
                role=UserRole.FARMER,
                is_active=True,
                last_login=datetime.utcnow(),
            )
            session.add(farmer)
            print("Created Farmer user.")
        else:
            print("Farmer user already exists.")

        # Commit users to generate IDs
        await session.commit()
        await session.refresh(admin)
        await session.refresh(advisor)
        await session.refresh(farmer)

        # 2. Create Campaign for the farmer
        stmt = select(Campaign).where(Campaign.user_id == farmer.id)
        res = await session.execute(stmt)
        campaign = res.scalar_one_or_none()
        if not campaign:
            campaign = Campaign(
                name="Maize Campaign 2026",
                description="Annual maize planting and harvesting season.",
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=180),
                user_id=farmer.id,
            )
            session.add(campaign)
            print("Created Campaign.")
        else:
            print("Campaign already exists.")

        await session.commit()
        await session.refresh(campaign)

        # 3. Create Plot for the Campaign & Farmer
        stmt = select(Plot).where(Plot.campaign_id == campaign.id)
        res = await session.execute(stmt)
        plot = res.scalar_one_or_none()
        if not plot:
            plot = Plot(
                name="North Valley Plot",
                area=45.2,
                location="Coords: -34.6037, -58.3816",
                soil_type="Clay-Loam",
                campaign_id=campaign.id,
                user_id=farmer.id,
            )
            session.add(plot)
            print("Created Plot.")
        else:
            print("Plot already exists.")

        await session.commit()
        await session.refresh(plot)

        # 4. Create Event for that Plot/Campaign (Created by Farmer)
        stmt = select(Event).where(Event.plot_id == plot.id)
        res = await session.execute(stmt)
        event = res.scalar_one_or_none()
        if not event:
            event = Event(
                title="Sowing Maize",
                description="Planting pioneer hybrid maize seed.",
                event_date=datetime.utcnow() + timedelta(days=2),
                created_by_id=farmer.id,
                plot_id=plot.id,
                campaign_id=campaign.id,
            )
            session.add(event)
            print("Created Event.")
        else:
            print("Event already exists.")

        # 5. Create Recommendation for that Plot (Created by Advisor)
        stmt = select(Recommendation).where(Recommendation.plot_id == plot.id)
        res = await session.execute(stmt)
        rec = res.scalar_one_or_none()
        if not rec:
            rec = Recommendation(
                content="Ensure nitrogen fertilization is performed at V4 stage. Recommended dose is 150 kg/ha of Urea.",
                plot_id=plot.id,
                advisor_id=advisor.id,
            )
            session.add(rec)
            print("Created Recommendation.")
        else:
            print("Recommendation already exists.")

        await session.commit()
        print("Database seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed_data())
