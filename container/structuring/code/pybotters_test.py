import pandas as pd
import pybotters
from datetime import timedelta

class DataFetcher:
    def __init__(self, start_date, end_date, symbol, interval, limit):
        self.start_date = start_date
        self.end_date = end_date
        self.symbol = symbol
        self.interval = interval
        self.limit = limit

    async def get_data(self) -> pd.DataFrame:
        df = pd.DataFrame()
        current_date = self.start_date

        async with pybotters.Client() as client:
            while current_date < self.end_date:
                params = {
                    'symbol': self.symbol,
                    'interval': self.interval,
                    'from': int(current_date.timestamp()),
                    'limit': self.limit
                }
                response = await client.get('https://api.bybit.com/v2/public/kline/list', params=params)
                data = await response.json()
                temp_df = pd.DataFrame(data['result'])
                temp_df['opentime'] = pd.to_datetime(temp_df['open_time'], unit='s')
                temp_df.set_index('opentime', inplace=True)
                temp_df.index = pd.to_datetime(temp_df.index, format='%Y-%m-%d')
                temp_df['open'] = temp_df['open'].astype(float)
                temp_df['high'] = temp_df['high'].astype(float)
                temp_df['low'] = temp_df['low'].astype(float)
                temp_df['close'] = temp_df['close'].astype(float)
                temp_df['volume'] = temp_df['volume'].astype(float)
                df = pd.concat([df, temp_df])
                current_date = df.index[-1] + timedelta(minutes=15)

        df.columns = ['symbol', 'interval', 'open_time', 'open', 'high', 'low', 'close', 'volume', 'turnover']
        df = df[self.start_date:self.end_date]
        return df


from datetime import datetime
import asyncio

async def main():
    # データ取得のパラメータを設定
    start_date = datetime(2022, 1, 1)  # 2022年1月1日から開始
    end_date = datetime(2022, 1, 31)   # 2022年1月31日まで
    symbol = 'BTCUSD'                  # ビットコイン/USDの市場データを取得
    interval = '60'                    # 1時間ごとのデータ
    limit = 200                        # 一度に取得するデータの最大数
    dl = DataFetcher(start_date, end_date, symbol, interval, limit)
    df = await dl.get_data()
    print(df)

# 非同期イベントループを開始し、main関数を実行
asyncio.run(main())