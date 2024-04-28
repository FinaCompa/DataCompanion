from typing import Any
from enum import Enum
from gymnasium import Env
from gymnasium.spaces import Discrete, Box
import numpy as np
from finta import TA
import pandas as pd
import random



##############################################################################################################################


class Trading(Env):

    def __init__(self, dataframe, window, max_drawdown):
        # from inputs
        self.df = dataframe
        self.window = window
        self._start_tick = window + 48
        self._end_tick = len(dataframe) - 1
        self.prices, self.signals = self._process_data(dataframe)
        self._end_tick = len(self.prices)-1
        self.shape = (window, self.signals.shape[1])
        self.max_drawdown = max_drawdown

        # spaces
        self.action_space = Discrete(2)
        self.observation_space = Box(low=-np.inf, high=np.inf, shape=self.shape, dtype=np.float64)

        # internal
        self.terminated = None
        self.truncated = None
        self._current_tick = None
        self._current_price = None
        self._last_trade_tick = None
        self._last_trade_price = None
        self._position = None
        self._total_reward = None
        self._total_profit = None
        self._max_profit = None
        self.history = None
        self._trade = None
        self._position_history = None
        self.trade_fee_bid_percent = None # unit
        self.trade_fee_ask_percent = None  # unit
        self.wait = None

    ###################################################

    def reset(self, **kwargs):
        self.terminated = False
        self.truncated = False
        self._current_tick = self._start_tick
        self._last_trade_tick = self._current_tick - 1

        self._trade = False
        self._position = 0
        self._position_history = (self.window * [None]) + [self._position]
        self.history = {}
        self.trade_fee_bid_percent = 0.00  # unit
        self.trade_fee_ask_percent = 0.00  # unit

        self.wait = 0

        self._total_reward = 0.
        self._total_profit = 1.
        self._max_profit = 1.

        info = {}
        
        return self._get_observation(), info

    ###################################################
    
    def _process_data(self,df):
        prices = df.loc[:, 'Close'].to_numpy()

        #prices[self._start_tick - self.window]  # validate index (TODO: Improve validation)
        prices = prices[self._start_tick-self.window : self._end_tick]

        # Indicators
        RSI = (TA.RSI(df) / 50) - 1
        MFI = (TA.MFI(df) / 50) - 1
        WIL = (TA.WILLIAMS(df) / 50) + 1
        PCB = TA.PERCENT_B(df) - 0.5
        VZO = TA.VZO(df) / 100

        signals = np.column_stack((RSI,MFI,WIL,PCB,VZO))

        # Replace NaN values with 0
        signals = np.nan_to_num(signals, nan=0.0)

        return prices, signals

    ###################################################

    def _get_observation(self):
        return self.signals[(self._current_tick-self.window+1):self._current_tick+1]

    ###################################################

    def step(self, action):
        self._current_tick += 1

        if self._current_tick >= self._end_tick:
            self.terminated = True
        
        self._last_trade_price = self.prices[self._last_trade_tick]
        #print(f'action : {action}\t position : {self._position}')
        match (action, self._position):
            case (1, 0):
                self._position, self._last_trade_tick, self.wait, self._trade = 1, self._current_tick, 0, True
            case (0, 1):
                self._position, self._last_trade_tick, self.wait, self._trade = 0, self._current_tick, 0, True
            case _:
                self.wait += 1
                self._trade = False
        self._current_price = self.prices[self._current_tick]

        step_reward = self._calculate_reward()
        self._total_reward += step_reward

        self._update_profit()

        self._position_history.append(self._position)
        info = dict(
            total_reward = self._total_reward,
            total_profit = self._total_profit,
            position = self._position
        )
        self._update_history(info)

        self.signals[self._current_tick:][-1] = ((self.prices[self._last_trade_tick]/self.prices[self._current_tick])-1)*100 if self._position == 1 else 0

        return self._get_observation(), step_reward, self.terminated, self.truncated, info

    ###################################################

    def _update_history(self, info):
        if not self.history:
            self.history = {key: [] for key in info.keys()}

        for key, value in info.items():
            self.history[key].append(value)
    
    ###################################################

    def _calculate_reward(self):
        step_reward = 0.0

        return step_reward

    ###################################################

    def _update_profit(self):

        if self._trade or self.terminated:

            if self._position == 0:
                shares = (self._total_profit * (1 - self.trade_fee_ask_percent)) / self._last_trade_price
                self._total_profit = (shares * (1 - self.trade_fee_bid_percent)) * self._current_price
                #self._total_profit *= current_price / last_trade_price
                #print(f'{self._total_profit}')
                #print(f'{current_price}\t{last_trade_price}')

    ###################################################

    def render(self):
        pass