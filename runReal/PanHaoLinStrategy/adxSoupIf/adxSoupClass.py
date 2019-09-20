import talib as ta
import numpy as np
import pandas as pd
from numpy import *

np.seterr(divide='ignore',invalid='ignore')

class adxSoupSignal():
    def __init__(self):
        self.author = 'channel'
    #### 计算ADX指标
    def adxEnv(self,am,paraDict):
        adxPeriod = paraDict["adxPeriod"]
        adxMaPeriod = paraDict["adxMaPeriod"]
        adxThreshold = paraDict["adxThreshold"]

        adx = ta.ADX(am.high, am.low, am.close, adxPeriod)
        adxMa = ta.MA(adx, adxMaPeriod)

        # Status
        if (adx[-1]>adxMa[-1]) and (adx[-1]>adxThreshold):
            adxNoTrend = 0
        else:
            adxNoTrend = 1
        return adxNoTrend, adx

    def soupSignal(self,am, paraDict):
        hlPeriod = paraDict['hlPeriod']
        distanceMax = paraDict['distanceMax']
        distanceMin = paraDict['distanceMin']
        dangerousMinPct = paraDict['dangerousMinPct']
        dangerousMaxPct = paraDict['dangerousMaxPct']

        pastMax = ta.MAX(am.high, hlPeriod)[:-1][distanceMin-1:]
        pastMin = ta.MIN(am.low, hlPeriod)[:-1][distanceMin-1:]

        delayMax = ta.MAX(am.high, hlPeriod)[:-distanceMin]
        delayMin = ta.MIN(am.low, hlPeriod)[:-distanceMin]

        newHigh = ta.MAX(am.high, hlPeriod)[1:][distanceMin-1:]
        newLow = ta.MIN(am.low, hlPeriod)[1:][distanceMin-1:]

        # 找到满足创新高后找到最少多少个Bar前面的高低点
        exHighArray = delayMax*(pastMax<newHigh)
        exLowArray = delayMin*(pastMin>newLow)

        rightExHigh = exHighArray[-distanceMax:]
        rightExLow = exLowArray[-distanceMax:]

        delayHigh, delayLow = None, None
        for i in range(len(rightExHigh)-1, 0, -1):
            if rightExHigh[i] != 0:
                delayHigh = rightExHigh[i]
                break
        
        for i in range(len(rightExLow)-1, 0, -1):
            if rightExLow[i] != 0:
                delayLow = rightExLow[i]
                break
        
        # 判断过小与过大的边界
        dangerous = None
        if delayHigh:
            rangeHigh = (newHigh[-1] - delayHigh)/delayHigh
            if (rangeHigh<dangerousMinPct) or (rangeHigh>dangerousMaxPct):
                dangerous = 'highDangerous'
        if delayLow:
            rangeLow = (delayLow - newLow[-1])/ newLow[-1]
            if (rangeLow<dangerousMinPct) or (rangeLow>dangerousMaxPct):
                dangerous = 'lowDangerous'
        return delayHigh, delayLow, newHigh, newLow, dangerous

    def hlExitSignal(self, am, paraDict):
        hlExitPeriod = paraDict['hlExitPeriod']
        exitHigh = ta.MAX(am.high, hlExitPeriod)
        exitLow = ta.MIN(am.low, hlExitPeriod)
        return exitHigh, exitLow

    def pctTrailing(self, am, paraDict):
        pctPeriod = paraDict['pctPeriod']
        hourCount = paraDict['hourCount']
        clipPct = paraDict['clipPct']

        closeReturn = (am.close[1:]-am.close[:-1])/am.close[:-1]
        cond1 = np.percentile(closeReturn[1:], clipPct)
        cond2 = np.percentile(closeReturn[1:], 100-clipPct)

        standCloseReturn = np.clip(closeReturn, cond1, cond2)
        pctStd = ta.STDDEV(standCloseReturn, pctPeriod)
        trailingPct = 2*pctStd[-1]*(hourCount**0.5)
        return trailingPct