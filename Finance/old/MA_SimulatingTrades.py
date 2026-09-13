import datetime as dt
import time

import numpy as np
import pandas as pd
from pandas_datareader import data as pdr

pd.options.mode.chained_assignment = None  # default='warn'

t_s = time.time()

endDate = dt.datetime.now()
startDate = endDate - dt.timedelta(days=1020)

firstBuyDateString = '2020-01-01'
firstBuyDate = dt.datetime.strptime(firstBuyDateString, '%Y-%m-%d')


def _noTrade(df):
    rows = []
    total = 0
    flag = -1
    for i in df.index:
        # buy the first share
        if (i < firstBuyDate):
            continue
        if (i >= firstBuyDate) & (flag == -1):
            priceB = round(df['Adj Close'][i], 2)
            total -= priceB
            row = [i.strftime('%Y-%m-%d'), -priceB]
            rows.append(row)
            flag = 1
    # sell the last share
    if flag != 0:
        sigPriceS = round(df['Adj Close'][i], 2)
        total += sigPriceS
        row = [i.strftime('%Y-%m-%d'), sigPriceS, round((sigPriceS - priceB) / priceB * 100, 2)]
        rows.append(row)
    # out_df = pd.DataFrame(rows, columns=['date', 'price', 'percentile'])
    # print(out_df)
    return round(total, 2)


def _SMA(df, x):
    rows = []
    df['SMA'] = round(df['Adj Close'].rolling(window=x).mean(), 2)  # Simple Moving Average
    # TEMA triple exponential moving average | EMA Exponential Moving Average
    df['EMA1'] = round(df['Adj Close'].ewm(span=x, adjust=False).mean(), 2)
    df['EMA2'] = round(df['EMA1'].ewm(span=x, adjust=False).mean(), 2)
    df['EMA3'] = round(df['EMA2'].ewm(span=x, adjust=False).mean(), 2)
    df['TEMA'] = 3 * (df['EMA1'] - df['EMA2']) + df['EMA3']

    # up/down from previous 2 days
    df['SMA_2'] = df.SMA.shift(2)
    df['TEMA_2'] = df.TEMA.shift(2)
    df['SMA_up'] = df.apply(lambda x: '+' if x['SMA'] >= x['SMA_2'] else '-', axis=1)
    df['TEMA_up'] = df.apply(lambda x: '+' if x['TEMA'] >= x['TEMA_2'] else '-', axis=1)

    prevDir = 0
    total = 0
    flag = -1
    for i in df.index:
        # buy the first share
        if (i < firstBuyDate):
            continue
        if (i >= firstBuyDate) & (flag == -1):
            priceB = round(df['Adj Close'][i], 2)
            total -= priceB
            row = [i.strftime('%Y-%m-%d'), -priceB]
            rows.append(row)
            flag = 1

        if (prevDir != df['SMA_up'][i]):
            if (flag != 1) & (df['SMA_up'][i] == '+'):
                priceB = round(df['Adj Close'][i], 2)
                total -= priceB
                row = [i.strftime('%Y-%m-%d'), -priceB]
                rows.append(row)
                flag = 1
                prevDir = df['SMA_up'][i]
            elif (flag != 0) & (df['SMA_up'][i] == '-'):
                sigPriceS = round(df['Adj Close'][i], 2)
                total += sigPriceS
                row = [i.strftime('%Y-%m-%d'), sigPriceS, round((sigPriceS - priceB) / priceB * 100, 2)]
                rows.append(row)
                flag = 0
                prevDir = df['SMA_up'][i]
    # sell the last share
    if flag != 0:
        sigPriceS = round(df['Adj Close'][i], 2)
        total += sigPriceS
        row = [i.strftime('%Y-%m-%d'), sigPriceS, round((sigPriceS - priceB) / priceB * 100, 2)]
        rows.append(row)
    # out_df = pd.DataFrame(rows, columns=['date', 'price', 'percentile'])
    # print(out_df)
    return round(total, 2)


def _TEMA(df, x):
    rows = []
    df['SMA'] = round(df['Adj Close'].rolling(window=x).mean(), 2)  # Simple Moving Average
    # TEMA triple exponential moving average | EMA Exponential Moving Average
    df['EMA1'] = round(df['Adj Close'].ewm(span=x, adjust=False).mean(), 2)
    df['EMA2'] = round(df['EMA1'].ewm(span=x, adjust=False).mean(), 2)
    df['EMA3'] = round(df['EMA2'].ewm(span=x, adjust=False).mean(), 2)
    df['TEMA'] = 3 * (df['EMA1'] - df['EMA2']) + df['EMA3']

    # up/down from previous 2 days
    df['SMA_2'] = df.SMA.shift(2)
    df['TEMA_2'] = df.TEMA.shift(2)
    df['SMA_up'] = df.apply(lambda x: '+' if x['SMA'] >= x['SMA_2'] else '-', axis=1)
    df['TEMA_up'] = df.apply(lambda x: '+' if x['TEMA'] >= x['TEMA_2'] else '-', axis=1)

    prevDir = 0
    total = 0
    flag = -1
    for i in df.index:
        # buy the first share
        if (i < firstBuyDate):
            continue
        if (i >= firstBuyDate) & (flag == -1):
            priceB = round(df['Adj Close'][i], 2)
            total -= priceB
            row = [i.strftime('%Y-%m-%d'), -priceB]
            rows.append(row)
            flag = 1

        if (prevDir != df['TEMA_up'][i]):
            if (flag != 1) & (df['TEMA_up'][i] == '+'):
                priceB = round(df['Adj Close'][i], 2)
                total -= priceB
                row = [i.strftime('%Y-%m-%d'), -priceB]
                rows.append(row)
                flag = 1
                prevDir = df['TEMA_up'][i]
            elif (flag != 0) & (df['TEMA_up'][i] == '-'):
                sigPriceS = round(df['Adj Close'][i], 2)
                total += sigPriceS
                row = [i.strftime('%Y-%m-%d'), sigPriceS, round((sigPriceS - priceB) / priceB * 100, 2)]
                rows.append(row)
                flag = 0
                prevDir = df['TEMA_up'][i]
    # sell the last share
    if flag != 0:
        sigPriceS = round(df['Adj Close'][i], 2)
        total += sigPriceS
        row = [i.strftime('%Y-%m-%d'), sigPriceS, round((sigPriceS - priceB) / priceB * 100, 2)]
        rows.append(row)
    # out_df = pd.DataFrame(rows, columns=['date', 'price', 'percentile'])
    # print(out_df)
    return round(total, 2)


def _TEMA_SMA(df, x):
    rows = []
    df['SMA'] = round(df['Adj Close'].rolling(window=x).mean(), 2)  # Simple Moving Average
    # TEMA triple exponential moving average | EMA Exponential Moving Average
    df['EMA1'] = round(df['Adj Close'].ewm(span=x, adjust=False).mean(), 2)
    df['EMA2'] = round(df['EMA1'].ewm(span=x, adjust=False).mean(), 2)
    df['EMA3'] = round(df['EMA2'].ewm(span=x, adjust=False).mean(), 2)
    df['TEMA'] = 3 * (df['EMA1'] - df['EMA2']) + df['EMA3']

    # up/down from previous 2 days
    df['SMA_2'] = df.SMA.shift(2)
    df['TEMA_2'] = df.TEMA.shift(2)
    df['SMA_up'] = df.apply(lambda x: '+' if x['SMA'] >= x['SMA_2'] else '-', axis=1)
    df['TEMA_up'] = df.apply(lambda x: '+' if x['TEMA'] >= x['TEMA_2'] else '-', axis=1)

    prevDir = 0
    total = 0
    flag = -1
    for i in df.index:
        # buy the first share
        if (i < firstBuyDate):
            continue
        if (i >= firstBuyDate) & (flag == -1):
            priceB = round(df['Adj Close'][i], 2)
            total -= priceB
            row = [i.strftime('%Y-%m-%d'), -priceB]
            rows.append(row)
            flag = 1

        if (prevDir != df['TEMA_up'][i]):
            if (flag != 1) & (df['TEMA_up'][i] == '+'):
                priceB = round(df['Adj Close'][i], 2)
                total -= priceB
                row = [i.strftime('%Y-%m-%d'), -priceB]
                rows.append(row)
                flag = 1
                prevDir = df['TEMA_up'][i]
            elif (flag != 0) & (df['TEMA_up'][i] == '-') & (df['TEMA'][i] > df['SMA'][i]):  # FIXME only sell when TEMA above SMA
                sigPriceS = round(df['Adj Close'][i], 2)
                total += sigPriceS
                row = [i.strftime('%Y-%m-%d'), sigPriceS, round((sigPriceS - priceB) / priceB * 100, 2)]
                rows.append(row)
                flag = 0
                prevDir = df['TEMA_up'][i]
    # sell the last share
    if flag != 0:
        sigPriceS = round(df['Adj Close'][i], 2)
        total += sigPriceS
        row = [i.strftime('%Y-%m-%d'), sigPriceS, round((sigPriceS - priceB) / priceB * 100, 2)]
        rows.append(row)
    out_df = pd.DataFrame(rows, columns=['date', 'price', 'percentile'])
    print(out_df)
    return round(total, 2)


def _MACD(df):
    rows = []
    # Calculate the MACD and Signal Line indicators
    ShortEMA = df.Close.ewm(span=12, adjust=False).mean()  # Short Term Exponential Moving Average AKA Fast moving average
    LongEMA = df.Close.ewm(span=26, adjust=False).mean()  # Long Term Exponential Moving Average AKA Slow moving average
    MACD = ShortEMA - LongEMA  # Moving Average Convergence/Divergence
    signal = MACD.ewm(span=9, adjust=False).mean()  # signal line

    df['MACD'] = MACD
    df['Signal Line'] = signal

    flag = -1
    total = 0
    priceB = 0
    for i in df.index:
        # buy the first share
        if (i < firstBuyDate):
            continue
        if (i >= firstBuyDate) & (flag == -1):
            sigPriceB = round(df['Adj Close'][i], 2)
            priceB = sigPriceB
            total -= sigPriceB
            row = [i.strftime('%Y-%m-%d'), -priceB]
            rows.append(row)
            flag = 1

        # buy if MACD > signal line else sell
        if df['MACD'][i] >= df['Signal Line'][i]:
            if flag != 1:
                sigPriceB = round(df['Adj Close'][i], 2)
                priceB = sigPriceB
                total -= sigPriceB
                row = [i.strftime('%Y-%m-%d'), -priceB]
                rows.append(row)
                flag = 1
        elif df['MACD'][i] < df['Signal Line'][i]:
            if flag != 0:
                sigPriceS = round(df['Adj Close'][i], 2)
                total += sigPriceS
                row = [i.strftime('%Y-%m-%d'), sigPriceS, round((sigPriceS - priceB) / priceB * 100, 2)]
                rows.append(row)
                flag = 0
    # sell the last share
    if flag != 0:
        sigPriceS = round(df['Adj Close'][i], 2)
        total += sigPriceS
        row = [i.strftime('%Y-%m-%d'), sigPriceS, round((sigPriceS - priceB) / priceB * 100, 2)]
        rows.append(row)
    # out_df = pd.DataFrame(rows, columns=['date', 'price', 'percentile'])
    # print(out_df)
    return round(total, 2)


# df = pd.read_csv('G:\My Drive\data\out_fidelity.csv')
# stockList = df['Ticker'].tolist()

stockList = ['NVDA']  # , 'TQQQ',  'INTC','FCEL', 'SPY'
stockList = list(set(stockList))  # make elements unique
stockList = sorted(stockList)
len=20
rows = []
for symbol in stockList:
    df = pdr.get_data_yahoo(symbol, startDate, endDate)
    row = [symbol, _noTrade(df), _SMA(df, len), _TEMA(df, len), _TEMA_SMA(df, len), _MACD(df)]
    rows.append(row)
out_df = pd.DataFrame(rows, columns=['Symbol', '_noTrade', '_SMA', '_TEMA', '_TEMA_SMA', '_MACD'])
print(out_df)
print('Elapsed time:', dt.timedelta(seconds=round(time.time() - t_s)))
