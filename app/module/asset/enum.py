from enum import StrEnum


class StockAsset(StrEnum):
    ID = "id"
    PURCHASE_CURRENCY_TYPE = "주식통화"
    STOCK_CODE = "주식코드"
    BUY_DATE = "구매일자"
    QUANTITY = "수량"
    ACCOUNT_TYPE = "계좌종류"
    CURRENT_PRICE = "현재가"
    DIVIDEND = "배당금"
    HIGHEST_PRICE = "고가"
    INVESTMENT_BANK = "증권사"
    LOWEST_PRICE = "저가"
    OPENING_PRICE = "시가"
    PROFIT_RATE = "수익률"
    PROFIT_AMOUNT = "수익금"
    PURCHASE_AMOUNT = "매입금"
    PURCHASE_PRICE = "매입가"
    STOCK_NAME = "종목명"
    STOCK_VOLUME = "거래량"


class BaseCurrency(StrEnum):
    WON = "won"
    DOLLAR = "dollar"


class CountryMarketCode(StrEnum):
    USA = "O"
    KOREA_KOSPI = "KS"
    KOREA_KOSDAQ = "KQ"
    JAPAN = "T"
    UK = "L"
    GERMANY = "DE"
    FRANCE = "PA"
    CHINA = "SS"
    HONGKONG = "HK"
    CANADA = "TO"
    AUSTRALIA = "AX"
    INDIA = "BO"
    BRAZIL = "SA"
    ITALY = "MI"
    SPAIN = "MC"
    SWITZERLAND = "SW"
    NETHERLAND = "AS"


class MarketIndex(StrEnum):
    KOSPI = "KS11"
    KOSDAQ = "KQ11"
    DOW_JONES = "DJI"
    NASDAQ = "IXIC"
    SP500 = "GSPC"
    NYSE_COMPOSITE = "NYA"
    NIKKEI_225 = "N225"
    FTSE_100 = "FTSE"
    DAX = "DAX"
    CAC_40 = "PX1"
    SHANGHAI = "000001.SS"
    HANG_SENG = "HSI"
    SP_TSX = "GSPTSE"
    ASX_200 = "AXJO"
    NIFTY_50 = "NSEI"
    BOVESPA = "BVSP"
    MOSCOW = "IMOEX"
    FTSE_MIB = "FTSEMIB.MI"
    IBEX_35 = "IBEX"
    SWISS_MARKET_INDEX = "SMI"
    AEX = "AEX"
    TSE_300 = "TSE"
    EURO_STOXX_50 = "SX5E"
    NYSE = "NYSE"


class PurchaseCurrencyType(StrEnum):
    KOREA = "KRW"
    USA = "USD"


class InvestmentBankType(StrEnum):
    TOSS = "토스증권"
    MIRAEASSET = "미래에셋증권"
    SAMSUNGINVESTMENT = "삼성투자증권"
    KOREAINVESTMENT = "한국투자증권"
    KB = "KB증권"
    DAISHIN = "대신증권"
    NH = "NH투자증권"
    SHINHANINVESTMENT = "신한투자증권"
    KIWOOM = "키움증권"


class AccountType(StrEnum):
    ISA = "ISA"
    IRP = "IRP"
    PENSION = "개인연금"
    REGULAR = "일반계좌"


class AssetType(StrEnum):
    STOCK = "stock"
    BOND = "bond"
    VIRTUAL_ASSET = "virtual_asset"
    CURRENCY = "currency"
    OTHER = "other"


class VirtualExchangeType(StrEnum):
    UPBIT = "upbit"
    BITHUMB = "bithumb"
    BINANCE = "binance"
    WALLET = "wallet"


class CurrencyType(StrEnum):
    KOREA = "KRW"
    USA = "USD"
    JAPAN = "JPY"
    AUSTRALIA = "AUD"
    BRAZIL = "BRL"
    CANADA = "CAD"
    CHINA = "CNY"
    EUROPE = "EUR"
    HONG_KONG = "HKD"
    INDIA = "INR"
    SWITZERLAND = "CHF"
    UNITED_KINGDOM = "GBP"


class TimeInterval(StrEnum):
    DAY = "1d"
    WEEK = "1wk"
    MONTH = "1mo"


class Country(StrEnum):
    USA = "USA"
    JAPAN = "JAPAN"
    UK = "UK"
    GERMANY = "GERMANY"
    FRANCE = "FRANCE"
    CHINA = "CHINA"
    HONGKONG = "HONGKONG"
    CANADA = "CANADA"
    AUSTRALIA = "AUSTRALIA"
    INDIA = "INDIA"
    BRAZIL = "BRAZIL"
    RUSSIA = "RUSSIA"
    ITALY = "ITALY"
    SPAIN = "SPAIN"
    SWITZERLAND = "SWITZERLAND"
    NETHERLAND = "NETHERLAND"
    EUROZONE = "EUROZONE"
    KOREA = "KOREA"
