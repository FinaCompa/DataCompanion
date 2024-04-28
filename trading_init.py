from gymnasium.envs.registration import register
from copy import deepcopy
import pandas as pd

df = pd.read_csv('datas/BTC_USDT.csv')

register(
    id='Full-Trade',
    entry_point='env_perso:Trading',
    kwargs={
        'dataframe': deepcopy(df),
        'window': 31,
        'scenario': 'test',
        'len_train_ep': 365,
        'max_drawdown': 0.85 
    }
)

register(
    id='Production',
    entry_point='env_prod:Trading',
    kwargs={
        'dataframe': deepcopy(df),
        'window': 31,
        'scenario': 'test',
        'len_train_ep': 365,
        'max_drawdown': 0.85 
    }
)