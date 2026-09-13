# Tom DeMARK TD9 indicator
import datetime as dt
import time

import numpy as np
import pandas as pd
from pandas import DataFrame
from pandas_datareader import data as pdr
from pytickersymbols import PyTickerSymbols

t_s = time.time()

endDate = dt.datetime.now()
startDate = endDate - dt.timedelta(days=30)

df = pd.read_csv('..\data\in_stockList.csv', sep='[";"]', engine='python')  # 174 0:01:55 | 0:03:52
stockList = []
for i in df.index:
    symbolList = df['Symbol'][i]
    for x in symbolList.split(','):
        stockList.append(x.split(':')[-1])

# df = pd.read_csv('G:\My Drive\data\out_fidelity.csv')
# stockList = df['Ticker'].tolist()

# stock_data = PyTickerSymbols()
# lst = stock_data.get_stocks_by_index('S&P 500')  # NASDAQ 100 [98 x 10] 191 | S&P 500 [491 x 10] 847 | DOW JONES 30 37
# df = DataFrame(lst)
# stockList = df['symbol'].tolist()  # get list from a column

# stockList = ['FCEL', 'NVDA', 'TQQQ', 'SPY', 'INTC', 'SPCE', 'NUGT', 'AAPL']
stockList = list(set(stockList))  # make elements unique
stockList = sorted(stockList)


def _TD9_screen(df, seq, upSeq, dnSeq):
    closePrice = [0] * 5
    for i in df.index[::-1]:  # look backwards
        close = round(df['Adj Close'][i], 2)
        closePrice[0] = closePrice[1]
        closePrice[1] = closePrice[2]
        closePrice[2] = closePrice[3]
        closePrice[3] = closePrice[4]
        closePrice[4] = close
        if (closePrice[0] == 0):  # skip the first 4 rows
            continue
        if (closePrice[4] < closePrice[0]):
            if (upSeq == 0):  # trend reverse
                if (seq == 0):
                    seq = dnSeq
                else:
                    break
            upSeq += 1
            dnSeq = 0
        else:
            if (dnSeq == 0):
                if (seq == 0):
                    seq = upSeq
                else:
                    break
            upSeq = 0
            dnSeq += -1
    return [symbol, dnSeq + upSeq, seq]


rows = []
for symbol in stockList:
    try:
        df = pdr.get_data_yahoo(symbol, startDate, endDate)
        row = _TD9_screen(df, 0, 0, 0)
        rows.append(row)
    except Exception:
        print(symbol)
out_df = pd.DataFrame(rows, columns=['symbol', 'prevSeq', 'seq'])
out_df = out_df.loc[out_df['seq'] != 0]
out_df.to_csv('..\..\Google Drive\data\out_PythonScreen.csv', index=False)


def _pickUpDn(limitDay):
    out_df = pd.read_csv('..\..\Google Drive\data\out_PythonScreen.csv')
    endDate = dt.datetime.now()
    upList = out_df[(out_df['seq'] == 1) & (abs(out_df['prevSeq']) >= limitDay)]
    print(upList)
    upList['symbol'].to_csv('..\data\out_PythonRevUp' + endDate.strftime('%d') + '.txt', index=False, header=False)

    dnList = out_df[(out_df['seq'] == -1) & (abs(out_df['prevSeq']) >= limitDay)]
    print(dnList)
    dnList['symbol'].to_csv('..\data\out_PythonRevDn' + endDate.strftime('%d') + '.txt', index=False, header=False)


_pickUpDn(0)
print('Elapsed time:', dt.timedelta(seconds=round(time.time() - t_s)))
