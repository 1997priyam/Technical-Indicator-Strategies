CANDLE_SIZE_SET = ["day", "60minute", "15minute"]  # 1minute, 15minute, 30minute, 60minute, day, weekly, monthly
# CANDLE_SIZE_SET = ["monthly", "weekly", "day"]    # 1minute, 15minute, 30minute, 60minute, day, weekly, monthly
DIFFERENCE_TIME_FRAME = ["day", "60minute"]     # (day - 60minute)
RSI_A = 45
RSI_B = 55
WRITE_TO_FILE = True

import pandas as pd
from ta.momentum import RSIIndicator
import json
from kiteconnect import KiteConnect, KiteTicker
import datetime
import sys
import time
import csv


ZERODHA_CONFIG = {
    "API_KEY": "",
    "ACCESS_TOKEN": ""
}
stock_list = [
    "ACC","ADANIENT","ADANIPORTS","AMARAJABAT","AMBUJACEM","APOLLOHOSP",
    "APOLLOTYRE","ASHOKLEY","ASIANPAINT","AUROPHARMA","AXISBANK",
    "BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV","BALKRISIND","BANDHANBNK",
    "BANKBARODA","BATAINDIA","BERGEPAINT","BEL","BHARATFORG","BPCL",
    "BHARTIARTL","INFRATEL","BHEL","BIOCON","BOSCHLTD","BRITANNIA",
    "CADILAHC","CANBK","CENTURYTEX","CHOLAFIN","CIPLA","COALINDIA",
    "COLPAL","CONCOR","CUMMINSIND","DABUR","DIVISLAB","DLF","DRREDDY",
    "EICHERMOT","EQUITAS","ESCORTS","EXIDEIND","FEDERALBNK","GAIL",
    "GLENMARK","GMRINFRA","GODREJCP","GODREJPROP","GRASIM","HAVELLS",
    "HCLTECH","HDFCBANK","HDFC","HDFCLIFE","HEROMOTOCO","HINDALCO",
    "HINDPETRO","HINDUNILVR","ICICIBANK","ICICIPRULI","NAUKRI","IDEA",
    "IDFCFIRSTB","IBULHSGFIN","IOC","IGL","INDUSINDBK","INFY","INDIGO",
    "ITC","JINDALSTEL","JSWSTEEL","JUBLFOOD","JUSTDIAL","KOTAKBANK","L&TFH",
    "LT","LICHSGFIN","LUPIN","M&MFIN","MGL","M&M","MANAPPURAM","MARICO",
    "MARUTI","MFSL","MINDTREE","MOTHERSUMI","MRF","MUTHOOTFIN","NATIONALUM",
    "NCC","NESTLEIND","NIITTECH","NMDC","NTPC","ONGC","PAGEIND","PETRONET",
    "PIDILITIND","PEL","PFC","POWERGRID","PNB","PVR","RBLBANK","RELIANCE",
    "RECLTD","SHREECEM","SRTRANSFIN","SIEMENS","SRF","SBIN","SBILIFE",
    "SAIL","SUNPHARMA","SUNTV","TATACHEM","TCS","TATACONSUM","TATAMOTORS",
    "TATAPOWER","TATASTEEL","TECHM","RAMCOCEM","TITAN","TORNTPHARM",
    "TORNTPOWER","TVSMOTOR","UJJIVAN","ULTRACEMCO","UBL","MCDOWELL-N","UPL",
    "VEDL","VOLTAS","WIPRO","ZEEL","NIFTY 50","NIFTY BANK"
]

CANDLES_TO_OBSERVE = 1
CROSSOVER_VALUE = 50
RSI_DAYS = 14

def create_respective_candles(candles, interval):
    candles = pd.DataFrame(candles).set_index('date')
    candles.index = pd.to_datetime(candles.index)
    logic = {'open'  : 'first',
            'high'  : 'max',
            'low'   : 'min',
            'close' : 'last',
            'volume': 'sum'}
    if(interval == "weekly"):
        offset = pd.offsets.timedelta(days=-6)
        candles = candles.resample('W').agg(logic, loffset=offset)
    elif(interval == "monthly"):
        candles = candles.resample('1M').agg(logic)
    else:
        pass
    return candles


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

def get_data_of_stock(zerodha, stock, interval):
    org_interval = interval
    duration = 0
    if(interval == "weekly"):
        duration = 500
        interval = "day"
    elif(interval == "monthly"):
        duration = 900
        interval = "day"
    elif(interval == "day"):
        duration = 100
    else:
        duration = 50
    startDate = datetime.date.today() - datetime.timedelta(duration)
    endDate = datetime.date.today()
    data = zerodha.historical_data(stock["instrument_token"], startDate, endDate, interval)
    data = create_respective_candles(data, org_interval)
    return data

def print_crossovers(crossovers, stock):
    for cross in crossovers:
        print("STOCK--> {} -- {}".format(stock, cross))

def get_crossovers(rsi_data_points):
    crossing_list = []
    if (rsi_data_points.isnull().all()):
        print("All RSI values are NULL, increase DURATION_OF_DATA")
        sys.exit(1)
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

def print_range(range_data, stock, alerts):
    if range_data == None or not isinstance(range_data, list):
        return
    print_str = ""
    range_data.extend(alerts)
    for each_range in range_data:
        print_str += each_range + "    "
    print('%-10s  -----> %s' % (stock, print_str))
    
def write_to_file(range_list, stock):
    write_list = []
    write_list.append(stock)
    for value in range_list:
        value = value[:-2]
        write_list.append(value)
    with open("rsi.csv", "a") as write_file:
        csvwriter = csv.writer(write_file)
        csvwriter.writerow(write_list)

def get_range(last_candle_rsi, stock):
    if (last_candle_rsi.isnull().all()):
        print("All RSI values are NULL, increase DURATION_OF_DATA")
        sys.exit(1)
    if (len(last_candle_rsi) > 1):
        print("Only last candle is required")
        sys.exit(1)
    rsi = last_candle_rsi.iloc[0]
    rsi = round(rsi, 2)
    if (rsi > 0 and rsi < RSI_A):
        # print('%-10s  ---------------> %10s' % (stock, "D"))
        return "{:.2f} D".format(rsi)
    elif (rsi > RSI_A and rsi < RSI_B):
        # print('%-10s  ---------------> %10s' % (stock, "SW"))
        return "{:.2f} S".format(rsi)
    elif (rsi > RSI_B and rsi < 100):
        # print('%-10s  ---------------> %10s' % (stock, "U"))
        return "{:.2f} U".format(rsi)
    else:
        return None

def get_alerts(last_rsi):
    alerts = []
    try:
        if len(DIFFERENCE_TIME_FRAME) != 2:
            raise Exception
        if (last_rsi[DIFFERENCE_TIME_FRAME[0]] - last_rsi[DIFFERENCE_TIME_FRAME[1]]) > 15:
            alerts.append("Alert-1  ")
        if (last_rsi["15minute"] < 40):
            alerts.append("Alert-2  ")
    except Exception as e:
        pass
    finally:
        return alerts


def main():
    zerodha = get_zerodha_client(ZERODHA_CONFIG)
    instruments = zerodha.instruments("NSE")
    stock_list = filter_instruments(instruments)
    print_str = ""
    for candle in CANDLE_SIZE_SET:
        print_str += candle + "    "
    print("                     {}".format(print_str))
    row = ["STOCK"]
    row.extend(CANDLE_SIZE_SET)
    with open("rsi.csv", "w") as write_file:
        csvwriter = csv.writer(write_file)
        csvwriter.writerow(row)
    for stock in stock_list:
        try:
            range_list = []
            last_rsi = {}
            for CANDLE_SIZE in CANDLE_SIZE_SET:
                candles = get_data_of_stock(zerodha, stock, CANDLE_SIZE)
                rsi = RSIIndicator(close=candles['close'], n=RSI_DAYS)
                last_rsi[CANDLE_SIZE] = rsi.rsi().tail(CANDLES_TO_OBSERVE).iloc[0]
                if (CANDLES_TO_OBSERVE == 1):
                    range_stock = get_range(rsi.rsi().tail(CANDLES_TO_OBSERVE), stock["stock"])
                    range_list.append(range_stock)
                else:
                    crossovers = get_crossovers(rsi.rsi().tail(CANDLES_TO_OBSERVE))
                    print_crossovers(crossovers, stock["stock"])
            alerts = get_alerts(last_rsi)
            print_range(range_list, stock["stock"], alerts)
            if WRITE_TO_FILE:
                write_to_file(range_list, stock["stock"])
        except Exception as e:
            print(e)

if __name__ == "__main__":
    main()