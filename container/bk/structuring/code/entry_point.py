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
import json
import os
from datetime import datetime, timedelta
import argparse
import hashlib
import asyncio

from ruamel.yaml import YAML
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import pandas as pd
import pybotters

# 現在のスクリプトの絶対パスを取得
current_path = os.path.abspath(os.path.dirname(__file__))

# utils ディレクトリの絶対パスを取得
utils_path = os.path.join(current_path, './utils')

# sys.pathにutilsの絶対パスを追加
sys.path.append(utils_path)

# 定数定義
INPUT_DIR = '/opt/ml/input'
OUTPUT_DIR = 'opt/ml/output'

class StruturingSymbolData():
    def __init__(self, args) -> None:
        self.end_date = datetime.strptime(args.end_date, "%Y%m%d")
        self.backtest_period = args.backtest_period
        self.symbol = args.symbol
        self.interval = args.interval
        self.limit = args.limit
        
        self.start_date = self.end_date - relativedelta(months=self.backtest_period)
    
    def _get_interval_in_minutes(self) -> int or str:
        '''
        Available intervals:

        1 3 5 15 30 (min)
        60 120 240 360 720 (min)
        D (day)
        W (week)
        M (month)
        
        この内60~720min(入力時には1h単位で入力を想定),D, Wについて分に変換する
        月足に関しては使わんのと月によって日数が変わってめんどくさいのでなかったことにする
        
        '''
        
        # TODO 入力規制が必要かなあ(上記以外の値が与えられたら例外)
        min_interval_dic = {'1h': 60, '2h': 120, '4h': 240, '6h': 360, '12h': 720, 'D': 60*24, 'W': 60*24*7}
        return self.interval if isinstance(int, self.interval) else min_interval_dic[self.interval]
        
    def _get_response_list(self):
        '''
        start_date, end_date, intervalに対応した期間内の日付のリストを生成する
        '''
        
        interval = self._get_interval_in_minutes(self)
        response_list = [date for date in range(self.start_date, self.end_date - timedelta(minutes=interval))]

        return response_list
    
    def _get_same_params_dir(self) -> str:
        
        '''
        input内に入力と全く同じパラメータを持つ保存データが存在するかチェックする
        params.jsonの中のkey部分を一つの文字列にまとめる
        ↑をhash関数で変換、変換後の値を比較する
        
        全く同じパラメータを持つ保存データがあれば対象のフォルダ名を、無ければNoneを返す
        '''
        
        target_hash_key = self._make_match_params_key()
        
        # inputフォルダ内を走査
        for folder_name in os.listdir(INPUT_DIR):
            folder_path = os.path.join(INPUT_DIR, folder_name)

            # フォルダのみを対象とする
            if os.path.isdir(folder_path):
                # フォルダ内のJSONファイルを確認
                for file_name in os.listdir(folder_path):
                    if file_name.endswith('.json'):
                        file_path = os.path.join(folder_path, file_name)
                        
                        # JSONファイルを読み込む
                        with open(file_path, 'r') as file:
                            params = json.load(file)
                            
                            # match_params_keyと引数のkeyを比較
                            if params.get('match_params_key') == target_hash_key:
                                return folder_name
        
        return None 
        
    
    def _is_else_parameters_symbol_data(self) -> bool:
        '''
        input内に全く同じパラメータを持つ保存データがあればTrue、なければFalseを返す
        '''
        
        if self._get_same_params_dir() == None:
            return False
        else :
            return True

    def dump_params(self) -> None:
        '''
        _is_else_parameters_symbol_dataがfalse(=input内に入力と全く同じパラメータを持つ保存データが存在しない)場合、
        yyyymmdd+m秒の形式でフォルダを作成する
        加えて、今回のパラメータをyaml形式でdumpする
        '''

        # get current date and time
        now = datetime.now()

        # format as a string: 'yyyymmddmmss'
        folder_name = now.strftime('%Y%m%d%H%M%S')

        # create the new folder
        self._output_dir_name = f'./output/{folder_name}'
        os.mkdir(self.output_dir_name)
        
        self._dump_json()
        
        return None
    
    def _dump_json(self):
         # dump into json
         
        params_dic = {
            'backtest_period': self.backtest_period,
            'end_date': self.end_date,
            'symbol': self.symbol,
            'interval': self.interval,
            'limit': self.limit,
            'match_params_key' : self._make_match_params_key()
        }
        with open(f'{self.output_dir_name}/params.json', 'w') as json_file:
            json.dump(params_dic, json_file)
            
    def _make_match_params_key(self):
        
        '''
        パラメータを一つの文字列にまとめ、その後ハッシュ化
        '''
        
        data_string = ''.join([self.backtest_period,
                               self.start_date, 
                               self.end_date, 
                               self.symbol, 
                               self.interval, 
                               self.limit, 
                               ])

        hash_object = hashlib.sha256(data_string.encode())
        hex_dig = hash_object.hexdigest()

        return hex_dig

    def get_data(self) -> pd.DataFrame:
        '''
        response_list内の日付に対してsymbolに対する価格データを取得する
        '''

        client = pybybit.API(key=api_key.api_key, secret=api_key.secret_key)

        df = pd.DataFrame()
        current_date = self.start_date
        while current_date < self.end_date:
            response = client.rest.inverse.public_kline_list(symbol=self.symbol, interval=self.interval, from_=int(current_date.timestamp()), limit=self.limit)
            data = response.json()
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
        df = df[self.start_date:self.end_date] # Make sure the dataframe is within the required date range.
        return df

    def run(self):
        '''
        入力されたパラメータ(期間やインターバル等)に対し、過去全く同じ構成でダウンロードしていたものがあればそれを使う
        なければ別途ダウンロードして保存し、次回以降はそれを使う
        '''

        if self._is_else_parameters_symbol_data:
            # 現在のパラメータと全く同じ構成の保存データが存在する場合
            df = pd.read_csv(f'{INPUT_DIR}/{self._get_same_params_dir()}/symbol_data.csv')
        else:
            # 現在のパラメータと全く同じ構成の保存データが存在しない場合
            df = self.get_data()

            # パラメータをdump
            self.dump_params()

            # dfをcsvで保存
            df.to_pickle(f'{INPUT_DIR}/symbol_data.csv')

        return df

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='自動売買bot作成に関するパラメータ設定')

    # 引数設定
    parser.add_argument('--backtest_period', help='バックテスト期間(default: 6ヶ月)', type=int, default=6)
    parser.add_argument('--end_date', help='バックテスト終了日', type=str, default='20230601')
    parser.add_argument('--interval', help='蝋燭足の時間軸', type=str, default='D')
    parser.add_argument('--symbol', help='売買対象銘柄(default: BTC)', type=str, default='BTCUSD')
    parser.add_argument('--limit', help='一度に取得する蝋燭足の上限', type=int, default=200)

    args = parser.parse_args()

    # メイン関数実行
    StruturingSymbolData(args).run()