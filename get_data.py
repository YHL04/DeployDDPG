import alpaca_trade_api as tradeapi
import keys
import pandas as pd


api_key = config.API_KEY
api_secret = config.SECRET_KEY
base_url = config.BASE_URL
ws_url = config.WS_URL

api = tradeapi.REST(api_key,
                    api_secret,
                    base_url=base_url,
                    api_version='v2')


def get_minute_data(symbols, limit):
    NY = 'America/New_York'
    until = pd.Timestamp.now().isoformat()

    if limit <= 1000:
        return api.get_barset(symbols, 'minute', until=until, limit=limit).df
    else:
        data = pd.DataFrame()

        while limit > 0:
            if limit >= 1000:
                temp_limit = 1000
            else:
                temp_limit = limit
            temp = api.get_barset(symbols, 'minute', until=until, limit=temp_limit).df
            try:
                until = temp.first_valid_index().isoformat()
            except:
                print(temp)
            data = pd.concat([temp, data])
            print(limit)
            limit -= 1000

        return data


stocks = ["NVDA", "AAPL", "QCOM", "TSMC", "INTC",
          "AMZN", "GOOGL", "GOOG", "AMD", "TSLA",
          "ASML", "AMAT", "MSFT", "LOW", "KO",
          "JPM"]


data = get_minute_data(stocks, 600000)
data.to_pickle("data/data.pkl")
