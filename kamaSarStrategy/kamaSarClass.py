import talib as ta
import numpy as np
import pandas as pd

"""
将kdj策略需要用到的信号生成器抽离出来
"""

class kamaSarSignal():

    def __init__(self):
        self.author = 'channel'
        self.kamaList = []
    
    def kamaSignal(self, am, paraDict):
        kamaFastest = paraDict['kamaFastest']
        kamaSlowest = paraDict['kamaSlowest']
        kamaPeriod = paraDict['kamaPeriod']
        smaPeriod = paraDict['smaPeriod']

        if len(self.kamaList)==0:
            self.kamaList.append(ta.MA(am.close, kamaPeriod)[-1])
        elif len(self.kamaList):
            change = np.abs(am.close[kamaPeriod:]-am.close[:-kamaPeriod])
            volatility = ta.SUM(np.abs(am.close[1:]-am.close[:-1]), kamaPeriod)
            er = change[-kamaPeriod:]/volatility[-kamaPeriod:]
            smooth = er[-1]*(2/(kamaFastest+1))+(1-er[-1])*(2/(kamaSlowest+1))
            sc = smooth**2
            newKama = self.kamaList[-1]+sc*(am.close[-1]-self.kamaList[-1])
            self.kamaList.append(newKama)
        if len(self.kamaList)>(kamaPeriod+1):
            self.kamaList.pop(0)
        
        sma = ta.MA(am.close, smaPeriod)
        
        kamaDirection = 0
        if sma[-1]>self.kamaList[-1]:
            kamaDirection = 1
        elif sma[-1]<self.kamaList[-1]:
            kamaDirection = -1
        return kamaDirection, self.kamaList[-1], sma[-1]

    #### 计算DI指标
    def sarSignal(self,am, paraDict):
        sarAcceleration = paraDict['sarAcceleration']
        sar = ta.SAR(am.high, am.low, sarAcceleration)
        if (am.close[-1]>sar[-1]):
            signalDirection = 1
        elif (am.close[-1]<sar[-1]):
            signalDirection = -1
        else:
            signalDirection = 0

        return signalDirection, sar

    def fliterVol(self, am, paraDict):
        volPeriod = paraDict['volPeriod']
        lowVolThreshold = paraDict['lowVolThreshold']

        std = ta.STDDEV(am.close, volPeriod)
        atr = ta.ATR(am.high, am.low, am.close, volPeriod)
        rangeHL = ta.MAX(am.high, volPeriod)-ta.MIN(am.low, volPeriod)
        minVol = min(std[-1], atr[-1], rangeHL[-1])
        lowFilterRange = am.close[-1]*lowVolThreshold
        filterCanTrade = 1 if (minVol >= lowFilterRange) else -1
        return filterCanTrade

    def dsEnv(self, am, paraDict):
        dsPeriod = paraDict['dsPeriod']
        dsSmaPeriod = paraDict['dsSmaPeriod']
        dsLmaPeriod = paraDict['dsLmaPeriod']
        dsthreshold = paraDict['dsThreshold']

        density = (ta.MAX(am.high, dsPeriod)-ta.MIN(am.low, dsPeriod))/ta.SUM(am.high-am.low, dsPeriod)
        dsSma = ta.MA(density, dsSmaPeriod)
        dsLma = ta.MA(density, dsLmaPeriod)

        dsUp = dsSma[-1]>dsLma[-1]
        dsCan = dsSma[-1]>dsthreshold

        preferTrade = dsUp and dsCan
        canTrade = dsCan

        return preferTrade, canTrade, dsSma, dsLma

        