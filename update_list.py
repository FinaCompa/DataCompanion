import ccxt

# Initialisation de l'échange Binance
exchange = ccxt.binance()

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

# Ouvrir le fichier pour écriture
with open("list_cryptos.txt", "w") as file:
    # Écrire chaque élément de la liste sur une ligne séparée par un saut de ligne
    for item in crypto_monnaies_communes:
        file.write(f"{item}\n")
