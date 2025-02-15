from httpx import AsyncClient

from app.module.asset.constant import ASSET_FIELD, REQUIRED_ASSET_FIELD
from app.module.asset.enum import AccountType, InvestmentBankType
from app.module.asset.schema import UpdateAssetFieldRequest


class TestAssetStock:
    """
    api: /api/asset/v1/assetstock
    method: GET, POST, PUT, DELETE
    """

    async def test_get_asset_stock_success(self, client: AsyncClient, setup_all):
        # given
        response = await client.get("/api/asset/v1/assetstock")

        # when
        stock_data = response.json()

        # then
        assert stock_data["asset_fields"] == REQUIRED_ASSET_FIELD
        assert stock_data["stock_assets"]
        assert stock_data["won_exchange"] == 1300.0

    async def test_post_asset_stock_success(self, client: AsyncClient, setup_all):
        # given
        request_data = {
            "trade_date": "2024-08-13",
            "purchase_currency_type": "USD",
            "quantity": 11,
            "stock_code": "AAPL",
            "trade": "매수",
        }
        response = await client.post("/api/asset/v1/assetstock", json=request_data)

        # when
        stock_data = response.json()

        # then
        assert stock_data["status_code"] == 201
        assert stock_data["detail"] == "주식 자산 성공적으로 등록 했습니다."

    async def test_post_asset_stock_fail_no_exist(self, client: AsyncClient, setup_all):
        # given
        request_data = {
            "trade_date": "1999-01-13",
            "purchase_currency_type": "USD",
            "quantity": 11,
            "stock_code": "AAPL",
            "trade": "매수",
        }
        response = await client.post("/api/asset/v1/assetstock", json=request_data)

        # when
        stock_data = response.json()

        # then
        assert stock_data["status_code"] == 404
        assert stock_data["detail"] == "AAPL 코드의 1999-01-13 날짜 데이터가 존재하지 않습니다."
        assert stock_data["field"] == "매매일자"

    async def test_put_asset_stock_success(self, client: AsyncClient, setup_all):
        # given
        request_data = {
            "id": 1,
            "trade_date": "2024-08-13",
            "purchase_currency_type": "USD",
            "quantity": 1,
            "stock_code": "AAPL",
            "trade": "매수",
        }
        response = await client.put("/api/asset/v1/assetstock", json=request_data)

        # when
        stock_data = response.json()

        # then
        assert stock_data["status_code"] == 200
        assert stock_data["detail"] == "주식 자산을 성공적으로 수정 하였습니다."

    async def test_put_asset_stock_fail_wrong_id(self, client: AsyncClient, setup_all):
        # given
        request_data = {
            "id": 999,
            "trade_date": "2024-08-13",
            "purchase_currency_type": "USD",
            "quantity": 1,
            "stock_code": "AAPL",
            "trade": "매수",
        }
        response = await client.put("/api/asset/v1/assetstock", json=request_data)

        # when
        stock_data = response.json()

        # then
        assert stock_data["status_code"] == 400
        assert stock_data["detail"] == "해당하는 asset을 찾지 못 했습니다."

    async def test_delete_asset_stock_by_asset_id_success(self, client: AsyncClient, setup_all):
        # given
        response = await client.delete("/api/asset/v1/assetstock/2")

        # when
        stock_data = response.json()

        # then
        assert stock_data["status_code"] == 200
        assert stock_data["detail"] == "주식 자산이 성공적으로 삭제 되었습니다."

    async def test_delete_asset_stock_fail_wrong_id(self, client: AsyncClient, setup_all):
        # given
        response = await client.delete("/api/asset/v1/assetstock/999")

        # when
        stock_data = response.json()

        # then
        assert stock_data["status_code"] == 404
        assert stock_data["detail"] == "해당하는 asset id가 유저에게 존재하지 않습니다."

    async def test_delete_asset_stock_by_stock_code_success(self, client: AsyncClient, setup_all):
        # given
        response = await client.delete("/api/asset/v1/assetstock/stock/AAPL")

        # when
        stock_data = response.json()

        # then
        assert stock_data["status_code"] == 200
        assert stock_data["detail"] == "부모행을 성공적으로 삭제 하였습니다."


class TestAssetField:
    """
    api: /api/asset/v1/asset-field
    method: GET, PUT
    """

    async def test_get_asset_field_success(self, client: AsyncClient, setup_all):
        # given
        response = await client.get("/api/asset/v1/asset-field")

        # when
        user_asset_field = response.json()

        # then
        assert response.status_code == 200
        assert user_asset_field == REQUIRED_ASSET_FIELD

    async def test_update_asset_field_success(self, client: AsyncClient, setup_all, user_instance):
        # given
        request_data = UpdateAssetFieldRequest(root=ASSET_FIELD)
        response = await client.put("/api/asset/v1/asset-field", json=request_data.model_dump())

        # when
        response_data = response.json()

        # then
        assert response_data["status_code"] == 200
        assert response_data["detail"] == "자산관리 필드를 성공적으로 수정 하였습니다."


class TestStocks:
    """
    api: /api/asset/v1/stocks
    method: GET
    """

    async def test_get_stocks_success(self, client: AsyncClient, setup_all):
        # given
        response = await client.get("/api/asset/v1/stocks")

        # when
        response_data = response.json()

        # then
        assert response_data


class TestBankAccounts:
    """
    api: /api/asset/v1/bank-accounts
    method: GET
    """

    async def test_get_bank_accounts_success(self, client: AsyncClient):
        # given
        response = await client.get("/api/asset/v1/bank-accounts")

        # when
        response_data = response.json()
        expected_investment_banks = [bank.value for bank in InvestmentBankType]
        expected_account_types = [account.value for account in AccountType]

        # then
        assert response_data["investment_bank_list"] == expected_investment_banks
        assert response_data["account_list"] == expected_account_types
