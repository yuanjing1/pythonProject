import datetime as dt
import re
from datetime import date
import pandas as pd

def calc_rate(cost, symbol_to):
    if not symbol_to.strip():
        return
    symbolOp = re.split(r'([\d.]+)', symbol_to)
    final_value = float(symbolOp[3])
    final_date = dt.datetime.strptime(str(int(symbolOp[1])), '%y%m%d').date()
    days_hold = (final_date - date.today()).days
    rate_of_gain = float(cost) / final_value * (365 / days_hold) * 100
    return symbol_to + " " + str(round(rate_of_gain))

df = pd.read_csv(r'G:\My Drive\data\out_fidelity.csv')
df = df.dropna(subset=['TEMA_seq'])
df = df[(df['gainLoss'] == 'sell') | (df['gainLoss'] == 'buy')]
for i in df.index:
    try:
        df.loc[i, 'comments'] = calc_rate(df['pct'][i], df['TEMA_seq'][i])
    except Exception as e:
        print(i, e)
df[['Account', 'Symbol', 'sell', 'pct', 'comments', 'gainLoss']]