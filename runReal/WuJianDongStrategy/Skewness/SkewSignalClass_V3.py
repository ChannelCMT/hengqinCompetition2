import talib as ta
import numpy as np
import pandas as pd

class skewBaseSignal():

    def __init__(self):
        pass
    
    def skewShortCal(self,am,paraDict):
        skewPeriod = paraDict['skewShortPeriod']
        skewShortThreshold = paraDict['skewShortThreshold']
        ret = ta.ROCP(am.close)
        miu = ta.MA(ret, skewPeriod)
        std = ta.STDDEV(ret, skewPeriod)
        skew = ta.MA(((ret - miu)/std)**3, skewPeriod)
        skewMa = ta.MA(skew, 3)
        skewSignal = 0
        if skew[-1]>=skewShortThreshold and skewMa[-1]>skewMa[-2]:
            skewSignal = 1
        if skew[-1]<=-skewShortThreshold and skewMa[-1]<skewMa[-2]:
            skewSignal = -1
        return skewSignal, skew

    def volumeSignal(self, am, paraDict):
        volumeMaPeriod = paraDict['volumeMaPeriod']
        volumeStdMultiple = paraDict['volumeStdMultiple']
        volumeUpper, _, _ = ta.BBANDS(am.volume[:-1], volumeMaPeriod, volumeStdMultiple, volumeStdMultiple)
        volumeSpike = 1 if ta.MA(am.volume, 3)[-1]>=volumeUpper[-1] else 0
        return volumeSpike, volumeUpper

    def skewLongCal(self, am, paraDict):
        skewPeriod = paraDict['skewLongPeriod']
        skewThreshold_left = paraDict['skewLongThreshold_left']
        # skewThreshold_right = paraDict['skewThreshold_right']
        skewThreshold_right = skewThreshold_left
        ret = ta.ROCP(am.close)
        miu = ta.MA(ret, skewPeriod)
        std = ta.STDDEV(ret, skewPeriod)
        skew = ta.MA(((ret - miu)/std)**3, skewPeriod)
        skewSignal = 0
        if skew[-1] > skewThreshold_right: # 长周期处于上涨趋势（右偏）
            skewSignal = 1
        elif skew[-1] < -skewThreshold_left:
            skewSignal = -1
        return skewSignal, skew