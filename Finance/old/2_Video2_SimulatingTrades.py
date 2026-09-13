import datetime as dt
from pandas_datareader import data as pdr

symbol = 'TQQQ'
start = dt.datetime(2018, 1, 1)
now = dt.datetime.now()
df = pdr.get_data_yahoo(symbol, start, now)

emasUsed = [3, 5, 8, 10, 12, 15, 30, 35, 40, 45, 50, 60]
for x in emasUsed:
    df['Ema_' + str(x)] = round(df['Adj Close'].ewm(span=x, adjust=False).mean(), 2)
df = df.iloc[60:]

pos = 0
percentChange = []
bsHistory = []
for i in df.index:
    shortTermMin = min(df['Ema_3'][i], df['Ema_5'][i], df['Ema_8'][i], df['Ema_10'][i], df['Ema_12'][i],
                       df['Ema_15'][i])
    longTermMax = max(df['Ema_30'][i], df['Ema_35'][i], df['Ema_40'][i], df['Ema_45'][i], df['Ema_50'][i],
                      df['Ema_60'][i])
    close = round(df['Adj Close'][i], 2)
    if (shortTermMin > longTermMax):
        if (pos == 0):
            buyPrice = close
            print(i.strftime('%Y-%m-%d'), 'Buying  at', buyPrice)
            pos = 1
            bsHistory.append(buyPrice)
    elif (shortTermMin < longTermMax):
        if (pos == 1):
            sellPrice = close
            print(i.strftime('%Y-%m-%d'), 'Selling at', sellPrice)
            pos = 0
            bsHistory.append(sellPrice)
            pc = round((sellPrice / buyPrice - 1) * 100, 2)
            percentChange.append(pc)

# sell the last time
if (pos == 1):
    sellPrice = round(df['Adj Close'][-1], 2)
    print(i.strftime('%Y-%m-%d'), 'Last Selling at', sellPrice)
    bsHistory.append(sellPrice)
    pc = round((sellPrice / buyPrice - 1) * 100, 2)
    percentChange.append(pc)

print(percentChange)

totalR = 1
for i in percentChange:
    totalR = totalR * ((i / 100) + 1)

print(round((totalR - 1) * 100, 2), '% Total return over', len(percentChange), 'trades')
# print(str(round((totalR - 1) * 100, 2)) + '% Total return over ' + str(len(percentChange)) + ' trades')
# print(str(round((bsHistory[-1] - bsHistory[0]) * 100 / bsHistory[0], 2)) + '% Total return no trades')
print(round((bsHistory[-1] - bsHistory[0]) * 100 / bsHistory[0], 2), '% Total return no trades')
