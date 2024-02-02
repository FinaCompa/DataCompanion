import ccxt

# Initialisation de l'échange Binance
exchange = ccxt.okx()

# Chargement des marchés (paires de trading)
markets = exchange.load_markets()

# Filtrage des paires de trading de la forme CRYPTO/USDT (excluant CRYPTO/USDT:USDT)
crypto_usdt_symbols = [symbol for symbol in markets.keys() if '/USDT' in symbol and ':USDT' not in symbol]

the_list = [    "BTC/USDT",
                "ETH/USDT",
                "BNB/USDT",
                "SOL/USDT",
                "XRP/USDT",
                "ADA/USDT",
                "AVAX/USDT",
                "DOGE/USDT",
                "TRX/USDT",
                "DOT/USDT",
                "LINK/USDT",
                "MATIC/USDT",
                "SHIB/USDT",
                "UNI/USDT",
                "ATOM/USDT",
                "XMR/USDT",
                "GRT/USDT"]

crypto_monnaies_communes = [crypto for crypto in the_list if crypto in crypto_usdt_symbols]

try:
    TOKEN = str(os.environ["TOKEN"])
except KeyError:
    exit(1)
g = Github(TOKEN)
    
REPO = g.get_repo("FinaCompa/DataCompanion")
CONTENT = REPO.get_contents("datas.json")
REPO.update_file(CONTENT.name, "update", "\n".join(crypto_monnaies_communes), CONTENT.sha, branch="main")
