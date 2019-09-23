import talib as ta
import numpy as np
import pandas as pd

"""
将kdj策略需要用到的信号生成器抽离出来
"""

class hlBreakSignal():

    def __init__(self):
        self.strategyName = 'hlBreakSignal'

    #### 计算ADX指标
    def adxEnv(self,am,paraDict):
        adxPeriod = paraDict["adxPeriod"]
        adxMaxPeriod = paraDict["adxMaxPeriod"]
        adxHighThreshold = paraDict["adxHighThreshold"]
        adxLowThreshold = paraDict["adxLowThreshold"]

        adxTrend = ta.ADX(am.high, am.low, am.close, adxPeriod)
        adxMax = ta.MAX(adxTrend, adxMaxPeriod)

        # Status
        if ((adxTrend[-1]<=adxHighThreshold) and (adxMax[-1]> adxHighThreshold)) \
        or (adxTrend[-1]<=adxLowThreshold):
            adxCanTrade = -1
        else:
            adxCanTrade = 1
        return adxCanTrade, adxTrend

    def hlExitWideBand(self, am, paraDict):
        hlExitPeriod = paraDict['hlExitPeriod']

        highExitBand = ta.MAX(am.high, hlExitPeriod)
        lowExitBand = ta.MIN(am.low, hlExitPeriod)

        return highExitBand, lowExitBand
    
    def hlExitNorrowBand(self, am, paraDict):
        hlExitPeriod = paraDict['hlExitPeriod']//2

        highExitBand = ta.MAX(am.high, hlExitPeriod)
        lowExitBand = ta.MIN(am.low, hlExitPeriod)

        return highExitBand, lowExitBand

    def hlEntryWideBand(self, am, paraDict):
        hlEntryPeriod = paraDict['hlEntryPeriod']

        highEntryBand = ta.MAX(am.close, hlEntryPeriod)
        lowEntryBand = ta.MIN(am.close, hlEntryPeriod)
        return highEntryBand, lowEntryBand
    
    def hlEntryNorrowBand(self, am, paraDict):
        hlEntryPeriod = paraDict['hlEntryPeriod']//2

        highEntryBand = ta.MAX(am.close, hlEntryPeriod)
        lowEntryBand = ta.MIN(am.close, hlEntryPeriod)
        return highEntryBand, lowEntryBand

    def fliterVol(self, am, paraDict):
        volPeriod = paraDict['volPeriod']
        lowVolThreshold = paraDict['lowVolThreshold']
        highVolThreshold= paraDict['highVolThreshold']
        std = ta.STDDEV(am.close, volPeriod)
        atr = ta.ATR(am.high, am.low, am.close, volPeriod)
        rangeHL = (ta.MAX(am.high, volPeriod)-ta.MIN(am.low, volPeriod))/2
        minVol = min(std[-1], atr[-1], rangeHL[-1])
        lowFilterRange = am.close[-1]*lowVolThreshold
        maxVol = max(std[-1], atr[-1], rangeHL[-1])
        highFilterRange = am.close[-1]*highVolThreshold

        filterCanTrade = 1 if minVol >= lowFilterRange else -1
        highVolPos = 1 if maxVol >= highFilterRange else -1
        return filterCanTrade, highVolPos

    def filterNorrowPatternV(self, am, paraDict):
        hlEntryPeriod = paraDict['hlEntryPeriod']//2
        filterRctV = paraDict['filterRctV']

        arrayRange = am.close[-hlEntryPeriod:-1]

        highIndex = np.where(arrayRange == arrayRange[np.argmax(arrayRange)])[0][-1]
        lowIndex = np.where(arrayRange == arrayRange[np.argmin(arrayRange)])[0][-1]
        
        highLowPeriod = int(hlEntryPeriod - highIndex)
        lowHighPeriod = int(hlEntryPeriod - lowIndex)
        filterHighPct = (ta.MAX(am.close, highLowPeriod)[-1] - ta.MIN(am.low, highLowPeriod)[-1])/am.close[-1]
        filterLowPct =  (ta.MAX(am.high, lowHighPeriod)[-1] - ta.MIN(am.close, lowHighPeriod)[-1])/am.close[-1]

        if (filterHighPct>=filterRctV) or (filterLowPct>=filterRctV):
            filterVCanTrade = -1
        else:
            filterVCanTrade = 1
        return filterVCanTrade

    def filterWidePatternV(self, am, paraDict):
        hlEntryPeriod = paraDict['hlEntryPeriod']
        filterRctV = paraDict['filterRctV']

        arrayRange = am.close[-hlEntryPeriod:-1]

        highIndex = np.where(arrayRange == arrayRange[np.argmax(arrayRange)])[0][-1]
        lowIndex = np.where(arrayRange == arrayRange[np.argmin(arrayRange)])[0][-1]

        highLowPeriod = int(hlEntryPeriod - highIndex)
        lowHighPeriod = int(hlEntryPeriod - lowIndex)
        filterHighPct = (ta.MAX(am.close, highLowPeriod)[-1] - ta.MIN(am.low, highLowPeriod)[-1])/am.close[-1]
        filterLowPct =  (ta.MAX(am.high, lowHighPeriod)[-1] - ta.MIN(am.close, lowHighPeriod)[-1])/am.close[-1]

        if (filterHighPct>=filterRctV) or (filterLowPct>=filterRctV):
            filterVCanTrade = -1
        else:
            filterVCanTrade = 1
        return filterVCanTrade

    # ----------------仓位管理模块----------------

    def dsAdd(self, am, paraDict):
        dsPeriod = paraDict['dsPeriod']
        dsSemaPeriod = paraDict['dsSemaPeriod']
        dsLemaPeriod = paraDict['dsLemaPeriod']
        dsthreshold = paraDict['dsThreshold']

        density = (ta.MAX(am.high, dsPeriod)-ta.MIN(am.low, dsPeriod))/ta.SUM(am.high-am.low, dsPeriod)
        dsSma = ta.EMA(density, dsSemaPeriod)
        dsLma = ta.MA(density, dsLemaPeriod)

        dsUp = dsSma[-1]>dsLma[-1]
        dsCan = (dsSma[-1]>dsthreshold)

        dsCanAddPos = True if dsUp and dsCan else False
        return dsCanAddPos, dsSma, dsLma

    def addTriangle(self, paraDict):
        posTime = paraDict['posTime']
        addVar = paraDict['addVar']
        initVar = paraDict['initVar']
        sp = 0
        if (posTime % 2) != 0:
            sp = int((posTime+1)/2)
        else:
            raise Exception("Invalid length!", posTime)
        result = [0] * posTime
        for i in range(1, sp):
            initVar += addVar
            result[i] = int(initVar)
        for i in range(sp, posTime):
            initVar -= addVar
            result[i] = int(initVar)
        return np.array(result)

    def addLotList(self, paraDict):
        posTime = paraDict['posTime']
        addVar = paraDict['addVar']
        initVar = paraDict['initVar']
        sign = paraDict['sign']

        result = [initVar] * posTime
        for i in range(1, posTime):
            addMultiplier = eval(f"initVar {sign} addVar")
            result[i] = addMultiplier
        return np.array(result)