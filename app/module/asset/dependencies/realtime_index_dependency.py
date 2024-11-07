from app.module.asset.services.realtime_index_service import RealtimeIndexService

def get_realtime_index_service() -> RealtimeIndexService:
    return RealtimeIndexService()