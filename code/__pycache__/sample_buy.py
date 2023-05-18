import pybybit
from settings import *

# テストネットでクライアントを作成
client = pybybit.API(key=api_key, secret=secret_key, testnet=True)

# ロングオーダーを発行する価格と数量を設定
symbol = 'BTCUSD'
side = 'Buy'  # 'Buy' for long, 'Sell' for short
order_type = 'Limit'  # 'Limit' for limit order, 'Market' for market order
qty = 1  # Quantity in BTC
price = 50000  # Price in USD

# 注文を出す
response = client.rest.inverse.private_order_create(
    symbol=symbol,
    side=side,
    order_type=order_type,
    qty=qty,
    price=price,
    time_in_force="GoodTillCancel"
)

# 注文のレスポンスを表示
print(response.json())
