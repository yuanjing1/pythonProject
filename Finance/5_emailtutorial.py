import datetime as dt
import smtplib
import time
from email.message import EmailMessage

from pandas_datareader import data as pdr

EMAIL_ADDRESS = 'yuanjing.xu@gmail.com'  # os.environ.get('EMAIL_USER')
EMAIL_PASSWORD = 'soopayavgpipnlrt'  # os.environ.get('EMAIL_PASS')

msg = EmailMessage()

start = dt.datetime(2020, 12, 1)
now = dt.datetime.now()

stock = 'QQQ'
TargetPrice = 180

msg['Subject'] = 'Alert on ' + stock + '!'
msg['From'] = EMAIL_ADDRESS
msg['To'] = 'yuanjing.xu@gmail.com'

alerted = False
while 1:
    df = pdr.get_data_yahoo(stock, start, now)
    currentClose = round(df['Adj Close'][-1], 2)
    condition = currentClose > TargetPrice
    if (condition and alerted == False):
        alerted = True
        message = stock + ' Has activated the alert price of ' + str(TargetPrice) + \
                  '\nCurrent Price: ' + str(currentClose)
        print(message)
        msg.set_content(message)

        # files = [r'E:\Google Drive\pythonProject\data']
        # for file in files:
        #     with open(file, 'rb') as f:
        #         file_data = f.read()
        #         file_name = 'FundamentalList.xlsx'
        #         msg.add_attachment(file_data, maintype='application',
        #                            subtype='ocetet-stream', filename=file_name)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
            print('Email sent')
    else:
        print('No new alerts')
    time.sleep(60)
