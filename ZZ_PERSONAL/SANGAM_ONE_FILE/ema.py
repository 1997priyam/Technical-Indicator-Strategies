DAYS_TO_OBSERVE = 5
DECIMAL_PLACES = 2
DURATION_OF_DATA = 80
EMA_FOR_DAYS = {
    5: 0.33,       #9, 21, 55
    13: 0.14,      # 5:0.33, 13:0.14, 26:0.074
    26: 0.074     # 9, 12, 26
                # 13, 55
                # 20, 50, 200
}
TICKER_FILE = "../tickers_nse.csv"

import csv
import re
from functools import reduce
from dateutil import parser
from numpy import *
import requests
import math
import json
import datetime
import nsepy

def get_data_of_stock(zerodha, stock, duration, interval):
    startDate = datetime.date.today() - datetime.timedelta(duration)
    endDate = datetime.date.today()
    data = zerodha.historical_data(stock["instrument_token"], startDate, endDate, interval)
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


EMA_SOURCE = 'close'
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

def read_candles(stock):
    candles = get_data_of_stock(zerodha, stock, DURATION_OF_DATA, "day")
    return candles

def isCrossover(candles, stock_name):
    variable_names = ["ema_{}".format(days) for days in EMA_FOR_DAYS]
    crossover_data = []
    for i in range(len(candles) - 1):
        intersection_points = []
        for j in range(len(variable_names) - 1):
            p1 = array([float(i), candles[i][variable_names[j]]])
            p2 = array([float(i+1), candles[i+1][variable_names[j]]])
            p3 = array([float(i), candles[i][variable_names[j+1]]])
            p4 = array([float(i+1), candles[i+1][variable_names[j+1]]])
            point = seg_intersect(p1, p2, p3, p4)
            if validate_point(point, [p1[0], p2[0]]):
                intersection_points.append(point)
            else:
                intersection_points = []
                break

        if(len(intersection_points) > 0):
            if arePointsEqual(intersection_points):
                candles[i]["stock"] = stock_name
                crossover_data.append(candles[i])
                crossover_data.append(candles[i+1])
    return crossover_data
        

# Calculates the SMA of an array of candles using the `source` price.
def calculate_sma(candles, source):
    length = len(candles)
    sum = reduce((lambda last, x: { source: last[source] + x[source] }), candles)
    sma = sum[source] / length
    return sma

def calculate_ema(candles, source, days):
    length = len(candles)
    target = candles[0]
    previous = candles[1]

    ema_name = "ema_{}".format(days)
    # if there is no previous EMA calculated, then EMA=SMA
    if ema_name not in previous or previous[ema_name] == None:
        return calculate_sma(candles, source)

    else:
        # multiplier: (2 / (length + 1))
        # EMA: (close * multiplier) + ((1 - multiplier) * EMA(previous))
        # multiplier = 2 / (length + 1)
        multiplier = EMA_FOR_DAYS[days]
        ema = (target[source] * multiplier) + (previous[ema_name] * (1 - multiplier))

        return ema

def calculate(candles, source, days):
    sma_name = "sma_{}".format(days)
    candles[0][sma_name] = calculate_sma(candles, source)
    ema_name = "ema_{}".format(days)
    candles[0][ema_name] = calculate_ema(candles, source, days)


def dump_set_to_file(stockSet):
    if(len(stockSet) == 0):
        return
    with open(FINAL_FILENAME, 'a') as final_file:
        for stock in stockSet:
            if (isinstance(stock, str)):
                final_file.write("{}\n".format(stock))
            else:
                final_file.write("{}\n".format(stock["stock"]))
                print("CROSSOVER--> {}".format(stock["stock"]))
                break

if __name__ == '__main__':
    crossover_final = []
    stock_set = set()
    try:
        with open(FINAL_FILENAME, "w"):
            pass
    except Exception as e:
        raise e
    stock_list = get_tickers_from_file(TICKER_FILE)
    for stock in stock_list:
        candles = []
        try:
            candles = read_candles(stock)
            if(len(candles) == 0):
                continue
        except Exception as e:
            print(e)
        stock = stock["stock"]
        for days in EMA_FOR_DAYS:
            position = 0
            while position + days <= len(candles):
                current_candles = candles[position : (position + days)]
                current_candles = list(reversed(current_candles))
                calculate(current_candles, EMA_SOURCE, days)
                position += 1

        try:
            crossover_data = isCrossover(candles[DAYS_TO_OBSERVE * -1 :], stock)
            crossover_final.extend(crossover_data)
            if(len(crossover_data) > 0):
                # print(crossover_data)
                dump_set_to_file(crossover_data)
        except Exception as e:
            pass

    if (len(crossover_final) > 0):
        for i in range(len(crossover_final) // 2):
            stock_set.add(crossover_final[2*i]["stock"])
    else:
        print("NO CROSSOVER")
    # dump_set_to_file(stock_set)
