I built A trading bot in the hours leading up to the MtGox shutdown.
I was able to run it and see it working, but it only ran for a couple of hours before MtGox imploded.

I have now re-built it to work with BTC-E

Usage:
add your BTC-E api key and secret to btce.py
edit the rebalancer call in the main function to use your desired currency pair, ratio, spread multiplier, and trade amount.
python3 btce.py

This bot uses a technique called rebalancing to calculate trades to make on your behalf.

First your acount balance in XPM and BTC are retrieved.
A price for XPM is calculated that would balance your account with the specified ratio.
2 trades for 0.1 XPM each are entered on either side of this value.
The trades are checked every 60 seconds to see if they have been filled.
If one trade is filled, the other trade is canceled.

Your current ratio is used to create trades, and the only feedback is whether trades happen or not.

!!!Caution, there may be some situations with low balance accounts in which the trades will oscilate and drain your account!!!
