import requests
import datetime
import time
from icecream import ic

# Polygon.io API 키 설정
API_KEY = "AHg4BmOVs2EYEtcvE7D56v8pFVdGBqBv"

# 종목 코드와 시작 날짜를 설정
TICKER = "AAPL"  

def fetch_aggregate_data_with_offset(ticker, start_offset, end_offset, timespan="minute", multiplier=1):
    """
    현재 시간 기준으로 특정 시간 범위의 데이터를 Unix Timestamp로 요청하는 함수
    """
    # 현재 시간 (밀리초 단위 Unix Timestamp)
    now = int(time.time() * 1000)
    
    # 시작 및 종료 시간 계산
    end_time = now - (end_offset * 60 * 1000)  # 종료 시간
    start_time = now - (start_offset * 60 * 1000)  # 시작 시간
    
    # Polygon.io API 호출
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{start_time}/{end_time}"
    params = {
        "adjusted": "true",
        "sort": "asc",
        "limit": 5000,
        "apiKey": API_KEY
    }
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        return data.get("results", [])
    else:
        print(f"Error: {response.status_code} - {response.json()}")
        return []

# 15분 전 ~ 25분 전 데이터 수집
data = fetch_aggregate_data_with_offset(TICKER, start_offset=25, end_offset=15)

# 데이터 출력
if data:
    print("15분 전 ~ 25분 전 데이터:")
    for record in data:
        # 타임스탬프를 사람이 읽을 수 있는 형식으로 변환
        timestamp = datetime.datetime.fromtimestamp(record["t"] / 1000)
        print(f"Time: {timestamp}, Open: {record['o']}, High: {record['h']}, Low: {record['l']}, Close: {record['c']}, Volume: {record['v']}")
else:
    print("15분 전 ~ 25분 전 데이터가 없습니다.")