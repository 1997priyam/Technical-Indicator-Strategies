EMA_FOR_DAYS = [9, 21, 55]
# TOKEN = "bslct37rh5rb8ivkrvgg"
TOKEN_1 = ""
TOKEN_2 = ""
TOKEN_3 = ""
TOKEN_4 = ""
FILENAME = "crossover.txt"


global CANDLES_TO_OBSERVE
CANDLE_SIZE = "1"           # Accepted values = 1, 5, 15, 30, 60, D
CANDLES_TO_OBSERVE = "1D"  # Accepted values in minutes and days only (Not hours) For 2 hours input 120m. EG: 5D, 60M, 120M etc.



from get_all_tickers import get_tickers as gt
import datetime
import requests
from ta.trend import EMAIndicator
import pandas as pd
from numpy import *
import csv
import multiprocessing as mp
from multiprocessing.pool import ThreadPool
import sys

THREAD_WORKERS = 4
TOKEN_LOCK = mp.Lock()
FILE_LOCK = mp.Lock()
TOKENS = [TOKEN_1, TOKEN_2, TOKEN_3, TOKEN_4]
global DURATION
DURATION = None

def perp( a ) :
    b = empty_like(a)
    b[0] = -a[1]
    b[1] = a[0]
    return b

def seg_intersect(a1,a2, b1,b2) :
    da = a2-a1
    db = b2-b1
    dp = a1-b1
    dap = perp(da)
    denom = dot( dap, db)
    num = dot( dap, dp )
    out = (num / denom.astype(float))*db + b1
    return out

def validate_point(point, range):
    if isnan(point).any() or isinf(point).any() or isneginf(point).any():
        return False

    if(point[0] >= range[0] and point[0] <= range[1]):
        return True
    else:
        return False

def get_ticker_data(ticker):
    """
    It will get OHLC for respective ticker
    """
    try:
        startDate = int((datetime.datetime.now() - datetime.timedelta(DURATION)).timestamp())
        endDate = int(datetime.datetime.now().timestamp())
        with TOKEN_LOCK:
            token = TOKENS.pop(0)
            TOKENS.append(token)
        r = requests.get('https://finnhub.io/api/v1/stock/candle?symbol={}&resolution={}&from={}&to={}&token={}'.format(ticker, 
        CANDLE_SIZE, startDate, endDate, token))
        return r.json()
    except Exception as e:
        # print("No data for {}".format(ticker))
        pass

def get_ema(data, days):
    """
    Function to get the EMA of a ticker
    """
    ema = EMAIndicator(close=data["c"], n=days)
    return ema.ema_indicator()

def is_crossover(candles):
    """
    Actual logic of the strategy which finds if 5 days EMA is > than rest
    """
    EMA_FOR_DAYS.sort()
    small_ema = EMA_FOR_DAYS[0]
    crossover_data = {}
    for j in range(1, len(EMA_FOR_DAYS)):
        intersection_points = []
        for i in range(len(candles) - 1):
            p1 = array([float(i), candles.iloc[i][small_ema]])
            p2 = array([float(i+1), candles.iloc[i+1][small_ema]])
            p3 = array([float(i), candles.iloc[i][EMA_FOR_DAYS[j]]])
            p4 = array([float(i+1), candles.iloc[i+1][EMA_FOR_DAYS[j]]])
            point = seg_intersect(p1, p2, p3, p4)
            if validate_point(point, [p1[0], p2[0]]):
                intersection_points.append((candles.iloc[i]["t"], candles.iloc[i]["c"]))
        if len(intersection_points) == 0:
            return False
        else:
            crossover_data["{}_{}".format(small_ema, EMA_FOR_DAYS[j])] = intersection_points
    return crossover_data
            
def is_uptrend(candle):
    min_ema = min(EMA_FOR_DAYS)
    ema_values = []
    for ema in EMA_FOR_DAYS:
        ema_values.append(candle.iloc[0][ema])
    max_value = max(ema_values)
    return True if candle.iloc[0][min_ema] == max_value else False

def dump_to_file(run_date, ticker, price, crossover_data):
    """
    Function to dump picks to the file
    """
    print_string = "{} -- {} -- Current Price: {} -- ".format(run_date, ticker, price)
    for key, value in crossover_data.items():
        crossover_ema_days = "&".join(key.split("_"))
        times = len(value)
        crossover_dates_price = ""
        for cross in value:
            date = datetime.datetime.fromtimestamp(cross[0]).strftime("%d-%m-%Y, %H:%M")
            price = cross[1]
            crossover_dates_price += "{}({}), ".format(date, price)
        crossover_dates_price = crossover_dates_price[:-2]
        print_string += "Crossover: {} on {} -- ".format(crossover_ema_days, crossover_dates_price)
    print_string = print_string[:-4]
    with FILE_LOCK:
        with open(FILENAME, "a") as final_file:
            print(print_string)
            final_file.write("{}\n".format(print_string))

def set_duration_and_observe_candle():
    global CANDLES_TO_OBSERVE
    global DURATION
    try:
        unit = CANDLES_TO_OBSERVE[-1].lower()
        value = int(CANDLES_TO_OBSERVE[:-1])
    except Exception:
        print("Invalid input, please check again")
        sys.exit(1)

    if (unit == "d" or unit == "m"):
        pass
    else:
        print("Invalid Unit in CANDLES_TO_OBSERVE, only add minutes (M) or days (D)")
        sys.exit(1)

    if (CANDLE_SIZE == "D"):
        DURATION = 100
        if (unit == "d"):
            CANDLES_TO_OBSERVE = value
        else:
            print("CANDLE_SIZE is 'D' so please enter CANDLES_TO_OBSERVE in days only")
            sys.exit(1)
    else:
        DURATION = 10
        if (unit == "d"):
            CANDLES_TO_OBSERVE = 390 * value
        else:
            CANDLES_TO_OBSERVE = value // int(CANDLE_SIZE)

    if (CANDLES_TO_OBSERVE < 3):
        print("Please check the input params carefully, increase the value of CANDLES_TO_OBSERVE")
        sys.exit(1)
    else:
        print("Observing {} candles".format(CANDLES_TO_OBSERVE))



def actual_processor(ticker):
    try:
        data = get_ticker_data(ticker)
        data = pd.DataFrame(data, columns=['c', 't'])
        for days in EMA_FOR_DAYS:
            ema = get_ema(data, days)
            data[days] = ema
        crossover_data = is_crossover(data.tail(CANDLES_TO_OBSERVE))
        if crossover_data and is_uptrend(data.tail(1)):
            dump_to_file(run_date, ticker, data.tail(1).iloc[0]["c"], crossover_data)
    except Exception as e:
        raise e

if __name__ == "__main__":
    set_duration_and_observe_candle()
    run_date = datetime.datetime.today().strftime("%d-%m-%Y, %H:%M")
    with open(FILENAME, "a") as write_file:
        write_file.write("Running on {}\n".format(run_date))
        print("Running on {}".format(run_date))
    tickers = []
    with open("tickers.csv") as ticker_file:
        try:
            csvreader = csv.reader(ticker_file)
            for row in csvreader: 
                tickers.append(row[0])
        except Exception:
            pass
    # tickers = gt.get_tickers(NYSE=True, NASDAQ=True)
    # tickers = ["ERF"]
    pool = ThreadPool(THREAD_WORKERS)
    pool.map(actual_processor, tickers)
    pool.close()
    pool.join()

