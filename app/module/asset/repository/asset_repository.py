from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.orm.exc import NoResultFound

from app.common.util.time import get_now_datetime
from app.module.asset.enum import AssetType
from app.module.asset.model import Asset, AssetStock


class AssetRepository:
    @staticmethod
    async def get_eager(session: AsyncSession, user_id: int, asset_type: AssetType) -> list[Asset]:
        result = await session.execute(
            select(Asset)
            .filter(and_(Asset.user_id == user_id, Asset.asset_type == asset_type, Asset.deleted_at.is_(None)))
            .options(joinedload(Asset.asset_stock).joinedload(AssetStock.stock))
        )
        return result.unique().scalars().all()

    @staticmethod
    async def save(session: AsyncSession, asset: Asset) -> None:
        session.add(asset)
        await session.commit()

    @staticmethod
    async def delete_assets(session: AsyncSession, asset_ids: list[int]) -> None:
        try:
            assets = await session.execute(
                select(Asset).filter(Asset.id.in_(asset_ids)).options(joinedload(Asset.asset_stock))
            )
            assets = assets.scalars().all()

            if not assets:
                raise ValueError(f"주어진 Asset IDs {asset_ids}에 해당하는 자산이 없습니다.")

            for asset in assets:
                if asset.asset_stock:
                    asset.asset_stock.deleted_at = get_now_datetime()

                asset.deleted_at = get_now_datetime()

            await session.commit()

        except NoResultFound:
            raise ValueError(f"Asset IDs {asset_ids} 중 하나도 찾을 수 없습니다.")
        except Exception as e:
            await session.rollback()
            raise ValueError(f"자산 삭제 중 오류 발생: {e}")

    @staticmethod
    async def delete_asset(session: AsyncSession, asset_id: int) -> None:
        try:
            asset = await session.execute(
                select(Asset).filter(Asset.id == asset_id).options(joinedload(Asset.asset_stock))
            )
            asset = asset.scalars().one()
        except NoResultFound:
            raise ValueError(f"Asset ID {asset_id}를 찾을 수 없습니다.")

        if asset.asset_stock:
            asset.asset_stock.deleted_at = get_now_datetime()

        asset.deleted_at = get_now_datetime()
        await session.commit()

    @staticmethod
    async def get_assets(session: AsyncSession, user_id: str) -> list[Asset]:
        result = await session.execute(
            select(Asset)
            .filter(and_(Asset.user_id == user_id, Asset.deleted_at.is_(None)))
            .options(joinedload(Asset.asset_stock).joinedload(AssetStock.stock))
        )
        return result.scalars().all()

    @staticmethod
    async def save_assets(session: AsyncSession, assets: list[Asset]) -> None:
        session.add_all(assets)
        await session.commit()

    @staticmethod
    async def get_eager_by_range(
        session: AsyncSession, user_id: int, asset_type: AssetType, date_range: tuple
    ) -> list[Asset]:
        start_date, end_date = date_range

        result = await session.execute(
            select(Asset)
            .filter(
                and_(
                    Asset.user_id == user_id,
                    Asset.asset_type == asset_type,
                    Asset.deleted_at.is_(None),
                    Asset.asset_stock.has(AssetStock.trade_date.between(start_date, end_date)),
                )
            )
            .options(selectinload(Asset.asset_stock).selectinload(AssetStock.stock))
        )

        return result.scalars().all()

    @staticmethod
    async def get_assets_by_ids(session: AsyncSession, asset_ids: list[int]) -> list[Asset]:
        result = await session.execute(
            select(Asset)
            .filter(and_(Asset.id.in_(asset_ids), Asset.deleted_at.is_(None)))
            .options(joinedload(Asset.asset_stock).joinedload(AssetStock.stock))
        )
        return result.scalars().all()

    @staticmethod
    async def get_asset_by_id(session: AsyncSession, asset_id: int) -> Asset | None:
        result = await session.execute(
            select(Asset)
            .options(joinedload(Asset.asset_stock).joinedload(AssetStock.stock))
            .where(Asset.id == asset_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_assets_by_user_ids(session: AsyncSession, user_ids: list[int]) -> list[Asset]:
        result = await session.execute(
            select(Asset)
            .filter(and_(Asset.user_id.in_(user_ids), Asset.deleted_at.is_(None)))
            .options(joinedload(Asset.asset_stock).joinedload(AssetStock.stock))
        )
        return result.scalars().all()
