import datetime as dt
import time

import pandas as pd
from pandas import DataFrame
from pandas_datareader import data as pdr
from pytickersymbols import PyTickerSymbols
import yfinance as yf
import contextlib
import io

yf.pdr_override()
pd.options.mode.chained_assignment = None  # default='warn'

t_s = time.time()

x = 20
limitDay = 3
DIR = '..\..\Google Drive\data'


def _MA_screen(symbol, df, x):
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

    # reverse up/down
    df['SMA_up_1'] = df.SMA_up.shift(1)
    df['TEMA_up_1'] = df.TEMA_up.shift(1)
    df = df.dropna(subset=['SMA', 'SMA_2', 'TEMA', 'TEMA_2', 'SMA_up_1', 'TEMA_up_1'])
    df['SMA_up_rev'] = df.apply(lambda x: x['SMA_up'] if x['SMA_up'] != x['SMA_up_1'] else '', axis=1)
    df['TEMA_up_rev'] = df.apply(lambda x: x['TEMA_up'] if x['TEMA_up'] != x['TEMA_up_1'] else '', axis=1)

    SMA_seq = ''
    TEMA_seq = ''
    seq = 0
    for i in df.index[::-1]:  # look backwards
        seq += 1
        if bool(SMA_seq) & bool(TEMA_seq):
            break
        if (not SMA_seq) & bool(df['SMA_up_rev'][i]):
            SMA_seq = df['SMA_up_rev'][i] + str(seq)
        if (not TEMA_seq) & bool(df['TEMA_up_rev'][i]):
            TEMA_seq = df['TEMA_up_rev'][i] + str(seq)
    return [symbol, TEMA_seq, SMA_seq]


def _MA_screen_list(stockList, x, filename):
    stockList = list(set(stockList))  # make elements unique
    stockList = sorted(stockList)
    rows = []
    for symbol in stockList:
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                df_yh = pdr.get_data_yahoo(symbol, period='120d')
            row = _MA_screen(symbol, df_yh, x)
            rows.append(row)
        except Exception:
            print(symbol)
    out_df = pd.DataFrame(rows, columns=['symbol', 'TEMA_seq', 'SMA_seq'])
    out_df = out_df.sort_values(by=['TEMA_seq', 'SMA_seq'])
    print(out_df)
    out_df.to_csv(DIR + filename, index=False)

def _pickUpDn(limitDay, filename):
    out_df = pd.read_csv(DIR + filename)
    today = dt.datetime.now().strftime('%d')
    upList = out_df[(0 <= out_df['TEMA_seq']) & (out_df['TEMA_seq'] <= limitDay)]  # & (out_df['SMA_seq'] < -9)
    print(upList)
    upList['symbol'].to_csv('..\data\out_PythonRevUp' + today + '.txt', index=False, header=False)

    dnList = out_df[(-limitDay <= out_df['TEMA_seq']) & (out_df['TEMA_seq'] <= 0)]  # & (out_df['SMA_seq'] > 9)
    print(dnList)
    dnList['symbol'].to_csv('..\data\out_PythonRevDn' + today + '.txt', index=False, header=False)


# print('--- Scan')
# df = pd.read_csv('..\data\in_stockList.csv', sep='[";"]', engine='python')  # 174 0:01:55 | 0:03:52
# stockList = []
# for i in df.index:
#     symbolList = df['Symbol'][i]
#     for x in symbolList.split(','):
#         stockList.append(x.split(':')[-1])
# filename = '\out_Python_MA.csv'
# _MA_screen_list(stockList, x, filename)
# _pickUpDn(limitDay, filename)

stock_data = PyTickerSymbols()
lst = stock_data.get_stocks_by_index('DOW JONES')  # NASDAQ 100 [98 x 10] 06:48 | S&P 500 [491 x 10] 10:34 | DOW JONES 30 04:24
df = DataFrame(lst)
stockList = df['symbol'].tolist()  # get list from a column
filename = '\out_Python_MA_SP.csv'
_MA_screen_list(stockList, x, filename)
# _pickUpDn(limitDay, filename)

print('Elapsed time:', dt.timedelta(seconds=round(time.time() - t_s)))
