# Requires python-requests. Install with pip:
#
#   pip install requests
#
# or, with easy-install:
#
#   easy_install requests


import json, hmac, hashlib, time, requests, base64
import signal
from requests.auth import AuthBase
from pprint import pprint
import sys

def log_trade(values):
    with open(log_filename,'a') as fd:
        fd.write(values)

def log_it(request):
    return
    with open(log_filename, 'ab') as fd:
            for chunk in request.iter_content(1024):
                fd.write(chunk)


# Create custom authentication for Exchange
class CoinbaseExchangeAuth(AuthBase):
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    def __call__(self, request):
        timestamp = str(time.time())
        message = timestamp + request.method + request.path_url + (request.body or '')
        hmac_key = base64.b64decode(self.secret_key)
        signature = hmac.new(hmac_key, message, hashlib.sha256)
        signature_b64 = signature.digest().encode('base64').rstrip('\n')

        request.headers.update({
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        })
        return request



#internal variable list:
calc_btc=0
calc_usd=0


#pseudo code
#read config from file
import ConfigParser
Config = ConfigParser.ConfigParser()
Config.read("coinbase.cfg")

# credentials
API_KEY = Config.get("coinbase","api_key")
API_SECRET = Config.get("coinbase","api_secret")
API_PASS = Config.get("coinbase","api_passphrase")

# offline balances to include
offline_btc = float(Config.get("coinbase","offline_btc"))
offline_usd = float(Config.get("coinbase","offline_usd"))

# ratio of bitcoin to dollars
ratio = float(Config.get("coinbase","ratio"))
# spread / imbalance that will trigger a trade
spread = float(Config.get("coinbase","ratio_spread"))
# frequency of polling
poll_delay = float(Config.get("coinbase","poll_delay"))
# trade sizes in btc
trade_size = float(Config.get("coinbase","trade_size"))

log_filename = Config.get("coinbase","log_file")

with open(log_filename,'ab') as f: f.write("\nRebalancing run started at {}\n".format(time.strftime('%x %X')))
    # log files to write to
    # crash recovery
    # gradual ratio change and period
        # when the ratio is too far out of balance with reality, a time frame within which to bring balance back.


# initialize communication
api_url = 'https://api.exchange.coinbase.com/'
auth = CoinbaseExchangeAuth(API_KEY, API_SECRET, API_PASS)


# gather data from exchange
# Get accounts
def get_balance():
    global my_price
    global low_price
    global high_price
    global calc_usd
    global calc_btc
    global price_h
    global price_l

    r = requests.get(api_url + 'accounts', auth=auth)
    log_it(r)
    #pprint(r.json())

    for item in r.json():
        if item['currency'] == "USD":
            usd_bal = float(item['balance'])

        if item['currency'] == "BTC":
            btc_bal = float(item['balance'])

    calc_btc = offline_btc + btc_bal
    #print('btc = {}'.format(calc_btc))
    calc_usd= offline_usd + usd_bal
    #print('usd = {}'.format(calc_usd))
    my_price = ((calc_usd/ratio) - calc_usd)/ calc_btc

    #sub optimal trade value
    high_price=round(((calc_usd/(ratio-spread)) - calc_usd)/ calc_btc,2)
    low_price=round(((calc_usd/(ratio+spread)) - calc_usd)/ calc_btc,2)

    #optimal trade value...
    price_h= round((calc_usd * (1-ratio))/((ratio*calc_btc) -trade_size),2)
    price_l= round((calc_usd * (1-ratio))/((ratio*calc_btc) +trade_size),2)



# balances available
get_balance()
prev_high=high_price
prev_low=low_price
#print('price_l = {}'.format(price_l))
#print('price_h = {}'.format(price_h))
calculated_spread = ratio - (calc_usd/(price_h*calc_btc + calc_usd))
#print('calculated spread is {}'.format(calculated_spread))


def make_trades():
    #print('making trades')
    global buy_id
    global sell_id

    get_balance()
    total = calc_btc*my_price + calc_usd
    print('portfolio value: ${}, my price is ${} best trades at ${} and ${}'.format(round(total,2),round(my_price,2),price_l,price_h))

    # prevent oscillations here
    global prev_high
    global prev_low
    if (prev_low >= high_price) | (prev_high <= low_price):
        optimal_spread = ratio - (calc_usd/(price_b*calc_btc + calc_usd))

        print('Oscillation prevented, try increasing spread ratio to something larger than {}'.format(optimal_spread/2))
        sys.exit(0)
    prev_high=high_price
    prev_low=low_price


    buy_order = {
        'size': trade_size,
        'price': price_l,
        'side': 'buy',
        'product_id': 'BTC-USD',
    }
    sell_order = {
        'size': trade_size,
        'price': price_h,
        'side': 'sell',
        'product_id': 'BTC-USD',
    }
    buy_req = requests.post(api_url + 'orders', data=json.dumps(buy_order), auth=auth)
    log_it(buy_req)
    sell_req = requests.post(api_url + 'orders', data=json.dumps(sell_order), auth=auth)
    log_it(sell_req)

    buy_id=buy_req.json()['id']
    sell_id=sell_req.json()['id']
    #print('my buy id is {}'.format(buy_id))
    #print('my sell id is {}'.format(sell_id))


    #pprint(buy_req.json())
    #pprint(sell_req.json())


def order_is_finished(order_id):
    order_req = requests.get(api_url + 'orders/' + order_id, auth=auth)
    log_it(order_req)
    #pprint(order_req.json())
    if (order_req.json()['status'] == 'open'):
        return False
    else:
        log_trade('{}\t{}\t{}\n'.format(time.strftime('%x %X'),order_req.json()['side'],order_req.json()['price']))
        print('{}: {} completed at ${}'.format(time.strftime('%x %X'),order_req.json()['side'],order_req.json()['price']))
        return True

def cancel_order(order_id):
    del_req = requests.delete(api_url + 'orders/' + order_id, auth=auth)
    log_it(del_req)

def trade():
    while(True):
        make_trades()
        while(True):
            if order_is_finished(buy_id):
                cancel_order(sell_id)
                time.sleep(poll_delay)
                break
            if order_is_finished(sell_id):
                cancel_order(buy_id)
                time.sleep(poll_delay)
                break
            #print('{}: no trades happened... looping'.format(time.strftime('%x %X')))
            time.sleep(poll_delay)
            continue


def cleanup(signum,frame):
    sys.exit(0) #exit early
    print('attempting to cleanup orders')
    try:
        cancel_order(buy_id)
    except:
        print('there was a problem cleaning up')
    try:
        cancel_order(sell_id)
    except:
        print('there was a problem cleaning up')
    sys.exit(0)

signal.signal(signal.SIGINT,cleanup)

#get_balance()
trade()

#print("my price is {}".format(my_price))
#print("my higher price is {}".format(high_price))
#print("my lower price is {}".format(low_price))

# current ticker
#tick_req=requests.get(api_url+'products/BTC-USD/ticker')
#print tick_req.json()


        # deposit/withdrawl detection
# calcuate trades based on info gathered

# make initial trades
    # poll for activity
    # handle trade activity
        #log activity
        #cancel obsolete trades
            #uses order-id
        #make new trades
