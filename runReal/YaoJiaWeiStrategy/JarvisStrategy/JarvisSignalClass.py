import talib as ta
import numpy as np
import pandas as pd

"""
将kdj策略需要用到的信号生成器抽离出来
"""

class JarvisSignal():

    def __init__(self):
        self.author = 'Jarvis'

    def filterLowAtr(self, am, paraDict):
        atrPeriod = paraDict["atrPeriod"]
        lowVolThreshold = paraDict["lowVolThreshold"]

        # 过滤超小波动率
        atr = ta.ATR(am.high, am.low, am.close, atrPeriod)
        filterCanTrade = 1 if atr[-1]>am.close[-1]*lowVolThreshold else 0
        return filterCanTrade

    def breakBandSignal(self, am, paraDict):
        BBandPeriod = paraDict['BBandPeriod']
        fastk_period = paraDict['fastk_period']
        slowk_period = paraDict['slowk_period']
        slowk_matype = paraDict['slowk_matype']
        slowd_period = paraDict['slowd_period']
        slowd_matype = paraDict['slowd_matype']

        slowk, slowd = ta.STOCH(am.high, am.low, am.close, fastk_period, slowk_period, slowk_matype, slowd_period, slowd_matype)   #KDJ指标
        upperBand, mid, lowerBand = ta.BBANDS(am.close, BBandPeriod)
        close = am.close

        breakUpperBand = am.close[-2] <= upperBand[-2] and am.close[-1] > upperBand[-2] and slowk[-1]>slowd[-1]
        breakLowerBand = am.close[-2] >= lowerBand[-2] and am.close[-1] < lowerBand[-2] and slowk[-1]<=slowd[-1]
        return breakUpperBand, breakLowerBand, upperBand, lowerBand

    def breakTrendBand(self, am, paraDict):
        hlMaPeriod = paraDict["hlMaPeriod"]
        adxPeriod = paraDict["adxPeriod"]

        adx = ta.ADX(am.high, am.low, am.close, adxPeriod)
        upperBand = ta.MA(am.high, hlMaPeriod)[-1]
        lowerBand = ta.MA(am.low, hlMaPeriod)[-1]
        breakUpperBand = am.close[-1]>upperBand and am.close[-2]<upperBand and adx[-1]>adx[-2] and adx[-1]>33
        breakLowerBand = am.close[-1]<lowerBand and am.close[-2]>lowerBand and adx[-1]<adx[-2] and adx[-1]<=33
        return breakUpperBand, breakLowerBand, upperBand, lowerBand

    def maExit(self, am, paraDict):
        maPeriod = paraDict['maPeriod']
        # 计算均线出场条件
        exitLongBandSignal = am.low[-1]<ta.MA(am.close, maPeriod)[-1]
        exitShortBandSignal = am.high[-1]>ta.MA(am.close, maPeriod)[-1]
        return exitLongBandSignal, exitShortBandSignal

    def atrStoploss(self, am, paraDict):
        atrPeriod = paraDict['atrPeriod']
        atr = ta.ATR(am.high, am.low, am.close, atrPeriod)
        return atr

    def KDJ(self,am,paraDict):
        fastk_period = paraDict['fastk_period']
        slowk_period = paraDict['slowk_period']
        slowk_matype = paraDict['slowk_matype']
        slowd_period = paraDict['slowd_period']
        slowd_matype = paraDict['slowd_matype']
        slowk, slowd = ta.STOCH(am.high, am.low, am.close, fastk_period, slowk_period, slowk_matype, slowd_period, slowd_matype)   #KDJ指标

        kdjSignal = 0
        if slowk[-1]>slowd[-1]:
            kdjSignal = 1
        elif slowk[-1]<=slowd[-1]:
            kdjSignall = -1
        else:
            kdjSignal = 0
        return kdjSignal, slowk, slowd

    def Env(self, am, paraDict):
        fastperiod = paraDict["fastperiod"]
        slowperiod = paraDict["slowperiod"]
        signalperiod = paraDict["signalperiod"]
        emaPeriod1 = paraDict["emaPeriod1"]

        close = am.close
        macd, macdsignal, macdhist = ta.MACD(am.close, fastperiod, slowperiod, signalperiod)
        ema1 = ta.EMA(close, emaPeriod1)

        EnvUp = (ema1[-1] > ema1[-2]) and (macdhist[-1] > macdhist[-2])
        EnvDn = (ema1[-1] <= ema1[-2]) and (macdhist[-1] <= macdhist[-2])
        trendStatus = 0

        if EnvUp:
            trendStatus = 1
        elif EnvDn:
            trendStatus = -1
        else:
            trendStatus = 0
        return trendStatus
