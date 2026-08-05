import datetime as dt
import re
from datetime import date

import pandas as pd
import yfinance as yf


def calc_rate(cost, symbol_to):
    if not symbol_to.strip():
        return
    symbolOp = re.split(r'([\d.]+)', symbol_to)
    final_value = float(symbolOp[3])
    final_date = dt.datetime.strptime(str(int(symbolOp[1])), '%y%m%d').date()
    days_hold = (final_date - date.today()).days
    rate_of_gain = float(cost) / final_value * (365 / days_hold) * 100
    return round(rate_of_gain)

print(calc_rate(9.35,'TSLA240920C235'))