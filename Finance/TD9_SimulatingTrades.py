import datetime as dt
import time

import pandas as pd
from pandas_datareader import data as pdr

t_s = time.time()
stockList = ['FCEL', 'SPY', 'NVDA']  # , 'TQQQ',  'INTC'

start = dt.datetime(2019, 1, 1)
now = dt.datetime.now()


def _noTrade(df):
    return round((df['Adj Close'][-1] - df['Adj Close'][0]) * 100 / df['Adj Close'][0], 2)


def _sim_TD9(df):
    pos = 0
    cntDT9 = 0
    upSeq = 0
    dnSeq = 0
    closePrice = [0] * 5
    balance = 100
    for i in df.index:
        close = round(df['Adj Close'][i], 2)
        closePrice[0] = closePrice[1]
        closePrice[1] = closePrice[2]
        closePrice[2] = closePrice[3]
        closePrice[3] = closePrice[4]
        closePrice[4] = close
        posChange = 0
        if (closePrice[4] > closePrice[0]):
            upSeq += 1
            dnSeq = 0
            if (upSeq == 9):
                cntDT9 += 1
                posChange = -1
        else:
            upSeq = 0
            dnSeq += -1
            if (dnSeq == -9):
                cntDT9 += -1
                posChange = 1
        pos += posChange
        balance -= close * posChange
    # last day closing, buy back all short positions or sell all long positions
    balance += df['Adj Close'][-1] * pos
    #
    # row = [i, close, -1 * pos, 0, cntDT9, round(balance, 2), upSeq + dnSeq]
    # rows.append(row)
    # out_df = pd.DataFrame(rows, columns=['Date', 'Close', 'posChange', 'pos', 'cntDT9', 'balance', 'seq'])
    # out_df.to_csv('..\data\out_df_' + symbol + '.csv')

    return round((balance - 100), 2)


def _TD9_buyExtra(df, buyExtra):
    rows = []
    pos = 0
    cntDT9 = 0
    upSeq = 0
    dnSeq = 0
    closePrice = [0] * 5
    balance = 100
    for i in df.index:
        close = round(df['Adj Close'][i], 2)
        closePrice[0] = closePrice[1]
        closePrice[1] = closePrice[2]
        closePrice[2] = closePrice[3]
        closePrice[3] = closePrice[4]
        closePrice[4] = close
        posChange = 0
        if (closePrice[4] > closePrice[0]):
            upSeq += 1
            dnSeq = 0
            if (upSeq == 9):
                cntDT9 += 1
                posChange = -1
        else:
            upSeq = 0
            dnSeq += -1
            if (dnSeq == -9):
                cntDT9 += -1
                posChange = 1
                if (pos < 0):
                    posChange = 1 + buyExtra  # FIXME
        pos += posChange
        balance -= close * posChange

        if ((posChange != 0) or (upSeq >= 9) or (dnSeq >= 9)):
            row = [i, close, posChange, pos, cntDT9, round(balance, 2), upSeq + dnSeq]
            rows.append(row)
    # last day closing, buy back all short positions or sell all long positions
    balance += df['Adj Close'][-1] * pos
    return round((balance - 100), 2)


def _TD9_skipSell(df):
    pos = 0
    cntDT9 = 0
    upSeq = 0
    dnSeq = 0
    closePrice = [0] * 5
    balance = 100
    for i in df.index:
        close = round(df['Adj Close'][i], 2)
        closePrice[0] = closePrice[1]
        closePrice[1] = closePrice[2]
        closePrice[2] = closePrice[3]
        closePrice[3] = closePrice[4]
        closePrice[4] = close
        posChange = 0
        if (closePrice[4] > closePrice[0]):
            upSeq += 1
            dnSeq = 0
            if (upSeq == 9):
                cntDT9 += 1
                posChange = -1
                if ((cntDT9 >= 1) and (cntDT9 % 2 == 0)):  # FIXME bullish: skip sell
                    posChange = 0
        else:
            upSeq = 0
            dnSeq += -1
            if (dnSeq == -9):
                cntDT9 += -1
                posChange = 1
        pos += posChange
        balance -= close * posChange
    # last day closing, buy back all short positions or sell all long positions
    balance += df['Adj Close'][-1] * pos
    return round((balance - 100), 2)


def _bear_doubleSell(df):
    pos = 0
    cntDT9 = 0
    upSeq = 0
    dnSeq = 0
    closePrice = [0] * 5
    balance = 100
    for i in df.index:
        close = round(df['Adj Close'][i], 2)
        closePrice[0] = closePrice[1]
        closePrice[1] = closePrice[2]
        closePrice[2] = closePrice[3]
        closePrice[3] = closePrice[4]
        closePrice[4] = close
        posChange = 0
        if (closePrice[4] > closePrice[0]):
            upSeq += 1
            dnSeq = 0
            if (upSeq == 9):
                cntDT9 += 1
                posChange = -1
                if (pos > 0):  # FIXME bearish: double sell
                    posChange = -2 * pos
        else:
            upSeq = 0
            dnSeq += -1
            if (dnSeq == -9):
                cntDT9 += -1
                posChange = 1
        pos += posChange
        balance -= close * posChange

    # last day closing, buy back all short positions or sell all long positions
    balance += df['Adj Close'][-1] * pos
    return round((balance - 100), 2)


def _bear_skipBuy(df):
    pos = 0
    balance = 100
    cntDT9 = 0
    upSeq = 0
    dnSeq = 0
    closePrice = [0] * 5
    for i in df.index:
        close = round(df['Adj Close'][i], 2)
        closePrice[0] = closePrice[1]
        closePrice[1] = closePrice[2]
        closePrice[2] = closePrice[3]
        closePrice[3] = closePrice[4]
        closePrice[4] = close
        posChange = 0
        if (closePrice[4] > closePrice[0]):
            upSeq += 1
            dnSeq = 0
            if (upSeq == 9):
                cntDT9 += 1
                posChange = -1
        else:
            upSeq = 0
            dnSeq += -1
            if (dnSeq == -9):
                cntDT9 += -1
                posChange = 1
                if ((cntDT9 <= -1) and (cntDT9 % 2 == 0)):  # FIXME bearish: skip buy
                    posChange = 0
        pos += posChange
        balance -= close * posChange
    # last day closing, buy back all short positions or sell all long positions
    balance += df['Adj Close'][-1] * pos
    return round((balance - 100), 2)


def _sim_MACD(df):
    ShortEMA = df.Close.ewm(span=12, adjust=False).mean()  # Short Term Exponential Moving Average AKA Fast moving average
    LongEMA = df.Close.ewm(span=26, adjust=False).mean()  # Long Term Exponential Moving Average AKA Slow moving average
    MACD = ShortEMA - LongEMA  # Moving Average Convergence/Divergence
    signal = MACD.ewm(span=9, adjust=False).mean()  # signal line

    df['MACD'] = MACD
    df['Signal Line'] = signal

    flag = -1
    pos = 0
    balance = 100
    rows = []
    for i in df.index:
        posChange = 0
        close = round(df['Adj Close'][i], 2)
        # buy if MACD > signal line else sell
        if df['MACD'][i] > df['Signal Line'][i]:
            if flag != 1:
                flag = 1
                posChange = 1
        elif df['MACD'][i] < df['Signal Line'][i]:
            if flag != 0:
                flag = 0
                posChange = -1
        pos += posChange
        balance -= close * posChange

        if (posChange != 0):
            row = [i, close, posChange, pos, round(balance, 2)]
            rows.append(row)

    row = [i, close, -1 * pos, 0, round(balance, 2)]
    rows.append(row)
    out_df = pd.DataFrame(rows, columns=['Date', 'Close', 'posChange', 'pos', 'balance'])
    out_df.to_csv('..\data\out_df_MACD_' + symbol + '.csv')

    return round((balance - 100), 2)


rows = []
for symbol in stockList:
    df = pdr.get_data_yahoo(symbol, start, now)
    row = [symbol, _noTrade(df), _sim_TD9(df), _TD9_buyExtra(df, 1), _TD9_buyExtra(df, 2), _TD9_buyExtra(df, 3), _sim_MACD(df), _TD9_skipSell(df),
           _bear_doubleSell(df), _bear_skipBuy(df)]
    rows.append(row)
out_df = pd.DataFrame(rows,
                      columns=['Symbol', '_noTrade', 'TD9', 'buyExtra1', 'buyExtra2', 'buyExtra3', 'MACD', 'skipSell', 'doubleSell', 'skipBuy'])

pd.set_option('display.width', 1000)  # display all columns without wrapping
pd.set_option('display.max_columns', None)  # display all columns
print(out_df)

print('Elapsed time:', dt.timedelta(seconds=round(time.time() - t_s)))

