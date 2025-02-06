from app.module.event.service import EventService


def get_event_service() -> EventService:
    return EventService()
