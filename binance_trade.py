import sys, time

#read config
import configparser
Config = configparser.ConfigParser()
Config.read("binance.cfg")

# credentials
API_KEY = Config.get("binance","api_key")
API_SECRET = Config.get("binance","api_secret")
CURRENCY_A = Config.get("binance","currency_a")
CURRENCY_B = Config.get("binance","currency_b")
AMOUNT = Config.get("binance","amount")
POLL_TIME = Config.get("binance","poll_time")

#buying and selling currency A, using currency B
MARKET = CURRENCY_A + CURRENCY_B

#create comunication object
from binance.client import Client
client = Client(API_KEY, API_SECRET)

#sanity check keys and market
test_keys = client.get_asset_balance(asset=CURRENCY_A)
if isinstance(test_keys,dict) is False:
    print("invalid Key or Secret")
    sys.exit()

info = client.get_symbol_info(MARKET)
if isinstance(info,dict) is False:
    print("invalid market symbol")
    sys.exit()

#make trades
while(True):
    #check balances
    A = float(client.get_asset_balance(asset=CURRENCY_A)['free'])
    B = float(client.get_asset_balance(asset=CURRENCY_B)['free'])

    #calculate trades - This is the magic math!
    price = round(((B/ratio) - B)/ A,2)
    price_h= round((B * (1-ratio))/((ratio*A) -size),2)
    price_l= round((B * (1-ratio))/((ratio*A) +size),2)
    print('our price is {}, attempting to buy at {}, sell at {}'.format(price,price_l,price_h))

    #send trades to exchange
    buy_order_id = client.order_limit_buy(symbol=MARKET,quantity=AMOUNT,price=price_l)['orderId']
    sell_order = client.order_limit_sell(symbol=MARKET,quantity=AMOUNT,price=price_h)['orderId']
    #poll for trade execution

    while(True):
        #check each order and cancel/break on order filled
        time.sleep(POLL_TIME)
        if client.get_order(symbol=MARKET,orderId=buy_order_id)['tatus'] is "FILLED":
            client.cancel_order(symbol=MARKET,orderId=sell_order_id)
            print('{}: bought {} {} at {}'.format(time.strftime('%x %X')),AMOUNT,CURRENCY_A,price_l)
            break
        if client.get_order(symbol=MARKET,orderId=sell_order_id)['tatus'] is "FILLED":
            client.cancel_order(symbol=MARKET,orderId=buy_order_id)
            print('{}: sold {} {} at {}'.format(time.strftime('%x %X')),AMOUNT,CURRENCY_A,price_h)
            break