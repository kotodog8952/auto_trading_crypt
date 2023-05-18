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
from datetime import timedelta, timezone, datetime
import math
import matplotlib.pyplot as plt
import pybybit
import numpy as np
import pandas as pd
from tqdm import tqdm
from matplotlib import pyplot as plt
from utils.settings import *

# %%
symbol    = "BTCUSD"
chart_min = 60 # 時間軸(1 3 5 15 30 60 120 240 360 720 )
start     = '2022/01/01 09:00' # ローソク足取得開始時刻
get_days  = 30 # 取得数[日]

# %%
# ローソク足のリサンプリング
def resample_ohlc(org_df, timeframe):
   org_df.index = org_df.index - timedelta(hours=9)
   df = org_df.resample(f'{timeframe*60}S').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'})
   df['close'] = df['close'].fillna(method='ffill')
   df['open'] = df['open'].fillna(df['close'])
   df['high'] = df['high'].fillna(df['close'])
   df['low'] = df['low'].fillna(df['close'])
   org_df.index = org_df.index + timedelta(hours=9)
   df.index = df.index + timedelta(hours=9)

   return df

# %%
def get_price_from_API(chart_min,start):
    bybit = pybybit.API(testnet = False)

    get_start = int(datetime.strptime(start,'%Y/%m/%d %H:%M').timestamp()) # タイムスタンプ変換
    price = []
    req_times = math.ceil(1440/chart_min*get_days/200)

    #200*n本のローソク足を取得して、price[]に入れる
    for o in tqdm(range(req_times), desc = "{}分足データ取得中".format(chart_min)): # ()内の回数だけデータを取得
        data = bybit.rest.inverse.public_kline_list(
                symbol   = symbol,
                interval = chart_min,
                from_    = get_start
                ).json()

        #priceに取得したデータを入れる
        for i in data["result"]:
            price.append(i)

        #200本x足の長さ分だけタイムスタンプを進める
        get_start += 200*60*chart_min

    return pd.DataFrame(price)

# %%
# ローソク足データの読み込み
df_all = get_price_from_API(chart_min,start)
df_all.open_time = pd.to_datetime(df_all.open_time*10**9,)
df_all = df_all.set_index('open_time').tz_localize('UTC').tz_convert('Asia/Tokyo')
df_all.drop(["symbol"],axis = 1,inplace=True)
df_all = df_all.astype('float')

# %%
# バックテスト区間を指定して5分足に変換
df = resample_ohlc(df_all['2022/01/01':'2022/01/31'],5)
print( df )

# %%
# ロジック部
entryLength=35
entryPoint=0.7
df['sell'] = df['high'].rolling(entryLength).max() * (1+entryPoint/100)
df['buy'] = df['low'].rolling(entryLength).min() * (1-entryPoint/100)
print( df )

# %%
# 指値位置補正(post only)
df['limit'] = df['open'].shift(-1)
df['buy'] = df[['buy', 'limit']].min(axis='columns')
df['sell'] = df[['sell', 'limit']].max(axis='columns')

# %%
# 約定判断
df['long'] = df['low'] < df['buy'].shift(1)    # 買い指値ヒット
df['short'] = df['high'] > df['sell'].shift(1) # 売り指値ヒット

# %%
# ポジション計算部（ドテン＆ピラミッディング）
pyramiding=3
df['order'] = 0
df['order'] = df['order'].where(df['long']!=True,1)
df['order'] = df['order'].where(df['short']!=True,-1)
df['pos'] = df['order'].where(df['order']!=0,).fillna(method='ffill').fillna(0)
df['pos'] = df.groupby((df['pos']*df['pos'].shift(1)<0).cumsum().fillna(0))['order'].cumsum()
df['pos'] = df['pos'].where(df['pos']<=pyramiding,pyramiding ) 
df['pos'] = df['pos'].where(df['pos']>=-pyramiding,-pyramiding )
print( df )

# %%
# 約定価格
df['exec_price'] = df['close']
df['exec_price'] = df['buy'].where(df['long'].shift(-1),df['exec_price'])
df['exec_price'] = df['sell'].where(df['short'].shift(-1),df['exec_price'])

# %%
# 累積損益計算
commision=-0.025
df['pos'] /= pyramiding
df['return']=df['exec_price'].diff(1)
df['commision'] = df['exec_price'] * commision / 100 * abs(df['pos']-df['pos'].shift(1))
df['profit'] = df['return']*df['pos'] -df['commision']
df['pnl'] = df['profit'].cumsum()

# %%
# ポジション変化が有ったところだけを抽出
df_only_hit = df[df['pos'].diff(1)!=0]

# %%
# 前後1日間のボトム/ピークの箇所だけをデータを適当に抽出して間引く(全部プロットしたら時間かかるため）
period_day = int(86400 / (df.index[-1].to_pydatetime().timestamp()-df.index[-2].to_pydatetime().timestamp()) )
df_bottom_peak = df[df['low']==df['low'].rolling(period_day,center=True).min()]  # ボトム部
df_top_peak = df[df['high']==df['high'].rolling(period_day,center=True).max()]  # トップ部

# %%
# ポジション変化したところとボトムピーク部と最終行を結合してプロットするデータを用意する
df = pd.concat( [df_only_hit, df_bottom_peak, df_top_peak, df.tail(1)] ).sort_index().drop_duplicates()

# %%
# 損益グラフプロット
fig = plt.figure()
ax1 = fig.subplots()
ax2 = ax1.twinx()
ax1.set_ylim([-1,5])
ax1.bar(df.index, df["pos"], color='blue', alpha=0.5, zorder=1)
ax1.axhline(y=0, color='k', linestyle='dashed', alpha=0.5, linewidth=0.5 )
ax1.axhline(y=1, color='k', linestyle='dashed', alpha=0.5, linewidth=0.5)
ax1.set_ylabel("pos")
ax2.plot(df.index, df["pnl"], color='red', zorder=2, linewidth=2)
ax2.set_ylabel("profit")
h1, l1 = ax2.get_legend_handles_labels()
ax1.legend(h1, l1, loc='upper left', prop={'size': 8})
plt.title('Backtest : {:+.0f}'.format(df['pnl'][-1]))
plt.show()
