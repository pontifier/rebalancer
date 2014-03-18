import hmac, hashlib
import urllib.parse
import requests, json
import time


key = "" #your btc-e.com API key
sec = "" #your btc-e.com secret

# important:
# This program can lose all your funds easily.
# There is a very real chance for it to get into
# a loop and start buying high and selling low
# if your funds are too low.

# Watch it carefully until you understand how it works.

# This program will make trades on your account.
# It does this by calculating an expected price
# between 2 of your currencies, and a ratio that you select.

# The default is xpm and btc with a ratio of 50%

# change the values in the main function at the
# bottom of this file to select which currencies
# you want to trade






class btce_connection(object):
    def __init__(self,api_key,api_secret):
        self.api_url = 'https://btc-e.com/tapi'
        self.api_key = api_key
        self.api_secret = api_secret.encode()
        self.signer = hmac.new(self.api_secret,digestmod=hashlib.sha512)
    def submit(self,data):
        # add or overwrite nonce
        time.sleep(2)
        data['nonce'] = str(time.time()).split('.')[0]
        # create signed header
        databytes = urllib.parse.urlencode(data).encode()
        signature = hmac.new(self.api_secret,databytes,digestmod=hashlib.sha512).hexdigest()
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Key":self.api_key,
                   "Sign":signature}
        self.result = requests.post(self.api_url,data=databytes,headers=headers)
        #make sure we got valid data back.
        try:
            self.result.json()
        except:
            #recursive retry
            print('[ {} ] Invalid Server Response'.format(time.strftime('%I:%M:%S %p')))
            time.sleep(30)
            self.submit(data)
    def update_balances(self,funds):
        self.funds = {}
        for key,value in funds.items():
            self.funds[key] = float(value)
    def getinfo(self):
        data = {"method":"getInfo"}
        self.submit(data)
        # fill up balances array
        values = self.result.json()
        if values['success'] == 1:
            self.update_balances(values['return']['funds'])
            
    def trade(self,market_pair,trade_type,price,amount):
        #type is buy or sell (coresponds to buying or selling the first currency in the pair.
        #price and amount is amount of first currency to trade, at price*second currency each.
        data={'method':'Trade','pair':market_pair,'type':trade_type,'rate':price,'amount':amount}
        self.submit(data)
        values = self.result.json()
        if values['success'] == 1:
            self.update_balances(values['return']['funds'])
            return self.result.json()['return']['order_id']
        return False
    def orders(self):
        data={'method':'ActiveOrders'}
        self.submit(data)
        values = self.result.json()
        self.order_return = self.result.json()
        #print(self.order_return)
        if values['success'] == 1:
            return self.result.json()['return']
        return False
    def cancel(self,orderid):
        data={'method':'CancelOrder','order_id':orderid}
        self.submit(data)

class rebalance(object):
    def __init__(self,currency1, currency2, percentage,spread = 0.02, amount = 0.1):
        print('Rebalancer will start trading on BTC-E in 30 seconds')
        print('Set to make trades of {} {} against {}'.format(amount,currency1,currency2))
        print('Will attempt to keep the ratio at {}'.format(percentage))
        print('press ctrl-C to quit')
        time.sleep(30)
        self.market = "{}_{}".format(currency1.lower(),currency2.lower())
        self.c1 = currency1.lower()
        self.c2 = currency2.lower()
        self.percentage = percentage
        self.fee = 0.002
        self.connection = btce_connection(key,sec)
        self.connection.getinfo()
        self.amount = amount
        self.buy_multi = 1 - spread
        self.sell_multi = 1 + spread
        
    def get_price(self):
        self.connection.getinfo()
    def trade(self):
        #calculate our price
        self.get_price()
        # should do divide by zero check here...
        try:
            temp_price = (self.connection.funds[self.c2]/self.percentage - self.connection.funds[self.c2])/self.connection.funds[self.c1]
        except:
            temp_price = 1000
        self.our_price = round(temp_price,5)
        #margins should be either adjustable, or more inteligently set.
        self.buy_price = round(temp_price * self.buy_multi,5)
        self.sell_price = round(temp_price * self.sell_multi,5)
        print('our price is ${}'.format(self.our_price))
        print("portfolio value {} {}".format(self.connection.funds[self.c2]+(self.our_price * self.connection.funds[self.c1]),self.c2))
        self.buy=self.connection.trade(self.market,'buy',self.buy_price,self.amount)
        if self.buy == 0:
            print('[ {} ] bought {} {} at {} {}'.format(time.strftime('%I:%M:%S %p'),self.amount,self.c1,self.buy_price,self.c2))
            return
        self.sell=self.connection.trade(self.market,'sell',self.sell_price,self.amount)
        #print("our orders are buy={}, sell={}".format(self.buy,self.sell))
        if self.sell == 0:
            print('[ {} ] sold {} {} at {} {}'.format(time.strftime('%I:%M:%S %p'),self.amount,self.c1,self.sell_price,self.c2))
            self.connection.cancel(self.buy)
            return
        
        while True:
            orders = self.connection.orders()
            if orders.keys().__contains__(self.buy.__str__()) == False:
                # our buy order was filled
                print('[ {} ] bought {} {} at {} {}'.format(time.strftime('%I:%M:%S %p'),self.amount,self.c1,self.buy_price,self.c2))
                self.connection.cancel(self.sell)
                return
            if orders.keys().__contains__(self.sell.__str__()) == False:
                # our sell order was filled
                print('[ {} ] sold {} {} at {} {}'.format(time.strftime('%I:%M:%S %p'),self.amount,self.c1,self.sell_price,self.c2))
                self.connection.cancel(self.buy)
                return
            #print("got {}, and all our orders were still there".format(orders))
            time.sleep(60)
        #make 2 trades
        #loop checking trades, and cancel one of them
        
if __name__ == "__main__":
    
    re = rebalance('xpm','btc',0.5,0.02,0.1)
    # Change this line to change how the bot works
    # the parameters in order are:
    # First currency
    # Second currency
    # value ratio (bot will attempt to keep the value of the balances at this ratio)
    # A multiplier... After your price is calculated, buy and sell order prices are made by multiplying your price by 1+multiplier and 1-multiplier
    # The amount to trade in each transaction.
    
    # !!! warning !!!
    # If the amount to trade is too high, or your available balance is too low,
    # this bot will get into a feedback loop and you will loose all your money.
    
    #markets available:
    # btc_usd btc_rur btc_eur ltc_btc ltc_rur ltc_eur nmc_btc nmc_usd nvc_btc
    # nvc_usd usd_rur eur_usd trc_btc ppc_btc ppc_usd ftc_btc xpm_btc
    
    #minimum trade on xpm_btc is 0.1 xpm
    #minimum trade on btc_usd is 0.01 btc
    #minimum trade on ltc_btc & ltc_usd is 0.1 ltc
    
    while True:
        re.trade()
