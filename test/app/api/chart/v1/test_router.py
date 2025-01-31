from httpx import AsyncClient



class TestAssetSaveTrend:
    """
    api: /api/chart/v1/asset-save-trend
    method: GET
    """    

    async def test_get_asset_save_trend_success(self, client: AsyncClient, setup_all):
        # given
        response = await client.get("/api/chart/v1/asset-save-trend")

        # when
        asset_save_trend = response.json()

        # then
        assert asset_save_trend
        assert asset_save_trend["values1"] 



class TestEstimateDividend:
    """
    api: /api/chart/v1/estimate-dividend?category=every
    params: category, type
    method: GET
    """    

    async def test_get_estimate_dividend_every_success(self, client: AsyncClient, setup_all):
        # given
        response = await client.get("/api/chart/v1/estimate-dividend?category=every")

        # when
        estimate_dividend = response.json()

        # then
        assert estimate_dividend

    async def test_get_estimate_dividend_type_success(self, client: AsyncClient, setup_all):
        # given
        response = await client.get("/api/chart/v1/estimate-dividend?category=type")

        # when
        estimate_dividend = response.json()

        # then
        assert estimate_dividend


class TestComposition:
    """
    api: /api/chart/v1/composition
    params: composition, account
    method: GET
    """    

    async def test_get_composition_success(self, client: AsyncClient, setup_all):
        # given
        response = await client.get("/api/chart/v1/composition?type=composition")

        # when
        composition = response.json()

        # then
        assert composition
 
    async def test_get_composition_account_success(self, client: AsyncClient, setup_all):
        # given
        response = await client.get("/api/chart/v1/composition?type=account")

        # when
        composition = response.json()

        # then
        assert composition



class TestPerformanceAnalysis:
    """
    api: /api/chart/v1/performance-analysis
    params: 1month, 3month, 6month, 1year
    method: GET
    """    

    async def test_get_performance_analysis_1month_success(self, client: AsyncClient, setup_all):
        # given
        response = await client.get("/api/chart/v1/performance-analysis?interval=1month")

        # when
        performance_analysis = response.json()

        # then
        assert performance_analysis

    async def test_get_performance_analysis_1year_success(self, client: AsyncClient, setup_all):
        # given
        response = await client.get("/api/chart/v1/performance-analysis?interval=1year")

        # when
        performance_analysis = response.json()

        # then
        assert performance_analysis


class TestMyStock:
    """
    api: /api/chart/v1/my-stock
    method: GET
    """    

    async def test_get_my_stock_success(self, client: AsyncClient, setup_all):
        # given
        response = await client.get("/api/chart/v1/my-stock")

        # when
        my_stock = response.json()

        # then
        assert my_stock



class TestSummary:
    """
    api: /api/chart/v1/summary
    method: GET
    """    

    async def test_get_summary_success(self, client: AsyncClient, setup_all):
        # given
        response = await client.get("/api/chart/v1/summary")

        # when
        summary = response.json()

        # then
        assert summary["increase_asset_amount"]
        assert summary["total_asset_amount"]



