import talib as ta
import numpy as np
import pandas as pd
from scipy import stats

class hlRegressionSignal:

    def __init__(self):
        self.slopeList = []
        self.zScore = np.array([])
        self.rsrsDirection = 0

    def initSlopeList(self, am, paraDict):
        regPeriod = paraDict["regPeriod"]
        for i in range(len(am.high)-regPeriod+1):
            high = am.high[i:i+regPeriod]
            low = am.low[i:i+regPeriod]
            slope, _, _, _, _ = stats.linregress(low, high)
            self.slopeList.append(slope)

    def regDirection(self, am, paraDict):
        zScorePeriod = paraDict['zScorePeriod']
        regPeriod = paraDict["regPeriod"]
        rsrsThreshold = paraDict["rsrsThreshold"]

        self.rsrsDirection = 0
        rsrsAmend = np.array([0])
        if len(self.slopeList)==0:
            self.initSlopeList(am, paraDict)
        else:
            high = am.high[-regPeriod:]
            low = am.low[-regPeriod:]
            slope, _, r_value, _, _ = stats.linregress(low, high)
            rSquare = r_value**2
            self.slopeList.append(slope)
            if len(self.slopeList)>1000:
                self.slopeList.pop(0)
            kArray = np.array(self.slopeList)
            mu = ta.MA(kArray, zScorePeriod)
            std = ta.STDDEV(kArray, zScorePeriod)
            self.zScore = (kArray - mu)/ std
            rsrsAmend = self.zScore*rSquare
            # rsStatus
            if (rsrsAmend[-1] >= rsrsThreshold):
                self.rsrsDirection = 1
            elif (rsrsAmend[-1] <= -rsrsThreshold):
                self.rsrsDirection = -1
        return self.rsrsDirection, rsrsAmend
    
    def zScoreVolumeCor(self, am, paraDict):
        corPeriod = paraDict["corPeriod"]
        corThreshold = paraDict["corThreshold"]
        lessPeriod = int(2*corPeriod)
        zScoreLength = len(self.zScore)
        if zScoreLength>lessPeriod:
            correlation = ta.CORREL(self.zScore[-lessPeriod:], am.volume[-lessPeriod:], corPeriod)
            if correlation[-1]>=corThreshold:
                correlationDirection = 1
            elif correlation[-1] <= -corThreshold:
                correlationDirection = -1
            else:
                correlationDirection = 0
            return correlationDirection, correlation
        else:
            return None, np.array([None])
        
    def fliterVol(self, am, paraDict):
        volPeriod = paraDict['volPeriod']
        lowVolThreshold = paraDict['lowVolThreshold']

        std = ta.STDDEV(am.close, volPeriod)
        atr = ta.ATR(am.high, am.low, am.close, volPeriod)
        rangeHL = (ta.MAX(am.high, volPeriod)-ta.MIN(am.low, volPeriod))/2
        minVol = min(std[-1], atr[-1], rangeHL[-1])
        lowFilterRange = am.close[-1]*lowVolThreshold
        filterCanTrade = 1 if (minVol >= lowFilterRange) else -1
        return filterCanTrade

    # def volumeCor(self, am, paraDict):
    #     corPeriod = paraDict["corPeriod"]
    #     correlation = ta.CORREL(am.close, am.volume, corPeriod)
    #     correlationDirection = 1 if correlation[-1]>0 else -1
    #     return correlationDirection, correlation
    
    #### 计算reg指标
    ### linregress(x, y)
    # def regScipy(self,am,paraDict):
    #     regPeriod = paraDict["regPeriod"]
    #     high = am.high[-regPeriod:]
    #     low = am.low[-regPeriod:]
    #     slope, _, r_value, _, _ = stats.linregress(low, high)
    #     rSquare = r_value**2
    #     return slope, rSquare
