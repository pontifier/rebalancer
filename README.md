I built this trading bot in the hours leading up to the MtGox shutdown.
I was able to run it and see it working, but it only ran for a couple of hours before MtGox imploded.

Usage:
add your MtGox api key and secret to the file.
python rebalancer.py

This bot uses a technique called rebalancing to calculate trades to make on your behalf.

First your acount balance in USD and BTC are retrieved.
A price for BTC is calculated that would balance your account with the specified ratio.
2 trades for 0.01 BTC each are entered on either side of this value.
The trades are checked every 60 seconds to see if they have been filled.
If one trade is filled, the other trade is canceled.

Your current ratio is used to create trades, and the only feedback is whether trades happen or not.

!!!Caution, there may be some situations with low balance accounts in which the trades will oscilate and drain your account!!!

Api info and the trading core for MtGox were taken from https://bitbucket.org/nitrous/mtgox-api/overview
The other code is all mine, and you may use it as you like.

ps. Included is my actual output, from the last usefull run, as MtGox shut down.
