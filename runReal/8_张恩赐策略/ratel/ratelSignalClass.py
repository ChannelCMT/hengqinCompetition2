import talib as ta
import numpy as np
import pandas as pd

class ratelSignal():

    def __init__(self):
        self.author = 'Ivan'

    '''
    计算入场指标
    '''
    def calEntryFilter(self, am, kind, period, threshold, cmiMAPeriod, gene4):
        if kind==0:
            self.entryFilter = 1
        elif kind==1:
            self.entryFilter = 1 if (ta.ADX(am.high,am.low,am.close, period)[-1] > threshold) else 0
        elif kind==2:
            diff = np.insert(abs(am.close[period:] - am.close[:-period]),0,[0 for _ in range(period)])
            de = np.insert(ta.SUM(abs(am.close[1:]-am.close[:-1]), period),0,0)
            ER = ta.DIV(diff, de)*100
            self.entryFilter = 1 if (ER[-1] > threshold) else 0
        elif kind==3:
            diff = np.insert(abs(am.close[period:] - am.close[:-period]),0,[0 for _ in range(period)])
            de = ta.MAX(am.close, period)-ta.MIN(am.close, period)
            cmi = ta.MA(ta.DIV(diff, de)*100, cmiMAPeriod)
            self.entryFilter = 1 if (cmi[-1] > threshold) else 0
            
    def calEntryIndicatorPart0(self, am, kind, period, upperK, lowerK, gene9):
        if kind==0:
            self.entryIndicatorPart0 = 0
        elif kind==1:
            entrySMAbuy= 1 if((am.close[-1] > ta.SMA(am.close, period)[-1])&(am.close[:-1][-1] < ta.SMA(am.close, period)[:-1][-1])) else 0
            entrySMAsell= -1 if((am.close[-1] < ta.SMA(am.close, period)[-1])&(am.close[:-1][-1] > ta.SMA(am.close, period)[:-1][-1])) else 0
            self.entryIndicatorPart0 = entrySMAbuy + entrySMAsell
        elif kind==2:
            entryEMAbuy= 1 if((am.close[-1] > ta.EMA(am.close, period)[-1]) & (am.close[:-1][-1] < ta.EMA(am.close, period)[:-1][-1])) else 0
            entryEMAsell = -1 if((am.close[-1] < ta.EMA(am.close, period)[-1]) & (am.close[:-1][-1] > ta.EMA(am.close, period)[:-1][-1])) else 0
            self.entryIndicatorPart0 = entryEMAbuy + entryEMAsell
        elif kind==3:
            entryBBANDSbuy = 1 if((am.close[-1] > ta.BBANDS(am.close, period, upperK, lowerK)[0][-1])&(am.close[:-1][-1]<ta.BBANDS(am.close, period, upperK, lowerK)[0][:-1][-1])) else 0
            entryBBANDSsell= -1 if((am.close[-1] < ta.BBANDS(am.close, period, upperK, lowerK)[-1][-1])&(am.close[:-1][-1]>ta.BBANDS(am.close, period, upperK, lowerK)[-1][:-1][-1])) else 0
            self.entryIndicatorPart0 = entryBBANDSbuy + entryBBANDSsell
        elif kind==4:
            entryATRBANDSbuy = 1 if((am.close[-1] > (ta.MA(am.close, period)+upperK*ta.ATR(am.high, am.low, am.close, period))[-1])&(am.close[:-1][-1]<(ta.MA(am.close, period)+upperK*ta.ATR(am.high, am.low, am.close, period))[:-1][-1])) else 0
            entryATRBANDSsell = -1 if((am.close[-1] < (ta.MA(am.close, period)-lowerK*ta.ATR(am.high, am.low, am.close, period))[-1])&(am.close[:-1][-1]>(ta.MA(am.close, period)-lowerK*ta.ATR(am.high, am.low, am.close, period))[:-1][-1])) else 0
            self.entryIndicatorPart0 = entryATRBANDSbuy + entryATRBANDSsell

            
    def calEntryIndicatorPart1(self, am, kind, period, upperK, lowerK, gene9):
        if kind==0:
            self.entryIndicatorPart1 = 0
        elif kind==1:
            entrySMAbuy= 1 if((am.close[-1] > ta.SMA(am.close, period)[-1])&(am.close[:-1][-1] < ta.SMA(am.close, period)[:-1][-1])) else 0
            entrySMAsell= -1 if((am.close[-1] < ta.SMA(am.close, period)[-1])&(am.close[:-1][-1] > ta.SMA(am.close, period)[:-1][-1])) else 0
            self.entryIndicatorPart1 = entrySMAbuy + entrySMAsell
        elif kind==2:
            entryEMAbuy= 1 if((am.close[-1] > ta.EMA(am.close, period)[-1]) & (am.close[:-1][-1] < ta.EMA(am.close, period)[:-1][-1])) else 0
            entryEMAsell = -1 if((am.close[-1] < ta.EMA(am.close, period)[-1]) & (am.close[:-1][-1] > ta.EMA(am.close, period)[:-1][-1])) else 0
            self.entryIndicatorPart1 = entryEMAbuy + entryEMAsell
        elif kind==3:
            entryBBANDSbuy = 1 if((am.close[-1] > ta.BBANDS(am.close, period, upperK, lowerK)[0][-1])&(am.close[:-1][-1]<ta.BBANDS(am.close, period, upperK, lowerK)[0][:-1][-1])) else 0
            entryBBANDSsell= -1 if((am.close[-1] < ta.BBANDS(am.close, period, upperK, lowerK)[-1][-1])&(am.close[:-1][-1]>ta.BBANDS(am.close, period, upperK, lowerK)[-1][:-1][-1])) else 0
            self.entryIndicatorPart1 = entryBBANDSbuy + entryBBANDSsell
        elif kind==4:
            entryATRBANDSbuy = 1 if((am.close[-1] > (ta.MA(am.close, period)+upperK*ta.ATR(am.high, am.low, am.close, period))[-1])&(am.close[:-1][-1]<(ta.MA(am.close, period)+upperK*ta.ATR(am.high, am.low, am.close, period))[:-1][-1])) else 0
            entryATRBANDSsell = -1 if((am.close[-1] < (ta.MA(am.close, period)-lowerK*ta.ATR(am.high, am.low, am.close, period))[-1])&(am.close[:-1][-1]>(ta.MA(am.close, period)-lowerK*ta.ATR(am.high, am.low, am.close, period))[:-1][-1])) else 0
            self.entryIndicatorPart1 = entryATRBANDSbuy + entryATRBANDSsell
                    
    def myentry(self, am, paraDict, kind):
        ch = paraDict["ch%s"%kind]
        self.calEntryFilter(am, ch[0], ch[1],ch[2],ch[3],ch[4])
        self.calEntryIndicatorPart0(am, ch[5],ch[6],ch[7],ch[8],ch[9])
        self.calEntryIndicatorPart1(am, ch[10],ch[11],ch[12],ch[13],ch[14])
        # entryFilter=0的时候执行entryIndicatorPart0   entryFilter=1的时候执行entryIndicatorPart1
        self.entry = self.entryIndicatorPart0*(1 if self.entryFilter==0 else 0)  +  self.entryIndicatorPart1 * self.entryFilter
        return self.entry


    '''
    计算出场指标
    '''
    def calExitFilter(self, am, kind, period, threshold, cmiMAPeriod, gene4):
        if kind==0:
            self.exitFilter = 1
        elif kind==1:
            self.exitFilter = 1 if (ta.ADX(am.high,am.low,am.close, period)[-1] > threshold) else 0
        elif kind==2:
            diff = np.insert(abs(am.close[period:] - am.close[:-period]),0,[0 for _ in range(period)])
            de = np.insert(ta.SUM(abs(am.close[1:]-am.close[:-1]), period),0,0)
            ER = ta.DIV(diff, de)*100
            self.exitFilter = 1 if (ER[-1] > threshold) else 0
        elif kind==3:
            diff = np.insert(abs(am.close[period:] - am.close[:-period]),0,[0 for _ in range(period)])
            de = ta.MAX(am.close, period)-ta.MIN(am.close, period)
            cmi = ta.MA(ta.DIV(diff, de)*100, cmiMAPeriod)
            self.exitFilter = 1 if (cmi[-1] > threshold) else 0
            
    def calExitIndicatorPart0(self, am, kind, period, upperK, lowerK, gene9):
        if kind==0:
            self.exitIndicatorPart0 = 0
        elif kind==1:
            self.exitIndicatorPart0 = 1 if(am.close[-1] > ta.SMA(am.close, period)[-1]) else -1
        elif kind==2:
            self.exitIndicatorPart0 = 1 if(am.close[-1] > ta.EMA(am.close, period)[-1]) else -1
        elif kind==3:
            exitBBANDSbuy = 1 if((am.close[-1] > ta.BBANDS(am.close, period, upperK, lowerK)[0][-1])) else 0
            exitBBANDSsell= -1 if((am.close[-1] < ta.BBANDS(am.close, period, upperK, lowerK)[-1][-1])) else 0
            self.exitIndicatorPart0 = exitBBANDSbuy + exitBBANDSsell
        elif kind==4:
            exitATRBANDSbuy = 1 if((am.close[-1] > (ta.MA(am.close, period)+upperK*ta.ATR(am.high, am.low, am.close, period))[-1])) else 0
            exitATRBANDSsell = -1 if((am.close[-1] < (ta.MA(am.close, period)-lowerK*ta.ATR(am.high, am.low, am.close, period))[-1]))else 0
            self.exitIndicatorPart0 = exitATRBANDSbuy + exitATRBANDSsell
  
    def calExitIndicatorPart1(self, am, kind, period, upperK, lowerK, gene9):
        if kind==0:
            self.exitIndicatorPart1 = 0
        elif kind==1:
            self.exitIndicatorPart1 = 1 if(am.close[-1] > ta.SMA(am.close, period)[-1]) else -1
        elif kind==2:
            self.exitIndicatorPart1 = 1 if(am.close[-1] > ta.EMA(am.close, period)[-1]) else -1
        elif kind==3:
            exitBBANDSbuy = 1 if((am.close[-1] > ta.BBANDS(am.close, period, upperK, lowerK)[0][-1])) else 0
            exitBBANDSsell= -1 if((am.close[-1] < ta.BBANDS(am.close, period, upperK, lowerK)[-1][-1])) else 0
            self.exitIndicatorPart1 = exitBBANDSbuy + exitBBANDSsell
        elif kind==4:
            exitATRBANDSbuy = 1 if((am.close[-1] > (ta.MA(am.close, period)+upperK*ta.ATR(am.high, am.low, am.close, period))[-1])) else 0
            exitATRBANDSsell = -1 if((am.close[-1] < (ta.MA(am.close, period)-lowerK*ta.ATR(am.high, am.low, am.close, period))[-1]))else 0
            self.exitIndicatorPart1 = exitATRBANDSbuy + exitATRBANDSsell
                    
    def myexit(self, am, paraDict, kind):
        ch = paraDict["ch%s"%kind]
        self.calExitFilter(am, ch[0], ch[1],ch[2],ch[3],ch[4])
        self.calExitIndicatorPart0(am, ch[20],ch[21],ch[22],ch[23],ch[24])
        self.calExitIndicatorPart1(am, ch[25],ch[26],ch[27],ch[28],ch[29])
        # exitFilter=0的时候执行exitIndicatorPart0   exitFilter=1的时候执行exitIndicatorPart1
        self.exit = self.exitIndicatorPart0*(1 if self.exitFilter==0 else 0)  +  self.exitIndicatorPart1 * self.exitFilter
        return self.exit