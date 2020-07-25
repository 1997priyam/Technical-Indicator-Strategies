import pandas as pd
from ta.utils import dropna
from ta.momentum import RSIIndicator
import json
from kiteconnect import KiteConnect, KiteTicker
import datetime
import sys
import time

DURATION_OF_DATA = 50
CANDLE_SIZE = "monthly"  # 1minute, 15minute, 30minute, 60minute, day, weekly, monthly

ZERODHA_CONFIG = {
    "API_KEY": "rtrb09gubf9ttq4d",
    "ACCESS_TOKEN": "yO46xgcjwI1OustSw3knAsy74hZECZi8"
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

def get_data_of_stock(zerodha, stock, duration, interval):
    org_interval = interval
    if(interval == "weekly"):
        duration = 200
        interval = "day"
    elif(interval == "monthly"):
        duration = 750
        interval = "day"
    else:
        pass
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

def get_range(last_candle_rsi, stock):
    if (last_candle_rsi.isnull().all()):
        print("All RSI values are NULL, increase DURATION_OF_DATA")
        sys.exit(1)
    if (len(last_candle_rsi) > 1):
        print("Only last candle is required")
        sys.exit(1)
    rsi = last_candle_rsi.iloc[0]
    if (rsi > 0 and rsi < 45):
        print('%-10s  ---------------> %10s' % (stock, "D"))
    elif (rsi > 45 and rsi < 55):
        print('%-10s  ---------------> %10s' % (stock, "SW"))
    elif (rsi > 55 and rsi < 100):
        print('%-10s  ---------------> %10s' % (stock, "U"))
    else:
        pass

def main():
    zerodha = get_zerodha_client(ZERODHA_CONFIG)
    instruments = zerodha.instruments("NSE")
    stock_list = filter_instruments(instruments)
    for stock in stock_list:
        try:
            candles = get_data_of_stock(zerodha, stock, DURATION_OF_DATA, CANDLE_SIZE)
            rsi = RSIIndicator(close=candles['close'], n=RSI_DAYS)
            if (CANDLES_TO_OBSERVE == 1):
                get_range(rsi.rsi().tail(CANDLES_TO_OBSERVE), stock["stock"])
            else:
                crossovers = get_crossovers(rsi.rsi().tail(CANDLES_TO_OBSERVE))
                print_crossovers(crossovers, stock["stock"])
            time.sleep(0.2)
        except Exception as e:
            print(e)
            pass

if __name__ == "__main__":
    main()