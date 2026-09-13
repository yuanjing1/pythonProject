import os
import pandas as pd
# resolve from this script's folder, so it runs from any working directory
CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data_save', 'out_fidelity.csv')
df = pd.read_csv(CSV, on_bad_lines='skip')
IS_OPTION = r'^[A-Za-z.]+\d{6}[P][\d.]+$'
df = df[df['Symbol'].notna() & df['Symbol'].astype(str).str.match(IS_OPTION)] # options only
df = df[~df['Quantity'].isin(['sell', 'buy'])]
print(df[['Account', 'Symbol', 'sell']]) #testing