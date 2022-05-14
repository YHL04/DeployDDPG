import alpaca_trade_api as tradeapi
import datetime
import pandas as pd
import threading
import numpy as np
import yfinance as yf
import time
from collections import deque

from model import TradeModel
from render import Render
from utils import read_tickers
import keys


class TradeAgent(object):
    def __init__(self, render=True):
        self.alpaca = tradeapi.REST(keys.API_KEY,
                                    keys.SECRET_KEY,
                                    keys.BASE_URL,
                                    "v2")

        self.tickers = read_tickers("model/stocks.txt")

        self.cash = 10000
        self.num_stocks = [0 for _ in self.tickers]

        self.maxlen = 2000
        self.state_buffer = deque(maxlen=self.maxlen)
        self.bar_buffer = pd.DataFrame()
        self.model = TradeModel()
        self.state = deque(maxlen=31*2000)
        self.current_prices = deque(maxlen=15)

        if render:
            self.render = Render(num_stocks=15)

    def run(self):
        # First, cancel any existing orders so they don't impact our buying power.
        orders = self.alpaca.list_orders(status="open")
        for order in orders:
            self.alpaca.cancel_order(order.id)

        # Wait for market to open.
        print("Waiting for market to open...")
        tAMO = threading.Thread(target=self.await_market_open)
        tAMO.start()
        tAMO.join()
        print("Market opened.")

        while True:
            clock = self.alpaca.get_clock()
            closing_time = clock.next_close.replace(tzinfo=datetime.timezone.utc).timestamp()
            current_time = clock.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
            self.time_to_close = closing_time - current_time

            if (self.time_to_close < (60 * 15)):
                # Run script again after market close for next trading day.
                print("Sleeping until market close (15 minutes).")
                time.sleep(60 * 15)

            elif not clock.is_open:
                tAMO = threading.Thread(target=self.await_market_open)
                tAMO.start()
                tAMO.join()
                print("Market opened again.")

            else:
                # Market is open, run step
                step = threading.Thread(target=self.step)
                step.start()
                step.join()
                self.render.step(self.state[-31:])
                self.render.render()
                time.sleep(60)


    def await_market_open(self):
        is_open = self.alpaca.get_clock().is_open
        while (not is_open):
            clock = self.alpaca.get_clock()
            opening_time = clock.next_open.replace(tzinfo=datetime.timezone.utc).timestamp()
            current_time = clock.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
            time_to_open = int((opening_time - current_time) / 60)
            print(str(time_to_open) + " minutes til market open.")
            time.sleep(60)
            is_open = self.alpaca.get_clock().is_open


    """can't use REST api without subscription, use yfinance to retrieve real time data"""
    def get_live_prices(self):
        data = yf.download(tickers=self.tickers, period="5m", interval="1m", progress=False).dropna()
        return data

    """can't use REST api without subscription, use yfinance to retrieve real time data"""
    def get_day_prices(self):
        data = yf.download(tickers=self.tickers, period="7d", interval="1m", progress=False).dropna()
        return data


    def submit_buy_order(self, index, action):
        price = self.current_prices[index]
        available_amount = self.cash // price
        qty = min(available_amount, action)

        self.cash -= self.current_prices[index]*qty
        self.num_stocks[index] += qty

        # submit order through api
        if qty > 0:
            ticker = self.tickers[index]
            price = str(price)

            self.alpaca.submit_order(symbol=ticker,
                                     qty=str(qty),
                                     side="buy",
                                     type="limit",
                                     time_in_force="day",
                                     limit_price=price)

        return qty

    def submit_sell_order(self, index, action):
        if self.num_stocks[index] > 0:
            price = self.current_prices[index]
            qty = min(abs(action), self.num_stocks[index])

            self.cash += price * qty
            self.num_stocks[index] -= qty

            # submit order through api
            ticker = self.tickers[index]
            price = str(price)

            self.alpaca.submit_order(symbol=ticker,
                                     qty=str(qty),
                                     side="sell",
                                     type="limit",
                                     time_in_force="day",
                                     limit_price=price)

            return qty

        return 0


    def submit_orders(self, actions):
        argsort_actions = np.argsort(actions)
        sell_index = argsort_actions[:np.where(actions < 0)[0].shape[0]]
        buy_index = argsort_actions[::-1][:np.where(actions > 0)[0].shape[0]]

        real_orders = [0 for _ in self.tickers]

        for index in sell_index:
            qty = self.submit_sell_order(index, actions[index])
            real_orders[index] = -qty

        for index in buy_index:
            qty = self.submit_buy_order(index, actions[index])
            real_orders[index] = qty

        return real_orders

    def clear_orders(self):
        # Clear existing orders again.
        orders = self.alpaca.list_orders(status="open")
        for order in orders:
            self.alpaca.cancel_order(order.id)

    def step(self):
        self.clear_orders()
        if len(self.bar_buffer) < self.maxlen:
            bars = self.get_day_prices()
        else:
            bars = self.get_live_prices()

        self.bar_buffer = pd.concat([self.bar_buffer, bars])
        self.bar_buffer = self.bar_buffer.iloc[-self.maxlen:]
        self.current_prices += self.bar_buffer["Adj Close"].iloc[-1].tolist()

        #if len(self.state) < 31*2000:
        self.state = []
        for index, row in self.bar_buffer["Adj Close"].iterrows():
            self.state += [self.cash] + row.tolist() + self.num_stocks
        # else:
        #     self.state += [self.cash] + list(self.current_prices) + self.num_stocks

        actions = self.model.get_action(self.state)
        orders = self.submit_orders(actions)

        # for logging purposes
        dt_string = datetime.datetime.now()
        print("{} \t {}".format(dt_string, orders))


if __name__ == "__main__":
    main = TradeAgent()
    main.run()
