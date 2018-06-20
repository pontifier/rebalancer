def optimal_price(btc,usd,size=.01,ratio=.5):
    price = round(((usd/ratio) - usd)/ btc,2)
    price_h= round((usd * (1-ratio))/((ratio*btc) -size),2)
    price_l= round((usd * (1-ratio))/((ratio*btc) +size),2)
    print("price is ${}. buy at ${}, sell at ${}".format(price,price_l,price_h))

if __name__ == "__main__":
    import sys
    optimal_price(float(sys.argv[1]),float(sys.argv[2]),float(sys.argv[3]))