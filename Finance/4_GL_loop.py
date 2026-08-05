import datetime as dt

import pandas as pd
from pandas_datareader import data as pdr

start = dt.datetime(1980, 12, 1)
now = dt.datetime.now()

symbol = input('Enter a symbol (quit to stop): ')
while symbol != 'quit':
    df = pdr.get_data_yahoo(symbol, start, now)
    df.drop(df[df['Volume'] < 1000].index, inplace=True)  # remove bad data
    dfmonth = round(df.groupby(pd.Grouper(freq='M'))['High'].max(), 2)

    lastGLV = 0
    GLVDate = ''
    curentGLV = 0
    for index, value in dfmonth.items():
        if value > curentGLV:
            curentGLV = value
            GLVDate = index
            counter = 0
        elif value <= curentGLV:
            counter = counter + 1
            if counter == 3 and ((index.month != now.month) or (index.year != now.year)):
                if curentGLV != lastGLV:
                    print(GLVDate.strftime('%Y-%m-%d'), curentGLV)
                lastGLV = curentGLV
                counter = 0
    if lastGLV == 0:
        print(symbol, 'has not formed a green line yet')
    symbol = input('Enter a symbol (quit to stop): ')
