import nsepy
import datetime
from datetime import date
import pandas as pd
import csv
from yahoo_finance import Share
import yfinance as yf

# def get_tickers_from_file(filename):
#     tickers = []
#     with open(filename) as tfile:
#         csvreader = csv.reader(tfile)
#         for sym in csvreader:
#             try:
#                 tickers.append(sym[0])
#             except Exception:
#                 pass
#     return tickers

# tickers = get_tickers_from_file("tickers_nse.csv")
tickers = ["SBIN", "HDFC", "RELIANCE"]

for symbol in tickers:
    data = nsepy.get_history(symbol=symbol, start=date(2020,7,12), end=date(2020,8,15))
    print(data)
    # data = data.iloc[0].name
    # sh = Share(symbol)
    # print(sh.get_historical('2020-04-25', '2020-04-29'))
    # a = yf.Ticker(symbol)
    # print(a.info)
