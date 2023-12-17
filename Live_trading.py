# -*- coding: utf-8 -*-
"""
Created on Fri Dec  1 12:56:23 2023

@author: kisah
"""
import pandas as pd
import numpy as np
import math
from datetime import datetime
from binance import Client
import time
import sys
sys.path.append('C:/Users/kisah/Desktop/Live_trading')
import config


## Create supertrend indicator for strategy
def generateSupertrend(df,close_array, high_array, low_array, atr_period, atr_multiplier):

    ## Truerange calculation for ATR
    df['TR1'] = abs(df['High'] - df['Close'].shift(1))
    df['TR2'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR3'] = abs(df['High'] - df['Low'])
    df['TrueRange'] = df[['TR1', 'TR2', 'TR3']].max(axis=1)
    
    ## applied SMA ATR
    df['TrueRange'] = df['TrueRange'].rolling(atr_period).mean()
    

    ## initialize necessary values
    previous_final_upperband = 0
    previous_final_lowerband = 0
    final_upperband = 0
    final_lowerband = 0
    previous_close = 0
    previous_supertrend = 0
    supertrend = []
    supertrendc = 0

    ## calculation of Supertrend
    for i in range(0, len(close_array)):
        if np.isnan(close_array[i]):
            pass
        else:
            highc = high_array[i]
            lowc = low_array[i]
            atrc = df.loc[i,'TrueRange']
            closec = close_array[i]

            if math.isnan(atrc):
                atrc = 0

            basic_upperband = (highc + lowc + closec) / 3 + atr_multiplier * atrc
            basic_lowerband = (highc + lowc + closec) / 3 - atr_multiplier * atrc

            if basic_upperband < previous_final_upperband or previous_close > previous_final_upperband:
                final_upperband = basic_upperband
            else:
                final_upperband = previous_final_upperband

            if basic_lowerband > previous_final_lowerband or previous_close < previous_final_lowerband:
                final_lowerband = basic_lowerband
            else:
                final_lowerband = previous_final_lowerband

            if previous_supertrend == previous_final_upperband and closec <= final_upperband:
                supertrendc = final_upperband
            else:
                if previous_supertrend == previous_final_upperband and closec >= final_upperband:
                    supertrendc = final_lowerband
                else:
                    if previous_supertrend == previous_final_lowerband and closec >= final_lowerband:
                        supertrendc = final_lowerband
                    elif previous_supertrend == previous_final_lowerband and closec <= final_lowerband:
                        supertrendc = final_upperband

            supertrend.append(supertrendc)

            previous_close = closec

            previous_final_upperband = final_upperband

            previous_final_lowerband = final_lowerband

            previous_supertrend = supertrendc
       
    ## drop unnecessary columns, add supertrend as column, drop first 50 data for unbalanced ATR
    df = df.drop(columns=['TR1','TR2','TR3','TrueRange'])
    df['Supertrend'] = supertrend
    df = df.reset_index(drop=True)
    return df

def sendLong(client,symbol, quantity,price):
    try:
        order = client.futures_create_order(
            symbol=symbol,
            side='BUY',
            type='LIMIT',
            quantity=quantity,
            price=price,
            timeInForce='GTC',
        )
        print(f"Buy order placed successfully: {order}")
    except Exception as e:
        print(f"Error placing buy order: {e}")

    return order

def sendLongStop(client,symbol, quantity,price):
    try:
        order = client.futures_create_order(
            symbol=symbol,
            side='SELL',
            type='STOP',
            quantity=quantity,
            price=price,
            stopPrice=price,
            timeInForce='GTC'
        )
        print(f"Buy order placed successfully: {order}")
    except Exception as e:
        print(f"Error placing buy order: {e}")

    return order

def sendLongStopUpdate(client,symbol, quantity,price,orderId):
    try:
        client.futures_cancel_order(
            symbol=symbol,
            orderId=orderId,
        )
        
        order = client.futures_create_order(
            symbol=symbol,
            side='SELL',
            type='STOP',
            quantity=quantity,
            price=price,
            stopPrice=price,
            timeInForce='GTC'
        )
        print(f"Buy order placed successfully: {order}")
    except Exception as e:
        print(f"Error placing buy order: {e}")

    return order

def sendShort(client,symbol, quantity,price):
    try:
        order = client.futures_create_order(
            symbol=symbol,
            side='SELL',
            type='LIMIT',
            quantity=quantity,
            price=price,
            timeInForce='GTC'
        )
        print(f"Buy order placed successfully: {order}")
    except Exception as e:
        print(f"Error placing buy order: {e}")

    return order


def sendShortStop(client,symbol, quantity,price):
    try:
        order = client.futures_create_order(
            symbol=symbol,
            side='BUY',
            type='STOP',
            quantity=quantity,
            price=price,
            stopPrice=price,
            timeInForce='GTC'
        )
        print(f"Buy order placed successfully: {order}")
    except Exception as e:
        print(f"Error placing buy order: {e}")

    return order

def sendShortStopUpdate(client,symbol, quantity,price,orderId):
    try:
        client.futures_cancel_order(
            symbol=symbol,
            orderId=orderId,
        )
        
        order = client.futures_create_order(
            symbol=symbol,
            side='BUY',
            type='STOP',
            quantity=quantity,
            price=price,
            stopPrice=price,
            timeInForce='GTC'
        )
        print(f"Buy order placed successfully: {order}")
    except Exception as e:
        print(f"Error placing buy order: {e}")

    return order

col_names = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'volume', 'closeTime', 'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol', 'takerBuyQuoteVol', 'ignore']


## you should change api_key and api_secret.
client = Client(config.API_KEY, config.API_SECRET)

symbol = 'BTCUSDT'
last_minute = '61'
interval = Client.KLINE_INTERVAL_15MINUTE
is_open = 0
stop_loss = 0
period = 10
multiplier = 5
trade_amount = 300

df_temp = pd.DataFrame()
order_list_buy = []
order_list_sell = []
stop_list_buy = []
stop_list_sell = []
stop_update_list_buy = []
stop_update_list_sell = []
stop_occur_list_buy = []
stop_occur_list_sell = []

while True:
    
    current_second = datetime.now().strftime('%S')
    current_minute = datetime.now().strftime('%M')
    
    if(current_second == '02' and current_minute != last_minute and int(current_minute) % 15 == 0):
        last_minute = current_minute
        if(len(df_temp) == 0):
            while True:
                last_candlestick = client.futures_klines(symbol=symbol, interval=interval, limit=period + 150)
                df = pd.DataFrame(last_candlestick, columns=col_names)
                df['Date'] = df['Timestamp'].apply(lambda x: datetime.fromtimestamp(x / 1000))
                df['Timestamp'] = pd.to_datetime(df['Date'])

                for column in df.columns:
                    if df[column].dtype == 'object':  # Check if the column contains objects (strings)
                        df[column] = df[column].astype(float)
        
                df = df.drop(columns = ['Date','closeTime','quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol', 'takerBuyQuoteVol', 'ignore'])        
                df = generateSupertrend(df.copy(), df['Close'].copy(), df['High'].copy(), df['Low'].copy(), period, multiplier)  
                if(df['Timestamp'].iloc[-1].minute == int(last_minute)):
                    break
        
        if(len(df_temp) != 0 and df_temp['Timestamp'].iloc[-1] == df['Timestamp'].iloc[-1]):
            while True:
                last_candlestick = client.futures_klines(symbol=symbol, interval=interval, limit=period + 150)
                df = pd.DataFrame(last_candlestick, columns=col_names)
                df['Date'] = df['Timestamp'].apply(lambda x: datetime.fromtimestamp(x / 1000))
                df['Timestamp'] = df['Date']
                
                for column in df.columns:
                    if df[column].dtype == 'object':  # Check if the column contains objects (strings)
                        df[column] = df[column].astype(float)

                df = df.drop(columns = ['Date','closeTime','quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol', 'takerBuyQuoteVol', 'ignore'])        
                df = generateSupertrend(df.copy(), df['Close'].copy(), df['High'].copy(), df['Low'].copy(), period, multiplier)   
                if(df_temp['Timestamp'].iloc[-1] != df['Timestamp'].iloc[-1]):
                    break
        
        close_nan_set = df.iloc[-1]['Open'].copy()
        df['Close'] = df['Open'].shift(-1).copy()
        df.iloc[-1, df.columns.get_loc('Close')] = close_nan_set
        df_temp = df.copy()
        
        if(df_temp.iloc[-2]['Supertrend'] > df_temp.iloc[-2]['Open'] and df_temp.iloc[-3]['Supertrend'] < df_temp.iloc[-3]['Open']):
            stop_loss = 0
            is_open = 0
        if(df_temp.iloc[-2]['Supertrend'] < df_temp.iloc[-2]['Open'] and df_temp.iloc[-3]['Supertrend'] > df_temp.iloc[-3]['Open']):
            is_open = 0
            stop_loss = 0
        
        if(is_open == 0):
            last_price = df_temp.iloc[-1]['Close']
            quantity = round(trade_amount/last_price,3)
            
            if(df_temp.iloc[-2]['Open'] >= df_temp.iloc[-2]['Supertrend']):
                is_open = 1
                trade = sendLong(client, symbol, quantity, round(last_price * 1.001,1))
                stop = sendLongStop(client,symbol,quantity,round(df_temp.iloc[-2]['Supertrend'],1))
                order_list_buy.append(trade)
                stop_list_buy.append(stop)
            elif(df_temp.iloc[-2]['Open'] <= df_temp.iloc[-2]['Supertrend']):
                is_open = -1
                trade = sendShort(client, symbol, quantity, round(last_price * 0.999,1))
                stop = sendShortStop(client,symbol,quantity,round(df_temp.iloc[-2]['Supertrend'],1))
                order_list_sell.append(trade)
                stop_list_sell.append(stop)
                
        elif(is_open == 1):
            if(df_temp.iloc[-2]['Low'] > df_temp.iloc[-2]['Supertrend']):
                order_is_stopped = 0
                open_orders = client.futures_get_open_orders()
                for order_counter in range(0,len(open_orders)):
                    if(stop['orderId'] == open_orders[order_counter]['orderId']):
                        order_is_stopped = 1
                        
                if(order_is_stopped == 0):
                    stop_occur_list_buy.append(df_temp.iloc[-2])
                    stop_loss = 1
                
            if(df_temp.iloc[-3]['Supertrend'] != df_temp.iloc[-2]['Supertrend'] and stop_loss == 0):
                stop = sendLongStopUpdate(client,symbol,quantity,round(df_temp.iloc[-2]['Supertrend'],1),stop['orderId'])
                stop_update_list_buy.append(stop)
            
        elif(is_open == -1):
            if(df_temp.iloc[-2]['High'] > df_temp.iloc[-2]['Supertrend']):
                order_is_stopped = 0
                open_orders = client.futures_get_open_orders()
                for order_counter in range(0,len(open_orders)):
                    if(stop['orderId'] == open_orders[order_counter]['orderId']):
                        order_is_stopped = 1
                        
                if(order_is_stopped == 0):
                    stop_occur_list_sell.append(df_temp.iloc[-2])
                    stop_loss = 1
                
            if(df_temp.iloc[-3]['Supertrend'] != df_temp.iloc[-2]['Supertrend'] and stop_loss == 0):
                stop = sendShortStopUpdate(client,symbol,quantity,round(df_temp.iloc[-2]['Supertrend'],1),stop['orderId'])   
                stop_update_list_sell.append(stop)
            
        
        current_time = datetime.now().strftime('%H:%M:%S.%f')
        print(current_time)
        time.sleep(60*15 - 15)
