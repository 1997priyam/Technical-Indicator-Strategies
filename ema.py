import csv
import re
from functools import reduce
from dateutil import parser
from numpy import *
import math
import utils
from config import *
EMA_SOURCE = 'close'
# Reads the input file and saves to `candles` all the candles found. Each candle is
# a dict with the timestamp and the OHLC values.
def read_candles(csv_file_name):
    candles = []
    with open(csv_file_name, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            try:
                if (row[1] == "EQ"):
                    candles.append({
                        'ts': parser.parse(row[TIMESTAMP_COLUMN_NUMBER - 1]),
                        'close': float(row[CLOSE_COLUMN_NUMBER - 1])
                    })
            except Exception as e:
                pass
                # print('Error parsing {}'.format(row))
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
            point = utils.seg_intersect(p1, p2, p3, p4)
            if utils.validate_point(point, [p1[0], p2[0]]):
                intersection_points.append(point)
            else:
                intersection_points = []
                break

        if(len(intersection_points) > 0):
            if utils.arePointsEqual(intersection_points):
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

# Calculates the EMA of an array of candles using the `source` price.
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
        multiplier = 2 / (length + 1)
        # multiplier = EMA_FOR_DAYS[days]
        ema = (target[source] * multiplier) + (previous[ema_name] * (1 - multiplier))

        return ema

def calculate(candles, source, days):
    sma_name = "sma_{}".format(days)
    candles[0][sma_name] = round(calculate_sma(candles, source), DECIMAL_PLACES)
    ema_name = "ema_{}".format(days)
    candles[0][ema_name] = round(calculate_ema(candles, source, days), DECIMAL_PLACES)

if __name__ == '__main__':
    crossover_final = []
    for stock in stock_list:
        candles = []
        file_name = "data/{}.csv".format(stock)
        try:
            candles = read_candles(file_name)
        except FileNotFoundError:
            print("Data file for {} not found".format(stock))
        # progress through the array of candles to calculate the indicators for each
        # block of candles

        for days in EMA_FOR_DAYS:
            position = 0
            while position + days <= len(candles):
                current_candles = candles[position : (position + days)]
                current_candles = list(reversed(current_candles))
                calculate(current_candles, EMA_SOURCE, days)
                position += 1

        for candle in candles:
            try:
                print('{}: stock: {}  ema_10={}  ema_20={}  ema_30={}'.format(candle['ts'], stock, candle['ema_10'], candle['ema_20'], candle['ema_30']))
            except Exception:
                pass

        # print(candles[DAYS_TO_OBSERVE * -1 :])
        crossover_data = isCrossover(candles[DAYS_TO_OBSERVE * -1 :], stock)
        crossover_final.extend(crossover_data)

    if (len(crossover_final) > 0):
        for i in range(len(crossover_final) // 2):
            print("Crossover Detected--> STOCK: {}    BETWEEN DATE: {} and {}".format(
                crossover_final[2*i]["stock"], 
                crossover_final[2*i]["ts"].strftime("%d-%m-%Y"), 
                crossover_final[(2*i)+1]["ts"].strftime("%d-%m-%Y")))
    else:
        print("NO CROSSOVER")