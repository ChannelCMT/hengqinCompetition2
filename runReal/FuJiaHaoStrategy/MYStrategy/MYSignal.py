import talib as ta
import numpy as np
import pandas as pd

"""
先计算cmi判断当前市场是处于趋势还是震荡调整，趋势采用海归交易策略。调整采用压力线与支撑线。
"""

class mySignal():

    def __init__(self):
        self.author = 'FJH'
    
    def Signal(self,am,paraDict):
        macdPeriod = paraDict["macdPeriod"]
        macdsignalPeriod = paraDict["macdsignalPeriod"]
        macdhistPeriod = paraDict["macdhistPeriod"]

        macd, macdsignal, macdhist = ta.MACD(am.close,macdPeriod,macdsignalPeriod,macdhistPeriod)

        maSignal = 0
        if macd[-1]>0 and macd[-2]<0 and macdsignal[-1]>macdsignal[-3] and macd[-1]>macd[-3] :#and atrma1[-1] > atrma2[-2]:
            maSignal = 1
        elif macd[-1]>0 and macd[-2]<0 and macdsignal[-1]>macdsignal[-3] and macd[-1]>macd[-3] : #and atrma1[-1] > atrma2[-2]:
            maSignal = -1
        else:
            maSignal = 0

        return maSignal, macd, macdsignal, macdhist

    def ATR(self,am,paraDict):
        atrPeriod = paraDict["atrPeriod"]
        atr = ta.ATR(am.high,am.low,am.close,atrPeriod)
        
        return atr

    def stopwin(self,am,paraDict):
        stopwinPeriod = paraDict["stopwinPeriod"]
        longwinPrice = ta.MA((3*am.high+am.low+2*am.close)/6, stopwinPeriod)[-1]
        shortwinPrice = ta.MA((am.high+3*am.low+2*am.close)/6, stopwinPeriod)[-1]
        
        return longwinPrice, shortwinPrice


    
 




