import matplotlib.pyplot as plt
import numpy as np


class Render():
    def __init__(self, num_stocks):
        self.i = 0
        self.num_stocks = num_stocks
        self.avg_price = []
        self.equity = []

    def reset(self):
        self.avg_price = []
        self.equity = []

    def step(self, state):
        self.avg_price.append(state[1:1+self.num_stocks])
        self.equity.append(state[0] +
                           sum(np.array(state[1:1+self.num_stocks])*np.array(state[1+self.num_stocks:])))

    def render(self):
        avg_price = np.array(self.avg_price)
        scale = self.equity[0] / avg_price[0]
        avg_price *= scale

        plt.clf()

        # plot all price trajectories
        plt.plot(avg_price, c="deepskyblue")

        # plot mean trajectory
        avg_price = np.mean(avg_price, axis=1)
        plt.plot(avg_price, c="blue")

        # plot equity trajectory
        plt.plot(self.equity, c="red")
        plt.pause(0.00001)
