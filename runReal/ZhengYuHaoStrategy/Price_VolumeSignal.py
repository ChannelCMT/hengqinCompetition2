import talib as ta
from talib import MA_Type

"""
交易规则：
捕捉到以下信号时，分别开平仓做多做空：
做多：价格突破布林线上轨且成交量巨大；
做空：价格跌破布林线中轨且成交量巨大；
平仓：
　　多单信号1：价格回归到布林线上轨；
　　多单信号2：价格跌破布林线中轨且成交量巨大；
　　空单信号1：价格恢复至布林线下轨；
　　空单信号2：价格突破布林线中轨且成交量巨大；
"""

class Price_Volume():

    def __init__(self):
        self.author = 'Raingo'

    def PVSignal(self,am,paraDict):
        PERIOD= paraDict["PERIOD"]
        STDUP = paraDict["STDUP"]
        STDDN = paraDict["STDDN"]
        pup,pmid,plow = ta.BBANDS(am.close, timeperiod=PERIOD,nbdevup=STDUP,nbdevdn=STDDN,matype=MA_Type.T3)
        vup,vmid,vlow = ta.BBANDS(am.volume,timeperiod=PERIOD,nbdevup=STDUP,nbdevdn=STDDN,matype=MA_Type.T3)
        Pup,Pmid,Plow=pup[-1],pmid[-1],plow[-1]
        Vup,Vmid,Vlow=vup[-1],vmid[-1],vlow[-1]
        lPup,lPmid,lPlow=pup[-2],pmid[-2],plow[-2]
        
        #----------------------------------------------------------------------
        
        # 多头信号：价格突破布林线上轨且成交量巨大
        Long_1 = am.high[-2]<lPup and am.high[-1]>=Pup and am.volume[-1]>Vmid
        # 空头信号：价格跌破布林线中轨且成交量巨大
        Short_3= am.low[-2]> lPmid and am.low[-1]<= Pmid and am.low[-1]>Plow and am.volume[-1]>Vmid
        
        #----------------------------------------------------------------------
        
        # 多单信号1：价格回归到布林线上轨
        Sell_1 = am.low[-2]> lPup  and am.low[-1]<= Pup
        # 空单信号1：价格恢复至布林线下轨
        Cover_1= am.high[-2]<lPlow and am.high[-1]>=Plow
        
        #----------------------------------------------------------------------
        
        # 多单信号2：价格跌破布林线中轨且成交量巨大
        Sell_2 = am.low[-2]>lPmid  and am.low[-1]<=Pmid  and am.volume[-1]>Vup
        # 空单信号2：价格突破布林线中轨且成交量巨大
        Cover_2= am.high[-2]<lPmid and am.high[-1]>=Pmid and am.volume[-1]>Vup
        
        #----------------------------------------------------------------------
        
        BuySignal = 0
        if Long_1:
            BuySignal = 1
        elif Short_3:
            BuySignal = -1

        SellSignal= 0
        if Sell_1 or Sell_2:
            SellSignal = 1
        elif Cover_1 or Cover_2:
            SellSignal = -1
        
        return am.close[-1],BuySignal,SellSignal,Pup,Pmid,Plow