from app.module.auth.services.user_service import UserService


def get_user_service() -> UserService:
    return UserService()