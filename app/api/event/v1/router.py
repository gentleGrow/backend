from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth.security import verify_jwt_token
from app.common.schema.common_schema import PutResponse
from app.module.auth.repository import UserRepository
from app.module.auth.schema import AccessToken
from app.module.event.enum import EventTypeID
from app.module.event.repository import EventRepository
from app.module.event.schema import UserPorfolioShareConsentRequst
from database.dependency import get_mysql_session_router

event_router = APIRouter(prefix="/v1")


@event_router.put("/portfolio", summary="포트폴리오 공유 여부를 수정합니다.", response_model=PutResponse)
async def update_share_portfolio(
    request_data: UserPorfolioShareConsentRequst,
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
):
    user = await UserRepository.get(session, token.get("user"))
    if user is None:
        return PutResponse(status_code=status.HTTP_404_NOT_FOUND, detail="유저 정보가 없습니다.")

    await EventRepository.update_event(session, user.id, EventTypeID.PORTFOLIO_SHARE.value, request_data.sharing)
    return PutResponse(status_code=status.HTTP_200_OK, detail="성공적으로 수정하였습니다.")
