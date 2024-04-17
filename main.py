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
    df_prophet = pd.DataFrame(columns=["ds","y"])
    df_prophet['ds'] = df['Time']
    df_prophet['y'] = df['Close']
    return df_prophet


##### Take decision
def decision(df, timeframe):
    if timeframe == '1m':
        timeframe = 'T'
    else:
        timeframe = timeframe[-1].upper()
    
    m = Prophet()
    m.fit(df=df)
    future = m.make_future_dataframe(periods=1, freq=timeframe)
    prediction = m.predict(future)

    iter_m1 = prediction['yhat'][len(prediction)-1:].values[0]
    iter_m2 = prediction['yhat'][len(prediction)-2:].values[0]
    last_pr = df['y'][len(df)-1:].values[0]

    if iter_m1 > iter_m2 and last_pr < iter_m2:
        return 'Up Moves'
    elif iter_m1 < iter_m2 and last_pr > iter_m2:
        return 'Down Moves'
    else:
        return 'Chill'

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
timeframe = '1d'
n_data = 60

mut = threading.Lock()  # Création d'un nouveau verrou
mut_get = threading.Lock()



######################### Threaded Fun #########################
def add_result(exchange, coin, timeframe, n_data):
    global Final_Dict

    mut_get.acquire()
    try:
        datas = get_crypto_data(exchange=exchange, timeframe=timeframe, symbol=coin, n=n_data)
    finally:
        mut_get.release()

    datas = get_crypto_data(exchange=exchange, timeframe=timeframe, symbol=coin, n=n_data)
    datas = df_process(datas)
    result = decision(datas,timeframe)

    datas['Time'] = datas['ds'].dt.day
    
    mut.acquire()
    try:
        Final_Dict[coin.split("/")[0]]["IA"] = result
        Final_Dict[coin.split("/")[0]]["ohlcv_histo"] = datas["y"].tail(31).tolist()
        Final_Dict[coin.split("/")[0]]["time_histo"] = datas["Time"].tail(31).tolist()
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












