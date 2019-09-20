import talib as ta
import numpy as np
import pandas as pd

"""
将kdj策略需要用到的信号生成器抽离出来
"""

class cciSignal():

    def __init__(self):
        self.author = 'channel'

    def maSignal(self, am, paraDict):
        maPeriod = paraDict['maPeriod']
        ma = ta.MA(am.close, maPeriod, 0)
        maDirection = 0
        if am.close[-1]>ma[-1]:
            maDirection = 1
        else:
            maDirection = -1
        return maDirection, ma


    def cciRBreakSignal(self,am, paraDict):
        cciPeriod = paraDict['cciPeriod']
        observedCci = paraDict['observedCci']
        reversedCci = paraDict['reversedCci']
        breakCci = paraDict['breakCci']
        sigPeriod = paraDict['sigPeriod']
        modifyPct = paraDict['modifyPct']

        cciIndicator = ta.CCI(am.high, am.low, am.close, cciPeriod)
        pastCciMax = ta.MAX(cciIndicator, sigPeriod)[-1]
        pastCciMin = ta.MIN(cciIndicator, sigPeriod)[-1]
        maDirection , _ = self.maSignal(am, paraDict)

        if maDirection==1:
            upRevertDn = pastCciMax>observedCci*modifyPct and cciIndicator[-1]<reversedCci*modifyPct
            dnRevertUp = pastCciMin<-observedCci and cciIndicator[-1]>-reversedCci
        elif maDirection==-1:
            upRevertDn = pastCciMax>observedCci and cciIndicator[-1]<reversedCci
            dnRevertUp = pastCciMin<-observedCci*modifyPct and cciIndicator[-1]>-reversedCci*modifyPct
        upBreak = cciIndicator[-1]>breakCci and cciIndicator[-2]<=breakCci
        dnBreak = cciIndicator[-1]<-breakCci and cciIndicator[-2]>=-breakCci
        longSignal, shortSignal = 0, 0
#   
        if dnRevertUp or upBreak:
            longSignal = 1
        if upRevertDn or dnBreak:
            shortSignal = 1
        return longSignal, shortSignal, cciIndicator

    def cciExitSignal(self, am, paraDict):
        cciPeriod = paraDict['cciPeriod']
        tbThreshold = paraDict['tbThreshold']
        sigPeriod = paraDict['sigPeriod']

        cciIndicator = ta.CCI(am.high, am.low, am.close, cciPeriod)
        topRevertDn = (ta.MAX(cciIndicator, sigPeriod)[-1]>tbThreshold) and (cciIndicator[-1]<tbThreshold)
        BottomRevertUp = (ta.MIN(cciIndicator, sigPeriod)[-1]<-tbThreshold) and (cciIndicator[-1]>-tbThreshold)
        longExit, shortExit = 0, 0
        if topRevertDn:
            longExit = 1
        if BottomRevertUp:
            shortExit = 1
        return longExit, shortExit

    def fliterVol(self, am, paraDict):
        volPeriod = paraDict['volPeriod']
        lowVolThreshold = paraDict['lowVolThreshold']
        std = ta.STDDEV(am.close, volPeriod)
        atr = ta.ATR(am.high, am.low, am.close, volPeriod)
        rangeHL = (ta.MAX(am.high, volPeriod)-ta.MIN(am.low, volPeriod))/2
        minVol = min(std[-1], atr[-1], rangeHL[-1])
        lowFilterRange = am.close[-1]*lowVolThreshold
        filterCanTrade = 1 if (minVol >= lowFilterRange) else 0
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

        