
import datetime as dt
import pandas as pd
from pandas_datareader import data as pdr
import yfinance as yf
from tkinter import Tk
from tkinter.filedialog import askopenfilename



yf.pdr_override() # <== that's all it takes :-)
start =dt.datetime(2017,12,1)
now = dt.datetime.now()

# root = Tk()
# ftypes = [(".xlsm","*.xlsx",".xls")]
# ttl  = "Title"
# dir1 = 'C:\\'
# filePath = askopenfilename(filetypes = ftypes, initialdir = dir1, title = ttl)
filePath=r"C:\Users\richard\Documents\KIW\Twitter\1-24-2020\RichardStocks.xlsx"


stocklist = pd.read_excel(filePath)
stocklist=stocklist.head()
#print(stocklist)

exportList= pd.DataFrame(columns=['Stock', "RS_Rating", "50 Day MA", "150 Day Ma", "200 Day MA", "52 Week Low", "52 week High"])


for i in stocklist.index:
	# symbol=str(stocklist["Symbol"][i])
	# RS_Rating=stocklist["RS Rating"][i]
	try:
		df = pdr.get_data_yahoo(stock, start, now)

		print("Checking "+stock+".....")

		#Condition 1: Current Price > 150 SMA and > 200 SMA
		#Condition 2: 150 SMA and > 200 SMA
		#Condition 3: 200 SMA trending up for at least 1 month (ideally 4-5 months)
		#Condition 4: 50 SMA> 150 SMA and 50 SMA> 200 SMA
		#Condition 5: Current Price > 50 SMA
		#Condition 6: Current Price is at least 30% above 52 week low (Many of the best are up 100-300% before coming out of consolidation)
		#Condition 7: Current Price is within 25% of 52 week high
		#Condition 8: IBD RS rating >70 and the higher the better
		
		#exportList = exportList.append({'Stock': symbol, "RS_Rating": RS_Rating, "50 Day MA": moving_average_50, "150 Day Ma": moving_average_150, "200 Day MA": moving_average_200, "52 Week Low": low_of_52week, "52 week High": high_of_52week}, ignore_index=True)
	
	except Exception:
		print("No data on "+stock)

print(exportList)
