import datetime as dt
import datetime as dt
import time
from yahoo_fin import stock_info as si
import numpy as np
import pandas as pd
from pandas import DataFrame
from pandas_datareader import data as pdr
from pytickersymbols import PyTickerSymbols

from pandas_datareader import data as pdr

t_s = time.time()
endDate = dt.datetime.now()
startDate = endDate - dt.timedelta(days=30)

def _pickUpDn(limitDay):
    out_df = pd.read_csv('..\..\Google Drive\data\out_PythonScreen.csv')
    endDate = dt.datetime.now()
    upList = out_df[(out_df['seq'] == 1) & (abs(out_df['prevSeq']) >= limitDay)]
    print(upList)
    upList['symbol'].to_csv('..\data\out_PythonRevUp' + endDate.strftime('%d') + '.txt', index=False, header=False)

    dnList = out_df[(out_df['seq'] == -1) & (abs(out_df['prevSeq']) >= limitDay)]
    print(dnList)
    dnList['symbol'].to_csv('..\data\out_PythonRevDn' + endDate.strftime('%d') + '.txt', index=False, header=False)

_pickUpDn(6)

# exportList = pd.DataFrame(columns=['symbol', 'RS Rating'])  # column header
# for i in df.index:
#     symbol = str(df['symbol'][i])
#     RS_Rating = df['RS Rating'][i]
#     exportList = exportList.append({'symbol': symbol, 'RS Rating': RS_Rating}, ignore_index=True)
# print(exportList)

# start = dt.datetime(2010, 6, 29)
# endDate = dt.datetime.now()
# symbol = 'TSLA' #[2743 rows x 7 columns]
# df = si.get_data(symbol)
# print(df.loc[df.index == '2021-05-21'])

# df = pdr.get_data_yahoo('TSLA', startDate, endDate)
# for i in df.index[::-1]:
#     print(df.loc[i])

print('Elapsed time:', dt.timedelta(seconds=round(time.time() - t_s)))
