import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.security import get_password_hash
from app.domain.models.user import User
from app.domain.models.device import Device
from app.core.config import get_settings

async def seed():
    settings = get_settings()
    engine = create_async_engine(settings.database.async_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if user exists
        user = User(
            email="admin@ampaware.com",
            full_name="Admin User",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        device = Device(
            serial_number="AA:BB:CC:DD:EE:FF",
            connection_type="SINGLE_PHASE",
            owner_id=user.id,
            name="Main Feeder",
            status="ACTIVE",
            is_online=True
        )
        session.add(device)
        await session.commit()
        
        print(f"Seeded user: {user.email} / password123")
        
if __name__ == "__main__":
    asyncio.run(seed())
