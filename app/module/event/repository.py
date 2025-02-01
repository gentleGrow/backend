from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.module.auth.model import UserEventConsent

class EventRepository:
    @classmethod
    async def update_event(cls, session: AsyncSession, user_id: int, event_type_id: int, consent: bool):
        stmt = (
            update(UserEventConsent)
            .where(UserEventConsent.user_id == user_id, UserEventConsent.event_id == event_type_id)
            .values(consent=consent)
            .execution_options(synchronize_session="fetch")
        )

        result = await session.execute(stmt)

        if result.rowcount == 0:
            new_record = UserEventConsent(user_id=user_id, event_id=event_type_id, consent=consent)
            session.add(new_record)

        await session.commit()




