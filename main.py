##### Dependencies
# Import the required libraries
import os
import ccxt
import pandas as pd
import threading
import json
import time
import datetime
from prophet import Prophet
from github import Github


##### Function

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
        return 'Achat'
    elif iter_m1 < iter_m2 and last_pr > iter_m2:
        return 'Vente'
    else:
        return 'Neutral'


##### G variables
# Chargement des données depuis le fichier mon_fichier.txt
with open("list_cryptos.txt", "r") as file:
    lines = file.readlines()
# Suppression des sauts de ligne
lines = [line.strip() for line in lines]
# Création de la liste à partir des éléments de la liste des lignes
cryptos_list = [str(x) for x in lines]

#cryptos_list = [
#    "BTC/USDT",
#    "ETH/USDT"
#]

threads = []
exchange = ccxt.okx()
Final_Dict = {}
Final_Dict["prediction_date"] = datetime.datetime.now().strftime("%d:%m:%Y")
timeframe = '1d'
n_data = 60

mut = threading.Lock()  # Création d'un nouveau verrou



##### G code
def add_result(exchange, coin, timeframe, n_data):
    global Final_Dict

    datas = get_crypto_data(exchange=exchange, timeframe=timeframe, symbol=coin, n=n_data)
    datas = df_process(datas)
    result = decision(datas,timeframe)

    mut.acquire()
    try:
        Final_Dict[coin] = result
    finally:
        mut.release()




for coin in cryptos_list:
    thread = threading.Thread(target=add_result, args=(exchange, coin, timeframe, n_data))
    threads.append(thread)

##### Main

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
CONTENT = REPO.get_contents("datas.json")
REPO.update_file(CONTENT.name, "update", json.dumps(Final_Dict, indent=4), CONTENT.sha, branch="main")












