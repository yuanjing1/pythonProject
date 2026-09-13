import pandas as pd
from yf_pkg import get_ext_price

df = pd.read_csv(r"G:\My Drive\data\out_fidelity.csv")
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
df = df[df['Option'].isna()].head(10) #  Limit to 10 rows for testing

df['CurPrice'] = df['Ticker'].apply(get_ext_price)
df['ref_price'] = df['sell'].combine_first(df['buy']) # Use 'sell' price if available, otherwise use buy column
df['Diff'] = df['CurPrice'] - df['ref_price']

df = df.sort_values('Diff', ascending=False)
df['sell'] = df['sell'].fillna('')
df['strike'] = df['strike'].apply(lambda x: int(x) if pd.notna(x) else '')
print(df[['Ticker', 'strike', 'buy', 'sell', 'CurPrice', 'Diff']])
