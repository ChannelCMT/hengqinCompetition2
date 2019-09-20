import talib as ta
import numpy as np
import pandas as pd

"""
将kdj策略需要用到的信号生成器抽离出来
"""

class hlBreakSignal():

    def __init__(self):
        self.author = 'abc'

    # def hlExitBand(self, am, paraDict):
    #     hlExitPeriod = paraDict['hlExitPeriod']
    #     highExitBand = ta.MAX(am.close, hlExitPeriod)
    #     lowExitBand = ta.MIN(am.close, hlExitPeriod)
    #     return highExitBand, lowExitBand

    def hlEntryBand(self, am, paraDict):
        hlEntryPeriod = paraDict['hlEntryPeriod']
        highEntryBand = ta.MAX(am.high, hlEntryPeriod)
        lowEntryBand = ta.MIN(am.low, hlEntryPeriod)
        return highEntryBand, lowEntryBand
    
    # def hlEntryWideBand(self, am, paraDict):
    #     bandTime = paraDict['bandTime']
    #     hlEntryPeriod = int(paraDict['hlEntryPeriod']*bandTime)
    #     highEntryBand = ta.MAX(am.high, hlEntryPeriod)
    #     lowEntryBand = ta.MIN(am.low, hlEntryPeriod)
    #     return highEntryBand, lowEntryBand

    # def trendBand(self,am,paraDict):
    #     trendPeriod = paraDict['trendPeriod']
    #     highEntryBand = ta.MA(am.high, trendPeriod)
    #     lowEntryBand = ta.MA(am.low, trendPeriod)
    #     return highEntryBand, lowEntryBand

    def csBandUp(self,am,paraDic):
        csdev1 = paraDic['csdev1']
        csdev2 = paraDic['csdev2']
        bandAtr = paraDic['bandAtr']

        atr = ta.ATR(am.high, am.low, am.close, bandAtr)
        highEntryBand = am.close[-2] + atr * csdev1
        lowEntryBand = am.close[-2] - atr*csdev2

        return highEntryBand, lowEntryBand

    def csBandDown(self,am,paraDic):
        csdev1 = paraDic['csdev1']
        csdev2 = paraDic['csdev2']
        bandAtr = paraDic['bandAtr']

        atr = ta.ATR(am.high, am.low, am.close, bandAtr)
        highEntryBand = am.close[-2] + atr * csdev2
        lowEntryBand = am.close[-2] - atr*csdev1

        return highEntryBand, lowEntryBand



    def dsEnvUp(self, am, paraDict):
        dsPeriod = paraDict['dsPeriod']
        dsSmaPeriod = paraDict['dsSmaPeriod']
        dsLmaPeriod = paraDict['dsLmaPeriod']
        dsthreshold = paraDict['dsThreshold']

        density = (ta.MAX(am.high, dsPeriod)-ta.MIN(am.low, dsPeriod))/ta.SUM(am.high-am.low, dsPeriod)
        dsSma = ta.EMA(density, dsSmaPeriod)
        dsLma = ta.MA(density, dsLmaPeriod)

        dsUp = dsSma[-1]>dsLma[-1]
        dsCan = (dsSma[-1]>dsthreshold)
        
        dsTrendEnv = True if dsUp and dsCan else False
        return dsTrendEnv, dsSma, dsLma
    
    def keltnerentryBand(self, am, paraDict):
        """肯特纳通道"""
        keltnerentrywindow = paraDict['keltnerentrywindow']
        keltnerentrydev =paraDict['keltnerentrydev']
        
        mid = ta.SMA(am.close,keltnerentrywindow)
        atr = ta.ATR(am.high, am.low, am.close,keltnerentrywindow)
        highEntryBand = mid + atr * keltnerentrydev
        lowEntryBand = mid - atr * keltnerentrydev

        #hlEntryPeriod = paraDict['hlEntryPeriod']

        # highEntryBand2 = ta.MAX(am.high, hlEntryPeriod)
        # lowEntryBand2 = ta.MIN(am.low, hlEntryPeriod)

        # highEntryBand = max(highEntryBand1, highEntryBand2)
        # lowEntryBand = min(lowEntryBand1, lowEntryBand2)

        return highEntryBand, lowEntryBand
    
    def keltnerexitBand(self, am, paraDict):
        """肯特纳通道"""
        keltnerexitwindow = paraDict['keltnerexitwindow']
        keltnerexitdev =paraDict['keltnerexitdev']

        mid = ta.SMA(am.close,keltnerexitwindow)
        atr = ta.ATR(am.high, am.low, am.close, keltnerexitwindow)

        highExitBand = mid + atr * keltnerexitdev
        lowExitBand = mid - atr * keltnerexitdev

        # hlExitPeriod = paraDict['hlExitPeriod']
        # highExitBand2 = ta.MAX(am.high, hlExitPeriod)
        # lowExitBand2 = ta.MIN(am.low, hlExitPeriod)

        # highExitBand = max(highExitBand1[-1], highExitBand2[-1])
        # lowExitBand = min(lowExitBand1[-1], lowExitBand2[-1])

        
        return highExitBand, lowExitBand
    
    def keltnerEntryWideBand(self, am, paraDict):
        bandTime = paraDict['bandTime']
        # keltnerexitwindow = paraDict['keltnerexitwindow']
        keltnerentrydev =paraDict['keltnerexitdev']
        keltnerEntryPeriod = int(paraDict['keltnerentrywindow']*bandTime)
        mid = ta.SMA(am.close,keltnerEntryPeriod)
        atr = ta.ATR(am.high, am.low, am.close, keltnerEntryPeriod)
               
        # highEntryBand = ta.MAX(am.high, keltnerEntryPeriod)
        # lowEntryBand = ta.MIN(am.low, keltnerEntryPeriod)
        highEntryBand = mid + atr * keltnerentrydev
        lowEntryBand = mid - atr * keltnerentrydev
        return highEntryBand, lowEntryBand
    
    def cmiEnv(self, am, paraDict):
        cmiPeriod = paraDict['cmiPeriod']
        cmiThreshold = paraDict['cmiThreshold']

        # momentum = (100*np.abs(am.close[cmiPeriod:] - am.close[:-cmiPeriod]))[-cmiPeriod:]
        momentum = (100*np.abs(am.close- am.close[-cmiPeriod]))[-cmiPeriod:]
        hlRange = (ta.MAX(am.high, cmiPeriod)-ta.MIN(am.low, cmiPeriod))[-cmiPeriod:]
        cmi = momentum/hlRange
        cmiMa = ta.MA(cmi, cmiPeriod)
        #envDirection = 1 if cmiMa[-1]>cmiThreshold else -1
        cmiTrendEnv = False
        if cmiMa[-1]>cmiThreshold:
            cmiTrendEnv = True   
        #cmi = 100*np.abs(am.close[-1]-am.close[-cmiPeriod])/ta.MAX(am.high,cmiPeriod)-ta.MIN(am.low,cmiPeriod)
        return  cmiTrendEnv,cmiMa
    
    def rsiSignal(self,am, paraDict):
        rsiPeriod = paraDict['rsiPeriod']
        rsi = ta.RSI(am.close, rsiPeriod)
        rsiDirection = 0
        if rsi[-1]<=45:
            rsiDirection=1
        elif rsi[-1]>=55:
            rsiDirection=-1
        return rsiDirection, rsi
    
    def soupSignal(self,am, paraDict):
        hlPeriod = paraDict['hlPeriod']
        delayPeriod = paraDict['delayPeriod']

        delayMax = ta.MAX(am.high, hlPeriod)[:-delayPeriod]
        delayMin = ta.MIN(am.low, hlPeriod)[:-delayPeriod]

        newHigh = ta.MAX(am.high, hlPeriod)[delayPeriod:]
        newLow = ta.MIN(am.low, hlPeriod)[delayPeriod:]

        exHighArray = delayMax*(delayMax<newHigh)
        exLowArray = delayMin*(delayMin>newLow)

        delayHigh, delayLow = 0, 0
        for i in range(len(exHighArray)-1, 0, -1):
            if exHighArray[i] != 0:
                delayHigh = exHighArray[i]
                break
        
        for i in range(len(exLowArray)-1, 0, -1):
            if exLowArray[i] != 0:
                delayLow = exLowArray[i]
                break
        
        return delayHigh, delayLow, newHigh, newLow
    
    def atr(self, am, paraDict):
        AtrPeriod = paraDict['AtrPeriod']
        atrLevel = paraDict['atrLevel']
        atr = ta.ATR(am.high, am.low, am.close, AtrPeriod)
        atrGreat = False
        if atr[-1] >= atrLevel:
            atrGreat = True
        return atr, atrGreat
    
    def consolidation(self,am):
        up = False
        down = False
        if am.close[-1] >= (am.close[-1]+ am.high[-1]+am.high[-1])*0.3:
            up = True
        if am.close[-1] <(am.close[-1]+am.high[-1]+am.high[-1])*0.3:
            down = True
        return up,down
    
    def maCross(self,am,paraDict):
        fastPeriod = paraDict["fastPeriod"]
        slowPeriod = paraDict["slowPeriod"]
        largePeriod = paraDict["largePeriod"]


        sma = ta.EMA(am.close, fastPeriod)
        lma = ta.EMA(am.close, slowPeriod)
        ema = ta.EMA(am.close, largePeriod)
        goldenCross = sma[-1]>lma[-1] and sma[-2]<=lma[-2]
        deathCross = sma[-1]<lma[-1] and sma[-2]>=lma[-2]

        maCrossSignal = 0
        if goldenCross:
            maCrossSignal = 1
        if deathCross:
            maCrossSignal = -1
        return maCrossSignal, sma, lma,ema