from typing import Any
from enum import Enum
from gymnasium import Env
from gymnasium.spaces import Discrete, Box
import numpy as np
from finta import TA
import pandas as pd
import random

# Activer l'option future pour éviter le warning
#pd.set_option('future.no_silent_downcasting', True)



##############################################################################################################################


class Trading(Env):

    def __init__(self, df, window):
        # inputs
        self.df = df
        self.window = window

        self.shape = (window, 18)

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
        #print(self.df)
        self.terminated = False
        self.truncated = False
        self._start_tick = self.window + 20
        self.prices, self.signals = self._process_data(self.df)
        self._last_trade_price = self.prices[self._start_tick]
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


        # Calculate PCT and normalize
        PCT = np.where(df["Close"].pct_change() > 0, 1, -1)
        PCT = np.nan_to_num(PCT, nan=0.0).astype(np.float64)
        df = df.infer_objects(copy=False)


        # Calculate BASPN and normalize
        BASPN = np.where(TA.BASPN(df)["Buy."] > TA.BASPN(df)["Sell."], 1, 0)
        BASPN = np.nan_to_num(BASPN, nan=0.0).astype(np.float64)


        chand = TA.CHANDELIER(df)
        # Calculate CHANDELIER and normalize
        CHAND1 = np.where(np.where(chand["Short."] > chand["Long."], 1, 0), 1, 0)
        CHAND1 = np.nan_to_num(CHAND1, nan=0.0).astype(np.float64)

        CHAND2 = np.where(np.where(chand["Short."] > df.Close, 1, 0), 1, 0)
        CHAND2 = np.nan_to_num(CHAND2, nan=0.0).astype(np.float64)

        CHAND3 = np.where(np.where(chand["Long."] > df.Close, 1, 0), 1, 0)
        CHAND3 = np.nan_to_num(CHAND3, nan=0.0).astype(np.float64)


        # Calculate VORTEX and normalize
        VORTEX = np.clip((TA.VORTEX(df)["VIp"]+TA.VORTEX(df)["VIm"]-2)*5, -1, 1)
        VORTEX = np.nan_to_num(VORTEX, nan=0.0).astype(np.float64)


        # Calculate VW_MACD and normalize
        MACD = np.where(TA.VW_MACD(df)["MACD"] > TA.VW_MACD(df)["SIGNAL"], 1, 0)
        MACD = np.nan_to_num(MACD, nan=0.0).astype(np.float64)


        # Calculate HMA and normalize
        HMA = np.where(df.Close > TA.HMA(df), 1, 0)
        HMA = np.nan_to_num(HMA, nan=0.0).astype(np.float64)


        # Calculate SSMA and normalize
        SSMA = np.where(df.Close > TA.SSMA(df), 1, 0)
        SSMA = np.nan_to_num(SSMA, nan=0.0).astype(np.float64)


        # Calculate SSHMA and normalize
        SSHMA = np.where(TA.HMA(df) > TA.SSMA(df), 1, 0)
        SSHMA = np.nan_to_num(SSHMA, nan=0.0).astype(np.float64)


        # Calculate BOP and normalize
        BOP = TA.BOP(df)
        BOP = np.nan_to_num(BOP, nan=0.0).astype(np.float64)


        # Calculate RSI and normalize
        RSI = TA.RSI(df) / 100
        RSI = np.nan_to_num(RSI, nan=0.0).astype(np.float64)


        # Calculate ER and normalize
        ER = TA.ER(df)
        ER = np.nan_to_num(ER, nan=0.0).astype(np.float64)


        # Calculate IFT_RSI and normalize
        IFT_RSI = TA.IFT_RSI(df)
        IFT_RSI = np.nan_to_num(IFT_RSI, nan=0.0).astype(np.float64)


        # Calculate MFI and normalize
        MFI = TA.MFI(df) / 100
        MFI = np.nan_to_num(MFI, nan=0.0).astype(np.float64)


        # Calculate SQZMI and normalize
        SQZMI = TA.SQZMI(df)
        SQZMI = np.nan_to_num(SQZMI, nan=0.0).astype(np.float64)


        # Calculate STOCH and normalize
        STOCH = TA.STOCH(df) / 100
        STOCH = np.nan_to_num(STOCH, nan=0.0).astype(np.float64)


        # Assign BASPN to PCH (as given in your original code)
        PCH = PCT

        signals = np.column_stack((PCT,BASPN,CHAND1,CHAND2,CHAND3,VORTEX,MACD,HMA,SSMA,SSHMA,BOP,RSI,ER,IFT_RSI,MFI,SQZMI,STOCH,PCH))
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
