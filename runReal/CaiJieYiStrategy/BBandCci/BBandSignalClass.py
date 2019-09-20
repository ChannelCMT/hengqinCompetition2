import talib as ta
import numpy as np
import pandas as pd

"""
将kdj策略需要用到的信号生成器抽离出来
"""

class BBandSignal:

    def __init__(self):
        self.author = 'channel'
    
    def atrStopLoss(self, am, paraDict):
        bandPeriod = paraDict['bandPeriod']
        atrTime = paraDict['atrTime']
        atr = ta.ATR(am.high, am.low, am.close, bandPeriod)
        stopLossAtr = atrTime*atr
        return stopLossAtr

    def bPct(self, am, paraDict):
        bandPeriod = paraDict['bandPeriod']
        bBandEntry = paraDict['bBandEntry']
        bPctThreshold = paraDict['bPctThreshold']
        limitPeriod = paraDict['limitPeriod']

        bBandEntryUp, _, bBandEntryDn = ta.BBANDS(am.close, bandPeriod, bBandEntry, bBandEntry)
        bPctValue = (am.close - bBandEntryDn)/(bBandEntryUp-bBandEntryDn) *100
        if bPctValue[-1]>bPctThreshold:
            if min(bPctValue[-limitPeriod:])<=bPctThreshold:
                bDirection = 1
            else:
                bDirection = 0
        elif bPctValue[-1]<(100-bPctThreshold) :
            if max(bPctValue[-limitPeriod:])>=(100-bPctThreshold):
                bDirection = -1
            else:
                bDirection = 0
        else:
            bDirection = 0
        return bDirection, bPctValue

    def bandWidth(self, am, paraDict):
        bandPeriod = paraDict['bandPeriod']
        bBandEntry = paraDict['bBandEntry']
        limitPeriod = paraDict['limitPeriod']
        bandWidthThreshold = paraDict['bandWidthThreshold']
        bandFilterThreshold = paraDict['bandFilterThreshold']
        
        stdStatus = 0
        bBandEntryUp, bBandEntryMa, bBandEntryDn = ta.BBANDS(am.close, bandPeriod, bBandEntry, bBandEntry)
        bandWidthValue = (bBandEntryUp-bBandEntryDn)/bBandEntryMa
        bandWidthMax = ta.MAX(bandWidthValue, limitPeriod)
        bandUp = bandWidthValue[-1]>bandWidthValue[-2]
        bandTight = bandWidthMax[-1]<bandWidthThreshold and bandWidthMax[-1]>bandFilterThreshold
        if bandUp and bandTight:
            stdStatus = 1
        return stdStatus, bandWidthValue, bandWidthMax

    def mfiIndicator(self, am, paraDict):
        mfiPeriod = paraDict['bandPeriod']
        mfiThreshold = paraDict['bPctThreshold']
        mfiSignal = ta.MFI(am.high, am.low, am.close, am.volume, mfiPeriod)
        mfiStatus = 0
        if mfiSignal[-1]>mfiThreshold:
            mfiStatus = 1
        if mfiSignal[-1]<(100-mfiThreshold):
            mfiStatus = -1
        return mfiStatus, mfiSignal
    
    def cciIndicator(self, am, paraDict):
        cciPeriod = paraDict['bandPeriod']
        cciThreshold = paraDict['cciThreshold']
        cciSignal = ta.CCI(am.high, am.low, am.close, cciPeriod)
        cciStatus = 0
        if cciSignal[-1]>cciThreshold:
            cciStatus = 1
        if cciSignal[-1]<-cciThreshold:
            cciStatus = -1
        return cciStatus, cciSignal
    
    ### 计算Vol加仓
    # def bandLimit(self, am, paraDict):
    #     bandPeriod = paraDict['bandPeriod']
    #     bBandEntry = paraDict['bBandEntry']
    #     limitPeriod = paraDict['limitPeriod']
    #     # bandLongPeriod = paraDict['bandLongPeriod']

    #     stdStatus = 0
    #     bBandEntryUp, bBandEntryMa, _ = ta.BBANDS(am.close, bandPeriod, bBandEntry, bBandEntry)
        
    #     atr = ta.ATR(am.high, am.low, am.close, bandPeriod)
    #     atrBand = bBandEntryMa+bBandEntry*atr
    #     stdInside = np.sum(atrBand[-limitPeriod:]<bBandEntryUp[-limitPeriod:])==0
    #     stdUp = (bBandEntryUp[-1]>bBandEntryUp[-2]) and (bBandEntryUp[-2]>bBandEntryUp[-3])
    #     if stdInside and stdUp:
    #         stdStatus = 1
    #     return stdStatus, bBandEntryUp, atrBand

    # def bBandEntrySignal(self, am, paraDict):
    #     bandPeriod = paraDict['bandPeriod']
    #     bBandEntry = paraDict['bBandEntry']

    #     bBandEntryUp, bBandEntryMa, bBandEntryDn = ta.BBANDS(am.close, bandPeriod, bBandEntry, bBandEntry)
    #     return bBandEntryUp, bBandEntryMa, bBandEntryDn