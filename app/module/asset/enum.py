from enum import StrEnum


class ASSETNAME(StrEnum):
    ESTIMATE_ASSET = "예상자산"
    REAL_ASSET = "실질자산"


class AmountUnit(StrEnum):
    BILLION_WON = "억원"
    MILLION_WON = "만원"


class StockAsset(StrEnum):
    ID = "id"
    PURCHASE_CURRENCY_TYPE = "주식통화"
    STOCK_CODE = "주식코드"
    TRADE_DATE = "매매일자"
    QUANTITY = "수량"
    TRADE = "매매"
    ACCOUNT_TYPE = "계좌종류"
    CURRENT_PRICE = "현재가"
    DIVIDEND = "배당금"
    HIGHEST_PRICE = "고가"
    INVESTMENT_BANK = "증권사"
    LOWEST_PRICE = "저가"
    OPENING_PRICE = "시가"
    PROFIT_RATE = "수익률"
    PROFIT_AMOUNT = "수익금"  # [TODO] 명칭 PRECEED으로 변경 필요
    TRADE_AMOUNT = "거래금"  # 매수/매도 가격 * 수량 (자동 필드)
    TRADE_PRICE = "거래가"  # 매수/매도 가격(옵션 필드)
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


class TradeType(StrEnum):
    BUY = "매수"
    SELL = "매도"


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
    NONE = "기타"


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
    HONG_KONG = "HKD"
    INDIA = "INR"
    SWITZERLAND = "CHF"
    UNITED_KINGDOM = "GBP"
    EUROPE = "EUR"
    FRANCE = "EUR"
    GERMANY = "EUR"
    NETHERLAND = "EUR"
    ITALY = "EUR"
    SPAIN = "EUR"


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


class RichPeople(StrEnum):
    WARRENBUFFETT = "warren-buffett"
    BILLACKMAN = "bill-ackman"
    RAYDALIO = "ray-dalio"
    GEORGESOROS = "george-soros"
    DAVIDTEPPER = "david-tepper"
    JOHNPAULSON = "john-paulson"
    NELSONPELTZ = "nelson-peltz"
