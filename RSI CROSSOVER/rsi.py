import zerodha as zd
import pandas as pd
from ta.utils import dropna
from ta.momentum import RSIIndicator
import json
from kiteconnect import KiteConnect, KiteTicker
import datetime

CANDLES_TO_OBSERVE = 5
DURATION_OF_DATA = 5
CANDLE_SIZE = "15minute"
RSI_DAYS = 14
CROSSOVER_VALUE = 50

FINAL_FILENAME = "rsi_cross"
ZERODHA_CONFIG = {
    "API_KEY": "rtrb09gubf9ttq4d",
    "ACCESS_TOKEN": "PDzyHEssIgHxIwK7f74HGOvqkfFKx0gS"
}

stock_list = [
    "ACC",
    "HDFC",
    "RELIANCE",
    "BAJAJFINSV",
    "ITC",
    "ICICIBANK"
]


def get_zerodha_client(creds):
    zerodha = KiteConnect(api_key = creds["API_KEY"])
    zerodha.set_access_token(creds["ACCESS_TOKEN"])
    return zerodha

def filter_instruments(instruments):
    final_frame = []
    for data in instruments:
        if(data["instrument_type"] == "EQ" and data["tradingsymbol"] in stock_list):
            final_frame.append({
                "instrument_token": data["instrument_token"],
                "stock": data["tradingsymbol"]
            })
    return final_frame

def get_data_of_stock(zerodha, stock, duration, interval):
    startDate = datetime.date.today() - datetime.timedelta(duration)
    endDate = datetime.date.today()
    data = zerodha.historical_data(stock["instrument_token"], startDate, endDate, interval)
    return data

def print_crossovers(crossovers, stock):
    for cross in crossovers:
        print("STOCK--> {} -- {}".format(stock, cross))

def get_crossovers(rsi_data_points):
    crossing_list = []
    if (rsi_data_points.isnull().all()):
        raise Exception("All RSI values are NULL, increase DURATION_OF_DATA")
    for i in range(len(rsi_data_points) - 1):
        prev = rsi_data_points.iloc[i]
        current = rsi_data_points.iloc[i+1]
        if (prev < CROSSOVER_VALUE and current < CROSSOVER_VALUE):
            pass
        elif(prev > CROSSOVER_VALUE and current > CROSSOVER_VALUE):
            pass
        elif(prev <= CROSSOVER_VALUE and current > CROSSOVER_VALUE):
            crossing_list.append("UPWARD_CROSSING_{}.{}".format(i, i+1))
        elif(prev >= CROSSOVER_VALUE and current < CROSSOVER_VALUE):
            crossing_list.append("DOWNWARD_CROSSING_{}.{}".format(i, i+1))
        else:
            pass
    return crossing_list

def main():
    zerodha = zd.get_zerodha_client(ZERODHA_CONFIG)
    instruments = zerodha.instruments("NSE")
    stock_list = zd.filter_instruments(instruments)
    for stock in stock_list:
        candles = pd.DataFrame(zd.get_data_of_stock(zerodha, stock, DURATION_OF_DATA, CANDLE_SIZE))
        rsi = RSIIndicator(close=candles['close'], n=RSI_DAYS)
        crossovers = get_crossovers(rsi.rsi().tail(CANDLES_TO_OBSERVE))
        print_crossovers(crossovers, stock["stock"])

if __name__ == "__main__":
    main()