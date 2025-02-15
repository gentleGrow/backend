from sqlalchemy.ext.asyncio import AsyncSession

from app.module.event.repository import EventRepository


class EventService:
    async def get_agreed_user_id_nickname(
        self, session: AsyncSession, event_id: int, limit: int
    ) -> list[tuple[int, str | None]]:
        return await EventRepository.get_agreed_user_id_nickname(session, event_id, limit)
