import json
from kiteconnect import KiteConnect, KiteTicker
from config import ZERODHA_CONFIG as creds
import datetime


def get_zerodha_client(creds):
    zerodha = KiteConnect(api_key = creds["API_KEY"])
    zerodha.set_access_token(creds["ACCESS_TOKEN"])
    return zerodha

def filter_instruments(instruments):
    final_frame = []
    for data in instruments:
        if(data["instrument_type"] == "EQ" and data["exchange"] == "NSE"):
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
