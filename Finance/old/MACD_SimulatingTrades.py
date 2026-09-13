import datetime as dt
import time

import matplotlib.pyplot as plt
import numpy as np
from pandas_datareader import data as pdr

t_s = time.time()

symbol = 'NVDA'
endDate = dt.datetime.now()
startDate = endDate - dt.timedelta(days=620)
print(startDate)
firstBuyDateString = '2020-01-01'
firstBuyDate = dt.datetime.strptime(firstBuyDateString, '%Y-%m-%d')

# plot the graph
# plt.style.use('fivethirtyeight')
# plt.figure(figsize=(12.2, 4.5))  # width = 12.2in, height = 4.5
# plt.plot(df['Adj Close'], label='Close')  # plt.plot( X-Axis , Y-Axis, line_width, alpha_for_blending,  label)
# plt.xticks(rotation=45)
# plt.title('Close Price History')
# plt.xlabel('Date', fontsize=18)
# plt.ylabel('Price USD ($)', fontsize=18)
# plt.show()


def buy_sell_MACD(df):
    # Calculate the MACD and Signal Line indicators
    ShortEMA = df.Close.ewm(span=12, adjust=False).mean()  # Short Term Exponential Moving Average AKA Fast moving average
    LongEMA = df.Close.ewm(span=26, adjust=False).mean()  # Long Term Exponential Moving Average AKA Slow moving average
    MACD = ShortEMA - LongEMA  # Moving Average Convergence/Divergence
    signal = MACD.ewm(span=9, adjust=False).mean()  # signal line

    # Plot the chart
    # plt.figure(figsize=(12.2, 4.5))
    # plt.plot(df.index, MACD, label='AAPL MACD', color='red')
    # plt.plot(df.index, signal, label='Signal Line', color='blue')
    # plt.xticks(rotation=45)
    # plt.legend(loc='upper left')
    # plt.show()

    df['MACD'] = MACD
    df['Signal Line'] = signal

    sigPriceBuy = []
    sigPriceSell = []
    flag = -1
    total = 0
    priceB = 0
    for i in df.index:
        sigPriceB = np.nan
        sigPriceS = np.nan

        # buy the first share
        if (i < firstBuyDate):
            sigPriceBuy.append(sigPriceB)
            sigPriceSell.append(sigPriceS)
            continue
        if (i >= firstBuyDate) & (flag == -1):
            sigPriceB = round(df['Adj Close'][i], 2)
            priceB = sigPriceB
            total -= sigPriceB
            print(i.strftime('%Y-%m-%d'), 'Buying  at', sigPriceB)
            flag = 1

        # buy if MACD > signal line else sell
        if df['MACD'][i] >= df['Signal Line'][i]:
            if flag != 1:
                sigPriceB = round(df['Adj Close'][i], 2)
                priceB = sigPriceB
                total -= sigPriceB
                print(i.strftime('%Y-%m-%d'), 'Buying  at', sigPriceB)
                flag = 1
        elif df['MACD'][i] < df['Signal Line'][i]:
            if flag != 0:
                sigPriceS = round(df['Adj Close'][i], 2)
                total += sigPriceS
                print(i.strftime('%Y-%m-%d'), 'Selling  at', sigPriceS, round((sigPriceS - priceB) / priceB * 100, 2), '%')
                flag = 0
        sigPriceBuy.append(sigPriceB)
        sigPriceSell.append(sigPriceS)
    # sell the last share
    if flag != 0:
        sigPriceS = round(df['Adj Close'][i], 2)
        total += sigPriceS
        print(i.strftime('%Y-%m-%d'), 'Selling  at', sigPriceS, round((sigPriceS - priceB) / priceB * 100, 2), '%')
    print(round(total, 2))
    return (sigPriceBuy, sigPriceSell)


df = pdr.get_data_yahoo(symbol, startDate, endDate)
x = buy_sell_MACD(df)
df['Buy_Signal_Price'] = x[0]
df['Sell_Signal_Price'] = x[1]
# print(df)
# df.to_csv('..\..\Google Drive\data\out_MACD_' + symbol + '.csv')

# plt.figure(figsize=(12.2, 4.5))
# plt.scatter(df.index, df['Buy_Signal_Price'], color='green', label='Buy Signal', marker='^', alpha=1)
# plt.scatter(df.index, df['Sell_Signal_Price'], color='red', label='Sell Signal', marker='v', alpha=1)
# plt.plot(df['Adj Close'], label='Close Price', alpha=0.35)
# plt.xticks(rotation=45)
# plt.title('Close Price History Buy / Sell Signals')
# plt.xlabel('Date', fontsize=18)
# plt.ylabel('Close Price USD ($)', fontsize=18)
# plt.legend(loc='upper left')
# plt.show()

print('Elapsed time:', dt.timedelta(seconds=round(time.time() - t_s)))
