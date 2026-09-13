import numpy as np
import pandas as pd
pd.set_option('display.width', 1000)  # display all columns without wrapping
pd.set_option('display.max_columns', None)  # display all columns
pd.set_option('display.max_rows', None)  # display all rows

df = pd.read_csv('G:\My Drive\data\out_fidelity.csv')

df = df[df['Option'] == 'P']
# df = df[df['Option'].isnull()]

# df['buy'] = df['buy'].replace('"', '').replace(',', '').replace({'\$': ''}, regex=True).astype(float)
df['sell'] = df['sell'].replace('"', '').replace(',', '').replace({'\$': ''}, regex=True).astype(float)
df['Quantity'] = df['Quantity'].replace('"', '').replace(',', '').astype(int)

def f(x):
    d = {}
    d['Quantity'] =  x['Quantity'].sum()
    d['Purchase Price'] = (x['Quantity'] * x['buy']).sum() / x['Quantity'].sum()
    # d['Purchase Price'] = (x['Quantity'] * x['sell']).sum() / x['Quantity'].sum()
    return pd.Series(d, index=['Quantity', 'Purchase Price'])


df = df.groupby('Ticker').apply(f)
df.index.name = 'Symbol'
df['Current Price'] = np.nan
df['Date'] = '2021/02/05'
df['Time'] = '10:03'
df['Change'] = np.nan
df['Open'] = np.nan
df['High'] = np.nan
df['Low'] = np.nan
df['Volume'] = np.nan
df['Trade Date'] = np.nan
df['Commission'] = np.nan
df['High Limit'] = np.nan
df['Low Limit'] = np.nan
df['Comment'] = np.nan
df = df[['Current Price', 'Date', 'Time', 'Change', 'Open', 'High', 'Low', 'Volume', 'Trade Date', 'Purchase Price', 'Quantity', 'Commission', 'High Limit', 'Low Limit', 'Comment']]
df = df.sort_values(by='Symbol', ascending=False)

print(df)
df.to_csv('G:\My Drive\data\out_yahoo.csv')
