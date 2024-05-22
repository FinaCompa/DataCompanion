##### Dependencies
# Import the required libraries
import os
import ccxt
import pandas as pd
import json
import time
import datetime
import threading
from prophet import Prophet
from github import Github
import gymnasium as gym
import trading_init
from stable_baselines3 import PPO


######################### Function #########################

##### Scrap datas
def get_crypto_data(exchange, timeframe, symbol, n):

    # Load the historical candlestick data for the specified symbol and timeframe
    bars = exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=n+1)

    # Convert the list of bars to a Pandas DataFrame
    df = pd.DataFrame(bars[:n], columns=["Time", "Open", "High", "Low", "Close", "Volume"])

    df['Time'] = pd.to_datetime(df["Time"]/1000, unit='s')

    return df


##### df process
def df_process(df):
    df['ds'] = df['Time']
    df['y'] = df['Close']
    return df


##### Take decision
def decisionBasic(df, timeframe, IA):
    if timeframe == '1m':
        timeframe = 'T'
    else:
        timeframe = timeframe[-1].upper()
    
    m = Prophet()
    m.fit(df=df.tail(60))
    future = m.make_future_dataframe(periods=1, freq=timeframe)
    prediction = m.predict(future)

    iter_m1 = prediction['yhat'][len(prediction)-1:].values[0]
    iter_m2 = prediction['yhat'][len(prediction)-2:].values[0]
    last_pr = df['y'][len(df)-1:].values[0]

    if last_pr < iter_m2 and iter_m1 > iter_m2:
        IA["Basic"] = 'Up Moves'
    elif last_pr > iter_m2 and iter_m1 > iter_m2:
        IA["Basic"] = 'Down Moves'
    else:
        IA["Basic"] = 'Chill'
        
    return IA


def decisionAdvanced(df, IA):
    
    env = gym.make(
        id='Production',
        df=df,
        window=31
        )
    
    model = PPO.load('trade_PPO', env=env)
    obs, info = env.reset()
    done = False
    terminated = False
    truncated = False
    score = 0
    while not done:
        action = model.predict(obs, deterministic=False)
        obs, reward, terminated, truncated, info = env.step(action[0])
        score += reward
        done = terminated or truncated
    
    if info['position'] == 0:
        IA['Advanced'] = 'Down Moves'
    else:
        IA['Advanced'] = 'Up Moves'
        
    return IA



def process(data):
    #pred_date = {}
    #pred_date["prediction_date"] = datetime.datetime.now().strftime("%d:%m:%Y")
    final_list = []
    for coin in data:
        final_list.append(data[coin])
    #final_list.append(pred_date)
    return final_list

######################### G variables #########################
threads = []
exchange = ccxt.okx()
# Ouvrir le fichier JSON en mode lecture ('r')
with open('list_cryptos.json', 'r') as f:
    # Charger les données JSON depuis le fichier
    Final_Dict = json.load(f)

with open('cryptos.json', 'r') as f:
    # Charger les données JSON depuis le fichier
    Old_Dict = json.load(f)

timeframe = '1d'
n_data = 300

mut = threading.Lock()  # Création d'un nouveau verrou
mut_get = threading.Lock()
mut_load_mod = threading.Lock()


######################### Threaded Fun #########################
def add_result(exchange, coin, timeframe, n_data):
    global Final_Dict
    global Old_Dict
    
    mut_get.acquire()
    try:
        datas = get_crypto_data(exchange=exchange, timeframe=timeframe, symbol=coin, n=n_data)
    finally:
        mut_get.release()

    open = datas['Open'].iloc[-1]
    close = datas['Close'].iloc[-1]

    exist = False
    for i in range(len(Old_Dict)):
        if Old_Dict[i]["paire"] == coin:
            exist = True
            break

    liste_Basic = Old_Dict[i]["histo_Basic"]
    liste_Advanced = Old_Dict[i]["histo_Advanced"]
    
    if exist:
        if (close > open and Old_Dict[i]["IA"]["Basic"] == "Up Moves") or (close < open and Old_Dict[i]["IA"]["Basic"] == "Down Moves"):
            liste_Basic.append(100)
        elif (close < open and Old_Dict[i]["IA"]["Basic"] == "Up Moves") or (close > open and Old_Dict[i]["IA"]["Basic"] == "Down Moves"):
            liste_Basic.append(0)
        liste_Basic = liste_Basic[-10:]
        
        if (close > open and Old_Dict[i]["IA"]["Advanced"] == "Up Moves") or (close < open and Old_Dict[i]["IA"]["Advanced"] == "Down Moves"):
            liste_Advanced.append(100)
        elif (close < open and Old_Dict[i]["IA"]["Advanced"] == "Up Moves") or (close > open and Old_Dict[i]["IA"]["Advanced"] == "Down Moves"):
            liste_Advanced.append(0)
        liste_Advanced = liste_Advanced[-10:]
    
    # IA
    IA = {"Basic":"",
         "Advanced":""}
    datas = df_process(datas)
    datas['Time'] = datas['ds'].dt.strftime("%Y-%m-%d")
    # Basic part
    IA = decisionBasic(datas, timeframe, IA)
    # Advanced part
    del datas['ds']
    del datas['y']
    IA = decisionAdvanced(datas, IA)
    
    mut.acquire()
    try:
        Final_Dict[coin.split("/")[0]]["IA"] = IA
        Final_Dict[coin.split("/")[0]]["ohlcv_histo"] = datas["Close"].tail(31).tolist()
        Final_Dict[coin.split("/")[0]]["time_histo"] = datas["Time"].tail(31).tolist()
        Final_Dict[coin.split("/")[0]]["histo_Advanced"] = liste_Advanced
        Final_Dict[coin.split("/")[0]]["histo_Basic"] = liste_Basic
    finally:
        mut.release()


######################### Main #########################

for coin in Final_Dict:
    thread = threading.Thread(target=add_result, args=(exchange, coin+"/USDT", timeframe, n_data))
    threads.append(thread)

for thread in threads:
    thread.start()
    
for thread in threads:
    thread.join()

try:
    TOKEN = str(os.environ["TOKEN"])
except KeyError:
    exit(1)
g = Github(TOKEN)

REPO = g.get_repo("FinaCompa/DataCompanion")
CONTENT = REPO.get_contents("cryptos.json")
REPO.update_file(CONTENT.name, "update", json.dumps(process(Final_Dict), indent=4, ensure_ascii=False), CONTENT.sha, branch="main")












