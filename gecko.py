import pandas as pd
import requests
from datetime import datetime
import time
import numpy as np

# CONFIG
START = "2018-01-01"
END   = "2025-04-30"
OUTPUT = "crypto_energy_full.xlsx"
DT_FMT = "%Y-%m-%d"

# UTILS
def fetch_coinpaprika(ticker):
    """Fetch daily price, mcap, volume from CoinPaprika."""
    url = (
        f"https://api.coinpaprika.com/v1/tickers/{ticker}/historical"
        f"?start={START}&end={END}&interval=24h"
    )
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['time_open']).dt.floor('D')
    df = df.set_index('date')[['price','market_cap','volume']]
    df.columns = [f"{ticker}_{c}" for c in df.columns]
    return df

def fetch_blockchain(series):
    url = f"https://api.blockchain.info/charts/{series}?timespan=all&format=json&sampled=false"
    data = requests.get(url).json()['values']
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['x'], unit='s').dt.floor('D')
    return df.set_index('date')['y'].rename(series)

def fetch_fred(series):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
    df = pd.read_csv(url, parse_dates=['DATE'])
    df = df.set_index('DATE')[series].rename(series)
    df.index = df.index.floor('D')
    return df

# 1. Crypto market data (CoinPaprika)
print("Fetching BTC from CoinPaprika…")
df_btc = fetch_coinpaprika("btc-bitcoin")
print("Fetching ETH from CoinPaprika…")
df_eth = fetch_coinpaprika("eth-ethereum")

# 2. Compute log returns
for coin in ['btc-bitcoin','eth-ethereum']:
    df = df_btc if 'btc' in coin else df_eth
    df[f"{coin}_return"] = np.log(df[f"{coin}_price"] / df[f"{coin}_price"].shift(1))

# 3. Bitcoin energy from Digiconomist (local file)
print("Loading Digiconomist energy…")
df_eng = (pd.read_csv("btc_energy.csv", parse_dates=["DateTime"])
            .rename(columns={"DateTime":"date","Estimated TWh per Year":"TWh_year"}))
df_eng['date'] = df_eng['date'].dt.floor('D')
df_eng['energy_twh_day'] = df_eng['TWh_year'] / 365
df_eng = df_eng.set_index('date')[['energy_twh_day']]

# 4. On-chain metrics
print("Fetching hash rate & tx count…")
df_hash = fetch_blockchain("hash-rate")
df_tx   = fetch_blockchain("n-transactions")

# 5. Macro controls
print("Fetching SP500, VIX, DXY, GOLD…")
df_spx  = fetch_fred("SP500")
df_vix  = fetch_fred("VIXCLS")
df_dxy  = fetch_fred("DTWEXM")
df_gold = fetch_fred("GOLDAMGBD228NLBM")

# 6. Global crypto-market cap (CoinPaprika)
print("Fetching total market cap…")
df_tot = fetch_coinpaprika("global-coinmarketcap")  # ticker exists on Paprika

# 7. Electricity prices (you still need to download 1 CSV)
#    Suppose you have 'elec_prices.csv' with Date, US, KZ, RU, CA, Others
print("Loading electricity prices…")
df_elec = (pd.read_csv("elec_prices.csv", parse_dates=["Date"])
             .set_index("Date"))
weights = {'US':0.35,'KZ':0.18,'RU':0.11,'CA':0.10,'Others':0.26}
df_elec['weighted'] = sum(df_elec[c]*w for c,w in weights.items())

# 8. Merge all
print("Merging…")
df = (df_btc
      .join(df_eth, how='outer')
      .join(df_eng, how='left')
      .join(df_hash, how='left')
      .join(df_tx, how='left')
      .join(df_spx, how='left')
      .join(df_vix, how='left')
      .join(df_dxy, how='left')
      .join(df_gold, how='left')
      .join(df_tot, how='left')
      .join(df_elec['weighted'], how='left')
     )

# 9. Compute EVMR
print("Computing EVMR…")
for label, price in [('Low',0.03),('Base',0.05),('High',0.07)]:
    df[f"EVMR_{label}"] = df['energy_twh_day']*1e6*price / df['btc-bitcoin_market_cap']

# 10. Export
print(f"Saving to {OUTPUT}")
df.to_excel(OUTPUT)
print("Done!")
