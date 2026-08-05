import datetime as dt

import matplotlib.pyplot as plt
from pandas_datareader import data as pdr

# Get the stocks
symbol = 'AAPL'
start = dt.datetime(2021, 1, 1)
now = dt.datetime.now()

df = pdr.get_data_yahoo(symbol, start, now)

# plot the graph
plt.style.use('fivethirtyeight')
plt.figure(figsize=(12.2, 4.5))  # width = 12.2in, height = 4.5
plt.plot(df['Adj Close'], label='Close')  # plt.plot( X-Axis , Y-Axis, line_width, alpha_for_blending,  label)
plt.xticks(rotation=45)
plt.title('Close Price History')
plt.xlabel('Date', fontsize=18)
plt.ylabel('Price USD ($)', fontsize=18)
plt.show()
