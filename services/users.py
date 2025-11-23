from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.models import User
from config.my_logger import get_logger

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_logger(__name__, self.__class__.__name__)

    async def get_user_by_email(self, email: str) -> User | None:
        try:
            result = await self.session.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error fetching user by email: {e}")
            return None
        
    async def get_user_by_id(self, user_id: int) -> User | None:
        try:
            result = await self.session.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error fetching user by id: {e}")
            return None

    async def create_user(self, user: User) -> User | None:
        self.session.add(user)
        try:
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error creating user: {e}")
            return None

    async def update_user(self, user: User) -> User | None:
        try:
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error updating user: {e}")
            return None