from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.module.auth.enum import ProviderEnum
from app.module.auth.model import User


class UserRepository:
    @staticmethod
    async def delete(session: AsyncSession, user_id: int) -> None:
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()

    @staticmethod
    async def get_by_social_id(session: AsyncSession, social_id: str, provider: ProviderEnum) -> User | None:
        select_instance = select(User).where(User.social_id == social_id, User.provider == provider.value)

        result = await session.execute(select_instance)
        return result.scalars().first()

    @staticmethod
    async def get(session: AsyncSession, user_id: int) -> User | None:
        select_instance = select(User).where(User.id == user_id)
        result = await session.execute(select_instance)
        return result.scalars().first()

    @staticmethod
    async def create(session: AsyncSession, new_user: User) -> User:
        session.add(new_user)
        await session.commit()
        return new_user

    @staticmethod
    async def get_by_name(session: AsyncSession, user_name: str) -> User | None:
        select_instance = select(User).where(User.nickname == user_name)
        result = await session.execute(select_instance)
        return result.scalars().first()

    @staticmethod
    async def get_by_names(session: AsyncSession, user_names: list[str]) -> list[User]:
        select_instance = select(User).where(User.nickname.in_(user_names))
        result = await session.execute(select_instance)
        return result.scalars().all()

    @staticmethod
    async def update_nickname(session: AsyncSession, user_id: int, nickname: str):
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(nickname=nickname)
            .execution_options(synchronize_session="fetch")
        )

        await session.execute(stmt)
        await session.commit()
