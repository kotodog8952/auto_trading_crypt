import backtrader as bt

# 戦略クラスの定義
class SmaCross(bt.Strategy):
    params = (('pfast', 5), ('pslow', 20),)  # パラメータの設定

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.p.pfast)  # 短期移動平均
        sma2 = bt.ind.SMA(period=self.p.pslow)  # 長期移動平均
        self.crossover = bt.ind.CrossOver(sma1, sma2)  # クロスオーバー信号

    def next(self):
        portfolio_value = self.broker.get_value()

        # If portfolio value is below zero, exit any existing positions and do not initiate new trades
        if portfolio_value < 0:
            if self.position:
                self.log('Closing position, %.2f' % self.data.close[0])
                self.close()  # Close the position

        if not self.position:  # ポジションがない場合
            if self.crossover > 0:  # クロスオーバーが「ゴールデンクロス」を示す場合
                self.buy()  # 買う
        elif self.crossover < 0:  # クロスオーバーが「デッドクロス」を示す場合
            self.close()  # ポジションをクローズする


class SimpleStrategy(bt.Strategy):
    params = (
        ('max_position_size_ratio', 1/3),
    )

    def __init__(self):
        self.initial_portfolio_value = self.broker.get_value()
        self.max_position_size = self.initial_portfolio_value * self.params.max_position_size_ratio

    def log(self, text, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), text))

    def next(self):
        # Check the current value of the portfolio
        portfolio_value = self.broker.get_value()

        # If portfolio value is below zero, exit any existing positions and do not initiate new trades
        if portfolio_value < 0:
            if self.position:
                self.log('Closing position, %.2f' % self.data.close[0])
                self.close()  # Close the position
        else:
            # Do not open new position if it would exceed maximum position size
            # if self.position.size + self.data.close[0] > self.max_position_size:
            #     return
            
            if not self.position:  # no position is open
                if self.data.close[0] > self.data.open[0]:  # closing price is greater than opening price
                    self.log('BUY CREATE, %.2f' % self.data.close[0])
                    self.buy()  # buy
                elif self.data.close[0] < self.data.open[0]:  # closing price is less than opening price
                    self.log('SELL SHORT, %.2f' % self.data.close[0])
                    self.sell()  # short sell
            else:  # a position is open
                if self.position.size > 0 and self.data.close[0] < self.data.open[0]:  # if long position and closing price is less than opening price
                    self.log('SELL CREATE, %.2f' % self.data.close[0])
                    self.sell()  # sell
                elif self.position.size < 0 and self.data.close[0] > self.data.open[0]:  # if short position and closing price is greater than opening price
                    self.log('BUY COVER, %.2f' % self.data.close[0])
                    self.buy()  # short cover



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