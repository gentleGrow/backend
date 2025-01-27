from app.module.asset.enum import AccountType, InvestmentBankType


class TestGetBankAccounts:
    """
    api: /api/asset/v1/bank-accounts
    method: GET
    """

    async def test_get_bank_accounts(self, client):
        # given
        response = client.get("/api/asset/v1/bank-accounts")

        # when
        response_data = response.json()
        expected_investment_banks = [bank.value for bank in InvestmentBankType]
        expected_account_types = [account.value for account in AccountType]

        # then
        assert response_data["investment_bank_list"] == expected_investment_banks
        assert response_data["account_list"] == expected_account_types
