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
from settings import *
from strategies import *
import matplotlib.pyplot as plt
import pybybit
from datetime import datetime, timedelta
import pandas as pd
import json

# %%
# BybitのAPIに接続します。
client = pybybit.API(key=api_key, secret=secret_key, testnet=True)

# %%
now = datetime.utcnow()
# 1ヶ月前の時間を取得
one_month_ago = now - timedelta(days=30)
# yesterday = now - timedelta(days=1)

# %%
# タイムスタンプをUnix時間に変換
# yesterday_unix = int(yesterday.timestamp())
one_month_ago_unix = int(one_month_ago.timestamp())
now_unix = int(now.timestamp())

# %%
data = client.rest.inverse.public_kline_list(symbol='BTCUSD', interval='60', from_=one_month_ago_unix, limit=200)

# %%
# レスポンスオブジェクトから JSON データを取得
parsed_data = data.json()

# JSON データから必要な部分だけを取り出し、データフレームに変換
df = pd.DataFrame(parsed_data['result'])

# データ型の変換
df['open_time'] = pd.to_datetime(df['open_time'], unit='s')
df['open'] = df['open'].astype(float)
df['high'] = df['high'].astype(float)
df['low'] = df['low'].astype(float)
df['close'] = df['close'].astype(float)
df['volume'] = df['volume'].astype(float)
df.set_index('open_time', inplace=True)

# %%
# DataFrameをBacktraderのデータフィードに変換
data_feed = bt.feeds.PandasData(dataname=df)


# %%
# Cerebroエンジンの初期化
cerebro = bt.Cerebro()

# %%
# データフィードの追加
cerebro.adddata(data_feed)

# %%
# 戦略の追加
cerebro.addstrategy(HigeCatchStrategy)

# %%

# 初期のポートフォリオの値を設定します（例：10,000ドル）
cerebro.broker.setcash(10000.0)

# バックテストを実行します。
cerebro.run()

# バックテスト後の最終的なポートフォリオの値を出力します。
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())# 初期のポートフォリオの値を設定します（例：10,000ドル）

# %%
# バックテストの結果をプロット
plt.figure(figsize=(10, 5))  # 幅10、高さ5のフィギュアを作成
plt.rcParams['font.size'] = 14  # フォントサイズを14に設定
cerebro.plot(style='candle')

# プロットの調整
plt.tight_layout()
plt.show()

# バックテストの実行とその結果を格納
result = cerebro.run()

# 結果の中から最初のストラテジーを取得
strategy = result[0]

# 取得したストラテジーからデータを取り出し
portfolio_value = strategy.stats.broker.value.get(size=len(strategy))
cash = strategy.stats.broker.cash.get(size=len(strategy))

# プロット


plt.figure(figsize=(10,5))
plt.plot(portfolio_value, label='Portfolio Value')
plt.plot(cash, label='Cash')
plt.legend()
plt.grid()
plt.show()

