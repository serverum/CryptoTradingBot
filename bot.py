#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import requests
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import copy
import time
import random

from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager
from futures_sign import send_signed_request, send_public_request
from cred import KEY, SECRET


# In[ ]:


symbol='ETHUSDT'
client = Client(KEY, SECRET)

maxposition=0.03
stop_percent=0.01 # 0.01=1%
eth_proffit_array=[[20,1],[40,1],[60,2],[80,2],[100,2],[150,1],[200,1],[200,0]]
proffit_array=copy.copy(eth_proffit_array)

pointer=str(random.randint(1000, 9999))


# In[ ]:


# Get last 500 kandels 5 minutes for Symbol

def get_futures_klines(symbol,limit=500):
    x = requests.get('https://binance.com/fapi/v1/klines?symbol='+symbol+'&limit='+str(limit)+'&interval=5m')
    df=pd.DataFrame(x.json())
    df.columns=['open_time','open','high','low','close','volume','close_time','d1','d2','d3','d4','d5']
    df=df.drop(['d1','d2','d3','d4','d5'],axis=1)
    df['open']=df['open'].astype(float)
    df['high']=df['high'].astype(float)
    df['low']=df['low'].astype(float)
    df['close']=df['close'].astype(float)
    df['volume']=df['volume'].astype(float)
    return(df)


# In[ ]:


# Open position for Sybol with 

def open_position(symbol,s_l,quantity_l):
    prt('open: '+symbol+' quantity: '+str(quantity_l))
    sprice=get_symbol_price(symbol)

    if(s_l=='long'):
        close_price=str(round(sprice*(1+0.01),2))
        params = {
            "batchOrders": [
                {
                    "symbol":symbol,
                    "side": "BUY",
                    "type": "LIMIT",
                    "quantity": str(quantity_l),
                    "timeInForce":"GTC",
                    "price": close_price        

                }
            ]
        }
        responce = send_signed_request('POST', '/fapi/v1/batchOrders', params)
       
       
    if(s_l=='short'):
        close_price=str(round(sprice*(1-0.01),2))
        params = {
            "batchOrders": [
                {
                    "symbol":symbol,
                    "side": "SELL",
                    "type": "LIMIT",
                    "quantity": str(quantity_l),
                    "timeInForce":"GTC",
                    "price": close_price
                }
           ]
        }
        responce = send_signed_request('POST', '/fapi/v1/batchOrders', params)
        


# In[ ]:


# Close position for symbol with quantity

def close_position(symbol,s_l,quantity_l):
    prt('close: '+symbol+' quantity: '+str(quantity_l))

    sprice=get_symbol_price(symbol)

    if(s_l=='long'):
        close_price=str(round(sprice*(1-0.01),2))
        params = {
                    "symbol":symbol,
                    "side": "SELL",
                    "type": "LIMIT",
                    "quantity": str(quantity_l),
                    "timeInForce":"GTC",
                    "price": close_price
                }
        responce = send_signed_request('POST', '/fapi/v1/order', params)
        print (responce)

    if(s_l=='short'):
        close_price=str(round(sprice*(1+0.01),2))
        params = {
                
                    "symbol":symbol,
                    "side": "BUY",
                    "type": "LIMIT",
                    "quantity": str(quantity_l),
                    "timeInForce":"GTC",
                    "price": close_price        
                }
        responce = send_signed_request('POST', '/fapi/v1/order', params)
        print (responce)



# In[ ]:


# Find all opened positions

def get_opened_positions(symbol):
    status = client.futures_account()
    positions=pd.DataFrame(status['positions'])
    a = positions[positions['symbol']==symbol]['positionAmt'].astype(float).tolist()[0]
    leverage = int(positions[positions['symbol']==symbol]['leverage'])
    entryprice = positions[positions['symbol']==symbol]['entryPrice']
    profit = float(status['totalUnrealizedProfit'])
    balance = round(float(status['totalWalletBalance']),2)
    if a>0:
        pos = "long"
    elif a<0:
        pos = "short"
    else: 
        pos = ""
    return([pos,a,profit,leverage,balance,round(float(entryprice),3),0])



# In[ ]:


# Close all orders 

def check_and_close_orders(symbol):
    global isStop 
    a=client.futures_get_open_orders(symbol=symbol)
    if len(a)>0:
        isStop = False
        client.futures_cancel_all_open_orders(symbol=symbol)


# In[ ]:


def get_symbol_price(symbol):
    prices = client.get_all_tickers()
    df=pd.DataFrame(prices)
    return float(df[ df['symbol']==symbol]['price'])


# In[ ]:


# INDICATORS


# In[ ]:


# To find a slope of price line 
def indSlope(series,n):
    
    array_sl = [j*0 for j in range(n-1)]
    
    for j in range(n,len(series)+1):
        y = series[j-n:j]
        x = np.array(range(n))
        x_sc = (x - x.min())/(x.max() - x.min())
        y_sc = (y - y.min())/(y.max() - y.min())
        x_sc = sm.add_constant(x_sc)
        model = sm.OLS(y_sc,x_sc)
        results = model.fit()
        array_sl.append(results.params[-1])
    slope_angle = (np.rad2deg(np.arctan(np.array(array_sl))))
    return np.array(slope_angle)


# In[ ]:


# True Range and Average True Range indicator

def indATR(source_DF,n):
    df = source_DF.copy()
    df['H-L']=abs(df['high']-df['low'])
    df['H-PC']=abs(df['high']-df['close'].shift(1))
    df['L-PC']=abs(df['low']-df['close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].rolling(n).mean()
    df_temp = df.drop(['H-L','H-PC','L-PC'],axis=1)
    return df_temp


# In[ ]:


# find local mimimum / local maximum

def isLCC(DF,i):
    df=DF.copy()
    LCC=0
    
    if df['close'][i]<=df['close'][i+1] and df['close'][i]<=df['close'][i-1] and df['close'][i+1]>df['close'][i-1]:
        #найдено Дно
        LCC = i-1;
    return LCC

def isHCC(DF,i):
    df=DF.copy()
    HCC=0
    if df['close'][i]>=df['close'][i+1] and df['close'][i]>=df['close'][i-1] and df['close'][i+1]<df['close'][i-1]:
        #найдена вершина
        HCC = i;
    return HCC


# In[ ]:



def getMaxMinChannel(DF, n):
    maxx=0
    minn=DF['low'].max()
    for i in range (1,n):
        if maxx<DF['high'][len(DF)-i]:
            maxx=DF['high'][len(DF)-i]
        if minn>DF['low'][len(DF)-i]:
            minn=DF['low'][len(DF)-i]
    return(maxx,minn)


# In[ ]:


# generate data frame with all needed data

def PrepareDF(DF):
    ohlc = DF.iloc[:,[0,1,2,3,4,5]]
    ohlc.columns = ["date","open","high","low","close","volume"]
    ohlc=ohlc.set_index('date')
    df = indATR(ohlc,14).reset_index()
    df['slope'] = indSlope(df['close'],5)
    df['channel_max'] = df['high'].rolling(10).max()
    df['channel_min'] = df['low'].rolling(10).min()
    df['position_in_channel'] = (df['close']-df['channel_min']) / (df['channel_max']-df['channel_min'])
    df = df.set_index('date')
    df = df.reset_index()
    return(df)


# In[ ]:


def check_if_signal(symbol):
    ohlc = get_futures_klines(symbol,100)
    prepared_df = PrepareDF(ohlc)
    signal="" # return value
    
    i=98 # 99 is current kandel which is not closed, 98 is last closed candel, we need 97 to check if it is bottom or top
    
    if isLCC(prepared_df,i-1)>0:
       # found bottom - OPEN LONG
        if prepared_df['position_in_channel'][i-1]<0.5:
            # close to top of channel
            if prepared_df['slope'][i-1]<-20:
                # found a good enter point for LONG
                signal='long'

    if isHCC(prepared_df,i-1)>0:
       # found top - OPEN SHORT
        if prepared_df['position_in_channel'][i-1]>0.5:
            # close to top of channel
            if prepared_df['slope'][i-1]>20:
                # found a good enter point for SHORT
                signal='short'

    return signal
    


# In[ ]:


telegram_delay=12
bot_token=''
chat_id=''

def getTPSLfrom_telegram():
    strr='https://api.telegram.org/bot'+bot_token+'/getUpdates'
    response = requests.get(strr)
    rs=response.json()
    if(len(rs['result'])>0):
        rs2=rs['result'][-1]
        rs3=rs2['message']
        textt=rs3['text']
        datet=rs3['date']

        if(time.time()-datet)<telegram_delay:
            if 'quit' in textt:
                quit()
            if 'exit' in textt:
                exit()
            if 'hello' in textt:
                telegram_bot_sendtext('Hello. How are you?')
            if 'close_pos' in textt:
                position=get_opened_positions(symbol)
                open_sl=position[0]
                quantity=position[1]
              #  print(open_sl,quantity)
                close_position(symbol,open_sl,abs(quantity))
            
def telegram_bot_sendtext(bot_message):
    bot_token2 = bot_token
    bot_chatID = chat_id
    send_text = 'https://api.telegram.org/bot' + bot_token2 + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
    response = requests.get(send_text)
    return response.json()
            


# In[ ]:


def prt(message):
    # telegram message
    telegram_bot_sendtext(pointer+': '+message)
    print(pointer+': '+message)
    


# In[ ]:


def main(step):
    global proffit_array

    try:
        getTPSLfrom_telegram()
        position=get_opened_positions(symbol)
        open_sl=position[0]
        if open_sl=="": # no position
            prt('Нет открытых позиций')
            # close all stop loss orders
            check_and_close_orders(symbol)
            signal=check_if_signal(symbol)
            proffit_array=copy.copy(eth_proffit_array)

            if signal=='long':
                open_position(symbol,'long',maxposition)

            elif signal=='short':
                open_position(symbol,'short',maxposition)
        else:

            entry_price=position[5] # enter price
            current_price=get_symbol_price(symbol)
            quantity=position[1]

            prt('Найдена открытая позиция '+open_sl)
            prt('Кол-во: '+str(quantity))

            if open_sl=='long':
                stop_price=entry_price*(1-stop_percent)
                if current_price<stop_price:
                    #stop loss
                    close_position(symbol,'long',abs(quantity))
                    proffit_array=copy.copy(eth_proffit_array)
                else:
                    temp_arr=copy.copy(proffit_array)
                    for j in range(0,len(temp_arr)-1):
                        delta=temp_arr[j][0]
                        contracts=temp_arr[j][1]
                        if(current_price>(entry_price+delta)):
                        # take profit
                            close_position(symbol,'long',abs(round(maxposition*(contracts/10),3)))
                            del proffit_array[0]

            if open_sl=='short':
                stop_price=entry_price*(1+stop_percent)
                if current_price>stop_price:
                    #stop loss
                    close_position(symbol,'short',abs(quantity))
                    proffit_array=copy.copy(eth_proffit_array)
                else:
                    temp_arr=copy.copy(proffit_array)
                    for j in range(0,len(temp_arr)-1):
                        delta=temp_arr[j][0]
                        contracts=temp_arr[j][1]
                        if(current_price<(entry_price-delta)):
                        # take profit
                            close_position(symbol,'short',abs(round(maxposition*(contracts/10),3)))
                            del proffit_array[0]
      
    except :
        prt('\n\nSomething went wrong. Continuing...')


# In[ ]:


starttime=time.time()
timeout = time.time() + 60*60*12  # 60 seconds times 60 meaning the script will run for 12 hr
counterr=1

while time.time() <= timeout:
    try:
        prt("script continue running at "+time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        main(counterr)
        counterr=counterr+1
        if counterr>5:
            counterr=1
        time.sleep(10 - ((time.time() - starttime) % 10.0)) # 1 minute interval between each new execution
    except KeyboardInterrupt:
        print('\n\KeyboardInterrupt. Stopping.')
        exit()
        

