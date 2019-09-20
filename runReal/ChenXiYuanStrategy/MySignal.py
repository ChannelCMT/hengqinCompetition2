import talib as ta
import numpy as np
import pandas as pd

"""
将策略需要用到的信号生成器抽离出来
"""

class MySignal():

    def __init__(self):
        self.author = 'Shinie Zen'

    def KMA(self, am, period):

        highEMA=ta.EMA(am.high, period)
        lowEMA=ta.EMA(am.low,period)

        return highEMA, lowEMA

    def getATR(self,am,paraDict):

        atrPeirod=paraDict['atrPeriod']

        atr = ta.ATR(am.high, am.low, am.close, atrPeirod)

        return atr[-1]

    def KMASignal(self, am, paraDict):

        fastPeriod = paraDict['fastPeriod']
        slowPeriod = paraDict['slowPeriod']
        slowPeriod2 = paraDict['slowPeriod2']

        slowHigh, slowLow=self.KMA(am,slowPeriod)
        slowHigh2, slowLow2=self.KMA(am,slowPeriod2)
        fastHigh, fastLow=self.KMA(am,fastPeriod)

        tradeSignal=0

        if fastHigh[-1]<slowLow[-1] and fastHigh[-1]<slowHigh2[-1]:
            tradeSignal=-1
        elif fastLow[-1]>slowHigh[-1] and fastLow[-1]>slowLow2[-1]:
            tradeSignal=1

        return tradeSignal, fastHigh[-1], fastLow[-1], slowHigh[-1], slowLow[-1]

    def CBSignal(self, am, paraDict):

        channelPeriod = paraDict['channelPeriod']

        highMax = am.high[-channelPeriod-1:-2].max()
        lowMin = am.low[-channelPeriod-1:-2].min()

        signal=0

        if am.close[-1]>highMax:
            signal=1
        elif am.close[-1]<lowMin:
            signal=-1
        
        return signal, highMax, lowMin

    def entrySignal(self, am, paraDict):

        atr = self.getATR(am, paraDict)

        KMASignal, fastHigh, fastLow, slowHigh, slowLow = self.KMASignal(am, paraDict)
        CBSignal, highMax, lowMin = self.CBSignal(am, paraDict)

        tradeSignal = 0

        if KMASignal==CBSignal: 
            tradeSignal = CBSignal
        #else: 
        #    tradeSignal = -CBSignal

        return tradeSignal, fastHigh, fastLow, slowHigh, slowLow, highMax, lowMin, atr, am.close[-1]


    def exitSignal(self, am, paraDict): 
        
        fastPeriod = paraDict['fastPeriod']
        slowPeriod2 = paraDict['slowPeriod2']

        slowHigh2, slowLow2=self.KMA(am,slowPeriod2)
        fastHigh, fastLow=self.KMA(am,fastPeriod)

        shortExitSignal = 0
        longExitSignal = 0

        if fastHigh[-1]>slowHigh2[-1]:
            shortExitSignal = 1
        if fastLow[-1]<slowLow2[-1]:
            longExitSignal = -1

        return shortExitSignal, longExitSignal, slowHigh2[-1], slowLow2[-1]



        