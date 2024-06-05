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

    def __init__(self, df, window):
        # inputs
        self.df = df
        self.window = window

        self.shape = (window, 8)

        # spaces
        self.action_space = Discrete(2)
        self.observation_space = Box(low=-np.inf, high=np.inf, shape=self.shape, dtype=np.float64)

        self.terminated = None
        self.truncated = None
        self._trade = None
        self._position = None
        self._current_tick = None
        self._last_trade_tick = None
        self._current_price = None
        self._last_trade_price = None
        self.max_profit = None
        self._total_profit = None
        self.prices = None
        self._start_tick = None
        self._end_tick = None
        self._total_reward = None
        self._position_history = None
        self.wait = None
        self.history = None

    ###################################################

    def reset(self, **kwargs):
        self.terminated = False
        self.truncated = False
        self._start_tick = self.window + 20
        self.prices, self.signals = self._process_data(self.df)
        self._end_tick = len(self.prices) - 1
        self._current_tick = self._start_tick
        self._last_trade_tick = self._current_tick - 1
        self._trade = False
        self._position = 0
        self._position_history = (self.window * [None]) + [self._position]

        self._total_reward = 0.
        self._total_profit = 1.
        self.max_profit = 1.

        info = {}

        self.wait = 0

        return self._get_observation(), info

    ###################################################
    
    def _process_data(self, df):
        prices = df.loc[:, 'Close'].to_numpy()
        prices = prices[self._start_tick - self.window:len(df)]

        # Calculate RSI and normalize
        RSI = (TA.RSI(df) / 50) - 1
        RSI = np.nan_to_num(RSI, nan=0.0).astype(np.float64)

        # Calculate MFI and normalize
        MFI = (TA.MFI(df) / 50) - 1
        MFI = np.nan_to_num(MFI, nan=0.0).astype(np.float64)

        # Calculate Williams %R and normalize
        WIL = (TA.WILLIAMS(df) / 50) + 1
        WIL = np.nan_to_num(WIL, nan=0.0).astype(np.float64)

        # Calculate Percent B and normalize
        PCB = TA.PERCENT_B(df) - 0.5
        PCB = np.nan_to_num(PCB, nan=0.0).astype(np.float64)

        # Calculate VZO and normalize
        VZO = TA.VZO(df) / 100
        VZO = np.nan_to_num(VZO, nan=0.0).astype(np.float64)

        # Calculate PCT and normalize
        PCT = np.where(df["Close"].pct_change() < 0, 1, -1)
        PCT = np.nan_to_num(PCT, nan=0.0).astype(np.float64)
        df = df.infer_objects(copy=False)

        # Calculate ZLEMA and normalize
        ZLEMA = np.where(TA.ZLEMA(df,14) < df['Close'], 1, -1)
        ZLEMA = np.nan_to_num(ZLEMA, nan=0.0).astype(np.float64)

        # Assign RSI to PCH (as given in your original code)
        PCH = RSI

        signals = np.column_stack((RSI, MFI, WIL, PCB, VZO, PCT, ZLEMA, PCH))
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
            
        match (action, self._position):
            case (1, 0):
                self._last_trade_price = self.prices[self._last_trade_tick]
                self._position, self._last_trade_tick, self.wait, self._trade = 1, self._current_tick, 0, True
            case (0, 1):
                self._last_trade_price = self.prices[self._last_trade_tick]
                self._position, self._last_trade_tick, self.wait, self._trade = 0, self._current_tick, 0, True
            case _:
                self.wait += 1
                self._trade = False
        self._current_price = self.prices[self._current_tick]

        step_reward = self._calculate_reward()
        self._total_reward = step_reward

        self._update_profit()

        self._position_history.append(self._position)
        info = dict(
            total_reward = self._total_reward,
            total_profit = self._total_profit,
            position = self._position
        )
        self._update_history(info)

        self.signals[self._current_tick:][-1] = ((self.prices[self._current_tick]/self._last_trade_price)-1)*100 if self._position == 1 else 0
        
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
                self._total_profit *= self._current_price / self._last_trade_price

    ###################################################

    def render(self):
        pass
