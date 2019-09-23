import talib as ta
import numpy as np
import pandas as pd
 
class dpSignal():

    def __init__(self):
        self.author = 'Wu Jiandong'

    def macdEnvironment(self, am, paraDict, signalControl=False, Min60Signal=False):
        "长周期如30Min,60MinK线产生的信号，帮助过滤短周期均线产生的噪声，帮助发现相对长周期的趋势"
        fastPeriod = paraDict["fastPeriod"]
        slowPeriod = int(fastPeriod * paraDict["fast_slow"])
        # slowPeriod = fastPeriod*3 # 长周期取短周期的3倍
        if signalControl == True: # 将30Min k线转换成60Min k线使用
            if Min60Signal==True:
                lseq = list(range(-1,-len(am.close)-1,-2))
                lseq.reverse()
            else: 
                lseq = list(range(-2,-len(am.close)-1,-2))
                lseq.reverse()
            dif, _, _ = ta.MACD(am.close[lseq], fastPeriod, slowPeriod, 1)
        else:
            dif, _, _ = ta.MACD(am.close, fastPeriod, slowPeriod, 5)
        if dif[-1]>dif[-2]:        
            envDirection = 1
        elif dif[-1]<dif[-2]:
            envDirection = -1
        else:
            envDirection = 0
        return envDirection, dif[-1]

    def emaCross(self, am5Min, am, paraDict, ExitSignal=False):
        fastPeriod = paraDict["EmaFastPeriod"]
        # slowPeriod = paraDict["EmaSlowPeriod"]
        slowPeriod = int(fastPeriod*paraDict['EmaFast_Slow'])
        sma = ta.EMA(am.close, fastPeriod)
        lma = ta.EMA(am.close, slowPeriod)
        goldenCross = sma[-1]>lma[-1] and sma[-2]<=lma[-2]
        deathCross = sma[-1]<lma[-1] and sma[-2]>=lma[-2]
        newHigh = sma[-1]>lma[-1] and am5Min.high[-1]>am.high[-2] # 当前5分钟bar高点突破上一根10分钟bar高点
        newLow = sma[-1]<lma[-1] and am5Min.low[-1]<am.low[-2]
        maCrossSignal = 0
        if ExitSignal: # 获取平仓信号
            "金叉平空仓，死叉平多仓"
            # if goldenCross:
            # if goldenCross or (sma[-1]>lma[-1] and sma[-1]>sma[-2]):
            if goldenCross:
                maCrossSignal = 1
            # elif deathCross:
            # elif deathCross or (sma[-1]<lma[-1] and sma[-1]<sma[-2]):
            elif deathCross:
                maCrossSignal = -1
        else: # 获取开仓信号
            "金叉或新高开多仓; 死叉或新低开空仓"
            if goldenCross or newHigh: 
                maCrossSignal = 1
            elif deathCross or newLow: 
                maCrossSignal = -1
        return maCrossSignal, sma, lma
    
    def atrFilter(self, am5Min, am, paraDict):
        atrPeriod = paraDict['atrPeriod']
        stdLongTimes = paraDict['stdLongTimes']
        # stdShortTimes = paraDict['stdShortTimes']
        stdShortTimes = stdLongTimes
        stdHighTimes = paraDict['stdHighTimes']
        close_atrPeriod = paraDict['close_atrPeriod']
        closePeriod = int(close_atrPeriod*atrPeriod)
        tr = ta.TRANGE(am.high,am.low,am.close)
        trStd = ta.STDDEV(tr, atrPeriod)[-1]
        ub = am.close[-closePeriod:].max()+(stdLongTimes*trStd)
        db = am.close[-closePeriod:].min()-(stdShortTimes*trStd)
        ubTooHigh = am.close[-closePeriod:].max()+(stdHighTimes*trStd)
        dbTooLow = am.close[-closePeriod:].min()-(stdHighTimes*trStd)
        if am5Min.close[-1]>ub and am5Min.close[-1]<ubTooHigh:
            atrFilterSignal = 1
        elif am5Min.close[-1]<db and am5Min.close[-1]>dbTooLow:
            atrFilterSignal = -1
        else:
            atrFilterSignal = 0
        return atrFilterSignal, ub, db, trStd

    def erSignalCal(self, am, paraDict):
        atrPeriod = paraDict['atrPeriod']
        er_atrPeriod = paraDict['er_atrPeriod']
        erThreshold_low = paraDict['erThreshold_low']
        erThreshold_high = paraDict['erThreshold_high']
        erMaPeriod = paraDict['erMaPeriod']
        erPeriod = int(er_atrPeriod*atrPeriod)
        direction = ta.MOM(am.close, erPeriod)
        volatility = ta.SUM(np.abs(ta.MOM(am.close, 1)), erPeriod)
        er = direction/volatility
        erMa = ta.MA(er, erMaPeriod)
        if erMa[-1]>=erThreshold_low and erMa[-1]<=erThreshold_high:
            erSignal = 1
        elif erMa[-1]<=-erThreshold_low and erMa[-1]>=-erThreshold_high:
            erSignal = -1
        else:
            erSignal = 0
        return erSignal, er



    
        