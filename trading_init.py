from gymnasium.envs.registration import register
from copy import deepcopy
import pandas as pd

df = pd.read_csv('BTC_USDT.csv')

register(
    id='Production',
    entry_point='env_prod:Trading',
    kwargs={
        'dataframe': deepcopy(df),
        'window': 31,
        'max_drawdown': 0.85 
    }
)
