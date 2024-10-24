from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth.security import verify_jwt_token
from app.common.schema.common_schema import PostResponse
from app.module.auth.constant import REDIS_JWT_REFRESH_EXPIRE_TIME_SECOND, SESSION_SPECIAL_KEY
from app.module.auth.enum import ProviderEnum
from app.module.auth.jwt import JWTBuilder
from app.module.auth.model import User
from app.module.auth.redis_repository import RedisSessionRepository
from app.module.auth.repository import UserRepository
from app.module.auth.schema import (
    AccessToken,
    AccessTokenResponse,
    NaverTokenRequest,
    NicknameRequest,
    NicknameResponse,
    TokenRefreshRequest,
    TokenRequest,
    TokenResponse,
    UserInfoResponse,
)
from app.module.auth.service import Google, Kakao, Naver
from database.dependency import get_mysql_session_router, get_redis_pool

auth_router = APIRouter(prefix="/v1")


@auth_router.get("/user", summary="유저 정보를 확인합니다.", response_model=UserInfoResponse)
async def get_user_info(
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
) -> UserInfoResponse:
    user = await UserRepository.get(session, token.get("user"))
    if user is None:
        return UserInfoResponse(nickname="", email="", isJoined=False)
    else:
        nickname = user.nickname if user.nickname is not None else ""
        email = user.email if user.email is not None else ""
        isJoined = True if user.nickname else False

        return UserInfoResponse(nickname=nickname, email=email, isJoined=isJoined)


@auth_router.get("/nickname", summary="해당 닉네임 존재 여부를 확인합니다.", response_model=NicknameResponse)
async def check_nickname(nickname: str, session: AsyncSession = Depends(get_mysql_session_router)) -> NicknameResponse:
    user_nickname = await UserRepository.get_by_name(session, nickname)

    return NicknameResponse(isUsed=False) if user_nickname is None else NicknameResponse(isUsed=True)


@auth_router.put("/nickname", summary="유저 닉네임을 수정합니다.", response_model=PostResponse)
async def update_nickname(
    request: NicknameRequest,
    token: AccessToken = Depends(verify_jwt_token),
    session: AsyncSession = Depends(get_mysql_session_router),
) -> PostResponse:
    user_nickname = await UserRepository.get_by_name(session, request.nickname)
    try:
        request.nickname = NicknameRequest.validate_nickname(request.nickname)
    except HTTPException as e:
        return PostResponse(status_code=e.status_code, content=e.detail)

    if user_nickname is not None:
        return PostResponse(status_code=status.HTTP_400_BAD_REQUEST, content="이미 존재하는 닉네임입니다.")

    await UserRepository.update_nickname(session, token.get("user"), request.nickname)
    return PostResponse(status_code=status.HTTP_200_OK, content="성공적으로 닉네임을 저장하였습니다.")


@auth_router.post(
    "/naver",
    summary="client naver access token을 확인후 jwt 토큰을 반환합니다.",
    description="client naver 토큰이 넘어오는 지 확인후, 해당 토큰으로 유저확인을 합니다. 신규 유저인 경우 DB에 저장한후, jwt를 반환합니다.",
    response_model=TokenResponse,
)
async def naver_login(
    request: NaverTokenRequest,
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
) -> TokenResponse:
    access_token = request.access_token
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="naver access token이 넘어오지 않았습니다.",
        )

    try:
        user_info = await Naver.verify_token(access_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    social_id = user_info["response"].get("id")
    if social_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="access token에 유저 정보가 없습니다.")

    user = await UserRepository.get_by_social_id(session, social_id, ProviderEnum.NAVER)

    if user is None:
        user = User(
            social_id=social_id,
            email=user_info["response"].get("email"),
            provider=ProviderEnum.NAVER.value,
        )
        user = await UserRepository.create(session, user)

    access_token = JWTBuilder.generate_access_token(user.id, social_id)
    refresh_token = JWTBuilder.generate_refresh_token(user.id, social_id)

    await RedisSessionRepository.save(
        redis_client, f"{social_id}_{SESSION_SPECIAL_KEY}", refresh_token, REDIS_JWT_REFRESH_EXPIRE_TIME_SECOND
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@auth_router.post(
    "/kakao",
    summary="client 카카오 id token을 확인후 jwt 토큰을 반환합니다.",
    description="client 카카오 토큰이 넘어오는 지 확인후, 해당 토큰으로 유저확인을 합니다. 신규 유저인 경우 DB에 저장한후, jwt를 반환합니다.",
    response_model=TokenResponse,
)
async def kakao_login(
    request: TokenRequest,
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
) -> TokenResponse:
    id_token = request.id_token
    if not id_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="카카오 id token이 넘어오지 않았습니다.",
        )

    try:
        id_info = await Kakao.verify_token(id_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    social_id = id_info.get("sub")
    if social_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="id token에 유저 정보가 없습니다.")

    user = await UserRepository.get_by_social_id(session, social_id, ProviderEnum.KAKAO)

    if user is None:
        user = User(
            social_id=social_id,
            email=id_info.get("email", None),
            provider=ProviderEnum.KAKAO.value,
        )
        user = await UserRepository.create(session, user)

    access_token = JWTBuilder.generate_access_token(user.id, social_id)
    refresh_token = JWTBuilder.generate_refresh_token(user.id, social_id)

    await RedisSessionRepository.save(
        redis_client, f"{social_id}_{SESSION_SPECIAL_KEY}", refresh_token, REDIS_JWT_REFRESH_EXPIRE_TIME_SECOND
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@auth_router.post(
    "/google",
    summary="client 구글 id token을 확인후 jwt 토큰을 반환합니다.",
    description="client 구글 토큰이 넘어오는 지 확인후, 해당 토큰으로 유저확인을 합니다. 신규 유저인 경우 DB에 저장한후, jwt를 반환합니다.",
    response_model=TokenResponse,
)
async def google_login(
    request: TokenRequest,
    session: AsyncSession = Depends(get_mysql_session_router),
    redis_client: Redis = Depends(get_redis_pool),
) -> TokenResponse:
    id_token = request.id_token

    try:
        id_info = await Google.verify_token(id_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    social_id = id_info.get("sub")

    if social_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="id token에 유저 정보가 없습니다.")

    user = await UserRepository.get_by_social_id(session, social_id, ProviderEnum.GOOGLE)

    if user is None:
        user = User(social_id=social_id, provider=ProviderEnum.GOOGLE.value, email=id_info.get("email", None))
        user = await UserRepository.create(session, user)

    access_token = JWTBuilder.generate_access_token(user.id, social_id)
    refresh_token = JWTBuilder.generate_refresh_token(user.id, social_id)

    await RedisSessionRepository.save(
        redis_client, f"{social_id}_{SESSION_SPECIAL_KEY}", refresh_token, REDIS_JWT_REFRESH_EXPIRE_TIME_SECOND
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@auth_router.post(
    "/refresh",
    summary="새로운 JWT 액세스 토큰을 발급합니다.",
    description="클라이언트로부터 유저 ID를 받아, Redis에서 해당 유저의 리프레시 토큰을 검색 후, 새로운 액세스 토큰을 발급하여 반환합니다.",
    response_model=AccessTokenResponse,
)
async def refresh_access_token(
    request: TokenRefreshRequest, redis_client: Redis = Depends(get_redis_pool)
) -> AccessTokenResponse:
    refresh_token = request.refresh_token
    decoded = JWTBuilder.decode_token(refresh_token)

    social_id = decoded.get("sub")
    user_id = decoded.get("user")

    if social_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token안에 유저 정보가 들어있지 않습니다.")

    stored_refresh_token = await RedisSessionRepository.get(redis_client, f"{social_id}_{SESSION_SPECIAL_KEY}")

    if stored_refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="서버에 저장된 refresh token이 없습니다.",
        )

    if stored_refresh_token != refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="서버에 저장된 refresh token과 다른 refresh token을 반환하였습니다.",
        )

    access_token = JWTBuilder.generate_access_token(user_id, social_id)

    return AccessTokenResponse(access_token=access_token)
