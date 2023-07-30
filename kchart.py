#!/usr/bin/env python3

import psycopg2
import pandas as pd
import mplfinance as mpf
import datetime
import matplotlib.pyplot as plt
import talib
    
conn = psycopg2.connect(
database = "equity_db",
host = "edw.cy1s98bz8vio.ca-central-1.rds.amazonaws.com",
port = 5555,
user = "wealthsigma_etl",
password = "algofamily")
cursor = conn.cursor()

def stock_data(stock, start_date, end_date):
    cursor.execute(f'''
                SELECT security_symbol, open_price, close_price, high_price, low_price, date_key_int, volume
                FROM us_equity_daily_finn
                WHERE security_symbol='{stock}'
                AND date_key_int BETWEEN {start_date} AND {end_date};
                ''')
    df = pd.DataFrame(cursor.fetchall(), columns=['stock', 'Open', 'Close', 'High', 'Low', 'date_key_int', 'Volume'])

    df['date_key_int']=pd.to_datetime(df['date_key_int'],format='%Y%m%d')
    df = df.set_index("date_key_int")
    df.index.name = 'Date'
    return df

def kchart_creator(df):
    add_plot = [mpf.make_addplot(df['UpperB']),
                mpf.make_addplot(df['LowerB']),
                mpf.make_addplot(df['MA20']),
                mpf.make_addplot(df['vwap'], type='line')]
    
    mpf.plot(df,type='candle',title = 'Kchart',
             ylabel = 'PRICE in USD',
             style = 'yahoo',
             addplot = add_plot,
             volume=True)


def Bollinger_band(df):
     df['MA20'] = talib.MA(df['Close'], timeperiod=20)
     stddev = talib.STDDEV(df['Close'], timeperiod=20)
     df['UpperB'] = df['MA20'] + 2 * stddev
     df['LowerB'] = df['MA20'] - 2 * stddev
     return df

def vwap(df):
    v = df['Volume'].values
    tp = (df['Low'] + df['Close'] + df['High']).div(3).values
    return df.assign(vwap=(tp * v).cumsum() / v.cumsum())


def full_chart(stock, start_date, end_date):
    df = stock_data(stock, start_date, end_date)
    df1 = Bollinger_band(df)
    df2 = vwap(df1)

    kchart_creator(df2)
    
