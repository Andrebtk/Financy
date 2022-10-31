import requests
import urllib.parse
import datetime 
import time
from cs50 import SQL

db = SQL("sqlite:///finance.db")


def main(symbol):
    
    #api_key = os.environ.get("API_KEY")
    api_key = "pk_6c70509ce93d4b36b2d416f60ca29a06"
    url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}"
    response = requests.get(url)
    response.raise_for_status()
    '''
    except requests.RequestException:
        print("[error] -> requests.RequestException")
    '''

    # Parse response
    try:
        quote = response.json()
        data = {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }


    except (KeyError, TypeError, ValueError):
        print("[Error] -> KeyError, TypeError, ValueError")

    print("[time] -> " + str(datetime.datetime.now()) + " | [respond] -> " + str(data))
    return str(datetime.datetime.now()), str(data['price'])

while True:
    stock_symbol = ["nflx", "googl", "tsla", "FB", "AMZN"]
    
    print("/////////////////////////////////////////////")
    for x in stock_symbol:
        date, data = main(x)
        db.execute("insert into stock_history (date, company, stock) values (?,?,?)", date, x, data)
    time.sleep(3600)
