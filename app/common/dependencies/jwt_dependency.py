from app.common.services.jwt_service import JWTService


def get_jwt_service() -> JWTService:
    return JWTService()
