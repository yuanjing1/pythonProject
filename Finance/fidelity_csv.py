import re

import numpy as np
import pandas as pd
import pandas as pd
import numpy as np
from pandas import DataFrame

pd.set_option('display.width', 1000)  # display all columns without wrapping
pd.set_option('display.max_columns', None)  # display all columns
pd.set_option('display.max_rows', None)  # display all rows

df = pd.read_csv('C:\\Users\yuanjing\Downloads\\fidelity_8.csv')  # truncated \UXXXXXXXX escape
df = df[df['Quantity'].notnull() & df['Cost Basis Per Share'].notnull()]

# df['Ticker'] = df['Symbol']
# df['ExpirationDate'] = df['Symbol']
# df['Option'] = df['Symbol']
# df['StrikePrice'] = df['Symbol']
# df = df[['Account Name/Number', 'Ticker', 'ExpirationDate', 'Option', 'StrikePrice', 'Quantity', 'Cost Basis Per Share', 'Symbol']]
#
# for i in df.index:
#     df['Symbol'][i] = df['Symbol'][i].replace('-', '')  # chop leading -
#     strArr = re.split('(\d+)', df['Symbol'][i])
#     df['Ticker'][i] = strArr[0]
#     if len(strArr) > 1:
#         df['ExpirationDate'][i] = strArr[1]
#     else:
#         df['ExpirationDate'][i] = np.nan
#     if len(strArr) > 2:
#         df['Option'][i] = strArr[2]
#     else:
#         df['Option'][i] = np.nan
#     if len(strArr) > 3:
#         df['StrikePrice'][i] = strArr[3]
#     else:
#         df['StrikePrice'][i] = np.nan

# df = pd.read_csv('G:\My Drive\data\out_fidelity.csv')
df = df[df['Symbol'].str.startswith('-')]
for i in df.index:
    df['Total Gain/Loss Percent'][i] = df['Total Gain/Loss Percent'][i].strip('"')
df = df.sort_values(by=['Total Gain/Loss Percent'])

# df['Total Gain/Loss Percent'] = df['Total Gain/Loss Percent'].replace('"', '').replace({'\%': ''}, regex=True).replace(',', '')  # .astype(float)
# df = df[df['Total Gain/Loss Percent']>0.5]

# df = df[df['Option'] == 'P']
# df = df[df['Option'].isnull()]

# stockList = df['Ticker'].tolist()
# stockList = list(set(stockList))  # make elements unique
# stockList = sorted(stockList)

print(df)
