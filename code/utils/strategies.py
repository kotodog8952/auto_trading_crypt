import backtrader as bt

# 戦略クラスの定義
class SmaCross(bt.Strategy):
    params = (('pfast', 10), ('pslow', 30),)  # パラメータの設定

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.p.pfast)  # 短期移動平均
        sma2 = bt.ind.SMA(period=self.p.pslow)  # 長期移動平均
        self.crossover = bt.ind.CrossOver(sma1, sma2)  # クロスオーバー信号

    def next(self):
        if not self.position:  # ポジションがない場合
            if self.crossover > 0:  # クロスオーバーが「ゴールデンクロス」を示す場合
                self.buy()  # 買う
        elif self.crossover < 0:  # クロスオーバーが「デッドクロス」を示す場合
            self.close()  # ポジションをクローズする


class SimpleStrategy(bt.Strategy):

    def log(self, text, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), text))

    def next(self):
        if not self.position:  # ポジションがない場合
            if self.data.close[0] > self.data.open[0]:  # 終値が開始価格よりも高い場合
                self.log('BUY CREATE, %.2f' % self.data.close[0])
                self.buy()  # 購入する
            elif self.data.close[0] < self.data.open[0]:  # 終値が開始価格よりも低い場合
                self.log('SELL SHORT, %.2f' % self.data.close[0])
                self.sell()  # 空売り（ショート）する
        else:  # ポジションがある場合
            if self.position.size > 0 and self.data.close[0] < self.data.open[0]:  # 買いポジションがあり、終値が開始価格よりも低い場合
                self.log('SELL CREATE, %.2f' % self.data.close[0])
                self.sell()  # 売却する
            elif self.position.size < 0 and self.data.close[0] > self.data.open[0]:  # 売りポジションがあり、終値が開始価格よりも高い場合
                self.log('BUY COVER, %.2f' % self.data.close[0])
                self.buy()  # 買い戻し（ショートカバー）する


class HigeCatchStrategy(bt.Strategy):
    params = (
        ('long_percentage', 0.05),
        ('short_percentage', 0.05),
    )

    def log(self, text, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), text))

    def next(self):
        if not self.position:  # ポジションがない場合
            if self.data.close[0] > self.data.low[0] * (1 + self.params.long_percentage):  # 前日の終値が前日の安値から一定比率以上上昇していたら
                self.log('BUY CREATE, %.2f' % self.data.close[0])
                self.buy()  # 買い注文
            elif self.data.close[0] < self.data.high[0] * (1 - self.params.short_percentage):  # 前日の終値が前日の高値から一定比率以上下落していたら
                self.log('SELL SHORT, %.2f' % self.data.close[0])
                self.sell()  # 売り注文
        else:  # ポジションがある場合
            if self.position.size > 0:  # ロングポジションを持っている場合
                self.log('SELL CREATE, %.2f' % self.data.close[0])
                self.sell()  # 売り注文（ポジションのクローズ）
            elif self.position.size < 0:  # ショートポジションを持っている場合
                self.log('BUY COVER, %.2f' % self.data.close[0])
                self.buy()  # 買い注文（ポジションのクローズ）