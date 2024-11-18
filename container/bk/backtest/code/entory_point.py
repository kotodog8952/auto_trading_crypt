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
import argparse

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


def run_backtest(df, start_portfolio, save_dir, start_date, commission, strategy):
    # Create a cerebro
    cerebro = bt.Cerebro()

    # Set the commission 
    cerebro.broker.setcommission(commission=commission)

    # Create a data feed
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.addstrategy(strategy)

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
    trades_df.to_csv(f'{save_dir}/{start_date.year:04}{start_date.month:02}_trades.csv', index=False)

    with open(f'{save_dir}/final_portfolio_value.txt', 'a') as f:
        f.write(f'{start_date.year:04}{start_date.month:02} Final Portfolio Value: {final_portfolio_value:02}\n' )

    return formatted_transactions

def main(args):

    client = pybybit.API(key=api_key, secret=secret_key)

    # Get today's date
    end_date = datetime.strptime(args.end_date, '%Y%m%d')

    # Get the date six months ago
    start_date = end_date - relativedelta(months=6)

    # Get the data for the whole period
    df = get_data(start_date, end_date, client, args.symbol, args.interval, args.limit)

    # 現在の日時を取得し、フォルダ名の形式に変換
    now = datetime.now()
    dir_name = now.strftime('%Y%m%d%H%M%S%f')
    base_dir = './data/output'
    save_dir = os.path.join(base_dir, dir_name)

    # ディレクトリが存在しない場合は作成
    os.makedirs(save_dir, exist_ok=True)

    # Get the start date of each month
    start_dates = [start_date.replace(day=1) + relativedelta(months=i) for i in range(args.backtest_period)]

    # Get the end date of each month
    end_dates = [start_date + relativedelta(months=1, days=-1) for start_date in start_dates]

    # Run the backtest for each month
    for start_date, end_date in zip(start_dates, end_dates):
        print(f"Running backtest for {start_date.strftime('%Y-%m')}")
        df_month = df[start_date:end_date]
        trades = run_backtest(df_month, args.start_portfolio, save_dir, start_date, args.commission, args.strategy)
        # Plot the trades
        plot_monthly_trades(df_month, trades, save_dir)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='自動売買bot作成に関するパラメータ設定')

    # 引数設定
    parser.add_argument('--backtest_period', help='バックテスト期間(default: 6ヶ月)', type=int, default=6)
    parser.add_argument('--end_date', help='バックテスト終了日', type=str, default='20230601')
    parser.add_argument('--interval', help='蝋燭足の時間軸', type=str, default='D')
    parser.add_argument('--symbol', help='売買対象銘柄(default: BTC)', type=str, default='BTCUSD')
    parser.add_argument('--limit', help='一度に取得する蝋燭足の上限', type=int, default=200)
    parser.add_argument('--commission', help='売買に伴う手数料', type=int, default=0.0006)
    parser.add_argument('--strategy', help='売買時の戦略', type=bt.Strategy, default=SimpleStrategy)
    parser.add_argument('--start_portfolio', help='各月バックテスト開始時のポートフォリオ', type=int, default=10000)

    args = parser.parse_args()

    # メイン関数実行
    main(args=args)