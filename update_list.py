import ccxt
import os
from github import Github
import json
import requests

# Initialisation de l'échange Binance
exchange = ccxt.okx()

# Chargement des marchés (paires de trading)
markets = exchange.load_markets()

# Filtrage des paires de trading de la forme CRYPTO/USDT (excluant CRYPTO/USDT:USDT)
crypto_usdt_symbols = [symbol for symbol in markets.keys() if '/USDT' in symbol and ':USDT' not in symbol]

with open('list_description.json', 'r') as f:
    # Charger les données JSON depuis le fichier
    descriptions = json.load(f)

crypto_monnaies_communes = [crypto for crypto in descriptions if crypto in crypto_usdt_symbols]
free_cryptos = ["BTC","ETH","SOL","XRP","ADA","AVAX"]

base_url = "https://api.coinpaprika.com/v1/coins"
list_json = requests.get(url=base_url).json()
new_dict = {}

for coin in list_json:
    if coin["symbol"] not in new_dict and coin["symbol"]+"/USDT" in crypto_monnaies_communes :
        new_url = base_url+"/"+coin["id"]
        response = requests.get(new_url).json()
        premium = False if coin["symbol"] in free_cryptos else True

        new_dict[coin["symbol"]] =  {
                                        "name":coin["name"],
                                        "description":descriptions[coin["symbol"]+"/USDT"],
                                        "symbol":coin["symbol"],
                                        "paire":coin["symbol"]+"/USDT",
                                        "logo":response["logo"],
                                        "ohlcv_histo":"",
                                        "time_histo":"",
                                        "ohlcv_today":new_url+"/ohlcv/today",
                                        "premium":premium,
                                        "IA_Adv":"Null",
                                        "IA_Bsc":"Null"
                                    }

try:
    TOKEN = str(os.environ["TOKEN"])
except KeyError:
    exit(1)
g = Github(TOKEN)
    
REPO = g.get_repo("FinaCompa/DataCompanion")
CONTENT = REPO.get_contents("list_cryptos.json")
REPO.update_file(CONTENT.name, "update", json.dumps(new_dict, indent=4, ensure_ascii=False), CONTENT.sha, branch="main")

