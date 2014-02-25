from __future__ import division
import hmac, base64, hashlib, urllib, urllib2, time, gzip, json, io
import pprint
base = 'https://data.mtgox.com/api/2/'
key = "" #api key
sec = "" #api secret

def sign(path, data):
    mac = hmac.new(base64.b64decode(sec), path+chr(0)+data, hashlib.sha512)
    return base64.b64encode(str(mac.digest()))

def req(path, inp={}, get=False):
    try:
        headers = {
            'User-Agent': "Trade-Bot",
            'Accept-Encoding': 'GZIP',
        }
        if get:
            get_data = urllib.urlencode(inp)
            url = base + path + "?" + get_data
            request = urllib2.Request(url, headers=headers)
            response = urllib2.urlopen(request)
        else:
            inp[u'tonce'] = str(int(time.time()*1e6))
            post_data = urllib.urlencode(inp)
            headers.update({
                'Rest-Key': key,
                'Rest-Sign': sign(path, post_data),
                'Content-Type': 'application/x-www-form-urlencoded',
            })
            request = urllib2.Request(base + path, post_data, headers)
            response = urllib2.urlopen(request, post_data)
    except urllib2.HTTPError as e:
        response = e.fp
    enc = response.info().get('Content-Encoding')
    if isinstance(enc, str) and enc.lower() == 'gzip':
        buff = io.BytesIO(response.read())
        response = gzip.GzipFile(fileobj=buff)
    try:
        output = json.load(response)
    except:
        #print "json error in response"
        #print response
        output = {'result':'json error'} 
    return output



# make single bid points. these bid points comprise a bid or ask equidistant around a specific price.
# each time the price passes that point, the bid/ask swaps.

class rebalance(object):
    def __init__(self,percentage):
        #percentage is decimal from 0 to 1 showing what portion of dollars to hold
        # (out of 1)
        self.percentage = percentage
        self.trade_fee = 0.6
        self.btc = 0
        self.usd = 0
        self.last = 0
        self.buy_trade = trade()
        self.sell_trade = trade()
    def start_trading(self,delay=60):
        print "starting trading"
        while True:
            self.one_trade()
            while self.watch_trades() == False:
                time.sleep(delay)
    def one_trade(self):        
        if self.get_data()== False:
            print "get_data returned False"
            return False
        self.sell_price = self.our_price * 1.07
        self.sell_trade.sell(self.sell_price)
        self.buy_price = self.our_price * 0.93
        self.buy_trade.buy(self.buy_price)
        print "asking ${}, bidding ${}".format(self.sell_price,self.buy_price)
        return True
    def watch_trades(self):
        if self.sell_trade.completed() == True:
            print "Sold BTC"
            self.buy_trade.cancel()
            return True
        if self.buy_trade.completed() == True:
            print "Bought BTC"
            self.sell_trade.cancel()
            return True
        return False
    def get_data(self):
        response = req('BTCUSD/money/info')
        if response['result'] == 'error':
            return false
        self.trade_fee = response['data']['Trade_Fee']
        self.btc = float(response['data']['Wallets']['BTC']['Balance']['value'])
        self.usd = float(response['data']['Wallets']['USD']['Balance']['value'])
        self.our_price = (self.usd/self.percentage - self.usd)/self.btc
        print "We have ${}, {} BTC, and our price is ${}".format(self.usd,self.btc,self.our_price)
        print "our current price is ${}".format(self.our_price)
        print "our current estimated portfolio value is ${}".format(self.usd + (self.btc * self.our_price))
    def get_market(self):
        response = req('BTCUSD/money/ticker_fast')
        if response['result'] == 'error':
            return
        self.last = float(response['data']['last']['value'])
class trade(object):
    def __init__(self):
        self.set_amount(0.01)
    def set_price(self,price):
        self.price = int(price * 100000.0)
    def set_amount(self,amount):
        self.amount = int(amount * 100000000.0)
    def buy(self,price):
        self.set_price(price)
        self.type = 'bid'
        self.send()
    def sell(self,price):
        self.set_price(price)
        self.type = 'ask'
        self.send()
    def send(self):
        self.transaction = req('BTCUSD/money/order/add',{"type":self.type,"amount_int":int(self.amount),"price_int": int(self.price)})
        if self.transaction['result'] != 'success':
            if self.transaction['error'] == 'Too many orders placed, please wait 45 secs':
                print "Throttling connection"
                time.sleep(45)
                self.send()
            print "Could not place {}".format(self.type)
    def completed(self):
        try:
            if self.type is 'ask':
                result = req('BTCUSD/money/order/result',{'type':'ask','order':self.transaction['data']})
            else:
                result = req('BTCUSD/money/order/result',{'type':'bid','order':self.transaction['data']})
            if result['result'] == 'error':
                return False
            return True
        except:
            return False
    def cancel(self):
        result = req('BTCUSD/money/order/cancel',{'oid':self.transaction['data']})

if __name__ == "__main__":
    account = rebalance(0.5)
    account.start_trading()
     
