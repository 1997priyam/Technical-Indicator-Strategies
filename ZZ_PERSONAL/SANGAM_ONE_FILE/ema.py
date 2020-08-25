DAYS_TO_OBSERVE = 20
DECIMAL_PLACES = 1
DURATION_OF_DATA = 90
EMA_FOR_DAYS = [5, 13, 26]
        #9, 21, 55
        # 5, 13, 26
        # 9, 12, 26
        # 13, 55
        # 20, 50, 200
TICKER_FILE = "../tickers_nse.csv"
# TICKER_FILE = "../tickers_bse.csv"
CLOSE_COLUMN = "Close"

import csv
from functools import reduce
from dateutil import parser
from numpy import *
import math
import json
import datetime
import nsepy
from ta.trend import EMAIndicator, SMAIndicator
import multiprocessing

FILE_LOCK = multiprocessing.Lock()

def get_data_of_stock(stock, duration):
    startDate = datetime.datetime.today() - datetime.timedelta(duration)
    endDate = datetime.datetime.today()
    data = nsepy.get_history(symbol=stock, start=startDate, end=endDate)
    return data

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

def arePointsEqual(points):
    if(len(points) == 1): 
        return True
    points = [[round(pt[0], DECIMAL_PLACES), round(pt[1], DECIMAL_PLACES)] for pt in points]
    for i in range(len(points) - 1):
        if (points[i][0] != points[i+1][0] or points[i][1] != points[i+1][1]):
            return False
    return True


FINAL_FILENAME = "sangam"

def get_tickers_from_file(filename):
    tickers = []
    with open(filename) as tfile:
        csvreader = csv.reader(tfile)
        for sym in csvreader:
            try:
                tickers.append(sym[0])
            except Exception:
                pass
    return tickers


def isCrossover(candles, stock_name):
    variable_names = ["ema_{}".format(days) for days in EMA_FOR_DAYS]
    for i in range(len(candles) - 1):
        intersection_points = []
        for j in range(len(variable_names) - 1):
            p1 = array([float(i), candles.iloc[i][variable_names[j]]])
            p2 = array([float(i+1), candles.iloc[i+1][variable_names[j]]])
            p3 = array([float(i), candles.iloc[i][variable_names[j+1]]])
            p4 = array([float(i+1), candles.iloc[i+1][variable_names[j+1]]])
            point = seg_intersect(p1, p2, p3, p4)
            if validate_point(point, [p1[0], p2[0]]):
                intersection_points.append(point)
            else:
                intersection_points = []
                break

        if(len(intersection_points) > 0):
            if arePointsEqual(intersection_points):
                return True
    return False

def get_ema(data, days):
    """
    Function to get the EMA of a ticker
    """
    ema = EMAIndicator(close=data, n=days)
    return ema.ema_indicator()

def get_sma(data, days):
    """
    Function to get the EMA of a ticker
    """
    sma = SMAIndicator(close=data, n=days)
    return sma.sma_indicator()

def calculate(candles, days):
    sma_name = "sma_{}".format(days)
    candles[sma_name] = get_sma(candles[CLOSE_COLUMN], days)
    ema_name = "ema_{}".format(days)
    candles[ema_name] = get_ema(candles[CLOSE_COLUMN], days)

def dump_set_to_file(stock):
    try:
        with FILE_LOCK:
            with open(FINAL_FILENAME, 'a') as final_file:
                final_file.write("{}\n".format(stock))
                print("CROSSOVER--> {}".format(stock))
    except Exception as e:
        print(e)
        raise e



def actual_processor(stock):
    candles = get_data_of_stock(stock, DURATION_OF_DATA)
    if candles is None or candles.empty:
        return
    for days in EMA_FOR_DAYS:
        calculate(candles, days)
    try:
        if isCrossover(candles.tail(DAYS_TO_OBSERVE), stock):
            dump_set_to_file(stock)
    except Exception as e:
        print(e)
        raise e

if __name__ == '__main__':
    with open(FINAL_FILENAME, "w"):
        pass
    stock_list = get_tickers_from_file(TICKER_FILE)
    with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
        prList = [pool.apply_async(actual_processor, [ticker]) for ticker in stock_list]
        [res.wait() for res in prList]
