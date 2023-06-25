# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     custom_cell_magics: kql
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.2
#   kernelspec:
#     display_name: auto_trading
#     language: python
#     name: python3
# ---

# %%
import sys
sys.path.append('./code/utils')
sys.path.append('./code/strategies')
from utils.settings import *
from utils.strategies import *
import matplotlib.pyplot as plt
import pybybit
from datetime import datetime, timedelta
import pandas as pd
import json
from dateutil.relativedelta import relativedelta
import pandas as pd
import matplotlib.pyplot as pltß
import os
from datetime import datetime

def make_output_dir(base_dir='./data/output'):
    '''
    yyyymmdd+ミリ秒のフォルダを作成フォルダ名をreturn
    
    Args:
        base_dir(str): 基底フォルダ
    Returns:
        str: 作成したフォルダ名
    '''
    
    

    return save_dir


def plot_monthly_trades(df, trades, save_dir):
    # データを月ごとに分割
    df = df.assign(month = df.index.to_period('M'))

    for month in df['month'].unique():
        # その月のデータを取得
        monthly_df = df[df['month'] == month]

        # その月のトレード情報を取得
        monthly_trades = [trade for trade in trades if trade['entry_date'].month == month]

        # プロット
        plt.figure(figsize=(10, 5))
        plt.plot(monthly_df.index, monthly_df['close'])

        for trade in monthly_trades:
            entry_date = trade['entry_date']
            exit_date = trade['exit_date']
            entry_price = trade['entry_price']
            exit_price = trade['exit_price']

            # 買った時点を赤色の点で表示
            plt.plot(entry_date, entry_price, 'ro')
            # 売った時点を緑色の点で表示
            plt.plot(exit_date, exit_price, 'go')

        plt.title(f'Trade Trajectory for {month}')
        plt.xlabel('Date')
        plt.ylabel('Price')

        # プロットを保存するためのパスを作成
        save_path = os.path.join(save_dir, f'Trade_Trajectory_{month}.png')

        # プロットを指定されたパスに保存
        plt.savefig(save_path)

        # プロットを表示（必要に応じて）
        # plt.show()



# %%
# BybitのAPIに接続します。
client = pybybit.API(key=api_key, secret=secret_key, testnet=True)


def get_data(start_date: datetime, end_date: datetime, client: pybybit.api.API ):

    df = pd.DataFrame()
    current_date = start_date
    while current_date < end_date:
        response = client.rest.inverse.public_kline_list(symbol='BTCUSD', interval='15', from_=int(current_date.timestamp()), limit=200)
        data = response.json()
        temp_df = pd.DataFrame(data['result'])
        # temp_df.columns = ['symbol', 'interval', 'open_time', 'open', 'high', 'low', 'close', 'volume', 'turnover']
        temp_df['opentime'] = pd.to_datetime(temp_df['open_time'], unit='s')
        temp_df.set_index('opentime', inplace=True)
        temp_df.index = pd.to_datetime(temp_df.index, format='%Y-%m-%d')
        temp_df['open_time'] = pd.to_datetime(temp_df['open_time'], unit='s')
        temp_df['open'] = temp_df['open'].astype(float)
        temp_df['high'] = temp_df['high'].astype(float)
        temp_df['low'] = temp_df['low'].astype(float)
        temp_df['close'] = temp_df['close'].astype(float)
        temp_df['volume'] = temp_df['volume'].astype(float)
        # df = df.append(temp_df)
        df = pd.concat([df, temp_df])
        current_date = df.index[-1] + timedelta(minutes=15)
    df.columns = ['symbol', 'interval', 'open_time', 'open', 'high', 'low', 'close', 'volume', 'turnover']
    df = df[start_date:end_date] # Make sure the dataframe is within the required date range.
    return df

def run_backtest(df, start_portfolio, save_dir, start_date):
    # Create a cerebro
    cerebro = bt.Cerebro()

    # Create a data feed
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.addstrategy(SimpleStrategy)

    # 初期のポートフォリオの値を設定します（例：10,000ドル）
    cerebro.broker.setcash(float(start_portfolio))

    # Add a transactions analyzer
    cerebro.addanalyzer(bt.analyzers.Transactions)

    # Run the backtest
    results = cerebro.run()

    # バックテスト後の最終的なポートフォリオの値を出力します。
    final_portfolio_value = cerebro.broker.getvalue()
    print('Final Portfolio Value: %.2f' % final_portfolio_value)# 初期のポートフォリオの値を設定します（例：10,000ドル）

    # Get the transactions
    transactions = results[0].analyzers.transactions.get_analysis()

    # Prepare a list for the formatted transactions
    formatted_transactions = []

    for date, transaction_dic in transactions.items():
        size = transaction_dic[0][4]
        action = 'BUY' if size > 0 else 'SELL SHORT'
        price = transaction_dic[0][1]
        
        # Format the transaction
        formatted_transactions.append({
            'entry_date': date,
            'action': action,
            'price': price
        })

    # Convert the transactions to a DataFrame and save to CSV
    trades_df = pd.DataFrame(formatted_transactions)
    trades_df.to_csv(f'{save_dir}/{start_date.year}{start_date.month}_trades.csv', index=False)
    
    with open(f'{save_dir}/{start_date.year}{start_date.month}_final_portfolio_value.txt', 'w') as f:
        f.write('Final Portfolio Value: %.2f' % final_portfolio_value)

    return formatted_transactions



# Get today's date
now = datetime.now() - relativedelta(day=1)

# Get the date six months ago
six_months_ago = now - relativedelta(months=6)

# Get the start date of each month
start_dates = [six_months_ago.replace(day=1) + relativedelta(months=i) for i in range(6)]


# Get the end date of each month
end_dates = [start_date + relativedelta(months=1, days=-1) for start_date in start_dates]


# Get the data for the whole period
df = get_data(six_months_ago, now, client)

# 現在の日時を取得し、フォルダ名の形式に変換
now = datetime.now()
dir_name = now.strftime('%Y%m%d%H%M%S%f')
base_dir = './data/output'
save_dir = os.path.join(base_dir, dir_name)

# ディレクトリが存在しない場合は作成
os.makedirs(save_dir, exist_ok=True)

# Run the backtest for each month
for start_date, end_date in zip(start_dates, end_dates):
    print(f"Running backtest for {start_date.strftime('%Y-%m')}")
    df_month = df[start_date:end_date]
    trades = run_backtest(df_month, 10000, save_dir, start_date)
    # Plot the trades
    plot_monthly_trades(df_month, trades, save_dir)