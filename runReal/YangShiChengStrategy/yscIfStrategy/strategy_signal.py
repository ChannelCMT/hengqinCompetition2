import talib as ta
import numpy as np
import pandas as pd

class strategySignal():

    def __init__(self):
        self.author = 'YANG'

    def trend_filter_15min(self, am, paraDict):
        #判断趋势或者震荡
        np.seterr(divide='ignore', invalid='ignore')
        
        Env_trend_period = paraDict["Env_trend_period"]
        Env_trend_value = paraDict["Env_trend_value"]

        trendSignal = 0
        high = ta.MAX(am.high, Env_trend_period)
        low = ta.MIN(am.low, Env_trend_period)

        numerator = (high - low) / low
        oldValue = pd.Series(am.close).shift(Env_trend_period).values
        indicator = np.abs((am.close - oldValue) / oldValue) / numerator

        if indicator[-1] >= Env_trend_value:
            trendSignal = 1

        return trendSignal

    def trend_condition(self, am, paraDict):
        Env_trend_period = paraDict["trend_condition_period"]
        EfficiencyRation_threshold = paraDict["EfficiencyRation_threshold"]

        PriceChange = np.abs(am.close - (pd.Series(am.close).shift(1).values))
        IndividualPriceChange = np.sum(PriceChange[-Env_trend_period:])
        NetPriceChange = np.abs(am.close[-1] - am.close[-Env_trend_period-1])
        EfficiencyRation = NetPriceChange/IndividualPriceChange

        if EfficiencyRation >= EfficiencyRation_threshold:
            trendConditionSignal = 3
        else:
            trendConditionSignal = 2

        return trendConditionSignal


    #策略1：强趋势
    def Bollsignal_strend(self, am, paraDict):
        BOLL_MID_MA = paraDict["BOLL_MID_MA_strend"]
        BOLL_SD = paraDict["BOLL_SD_strend"]/10

        highma = ta.KAMA(am.high, BOLL_MID_MA)
        lowma = ta.KAMA(am.low, BOLL_MID_MA)
        Bollmid = ta.KAMA(am.close, BOLL_MID_MA)

        STD = (ta.VAR(am.close, BOLL_MID_MA) ** 0.5)
        Bollup = Bollmid + STD * BOLL_SD
        Bolldown = Bollmid - STD * BOLL_SD

        UpValue = (highma + Bollmid)/2 + STD
        LowValue = (lowma + Bollmid)/2 - STD

        Up_upper = (am.close[-1] > Bollup[-1])
        Down_lower = (am.close[-1] < Bolldown[-1])

        if Up_upper:
            BollSignal = 1
        elif Down_lower:
            BollSignal = -1  
        else:
            BollSignal = 0

        #出场准备
        if Bollup[-1] >= UpValue[-1]:
            LongExitValue = UpValue[-1]
        else:
            LongExitValue = Bollup[-1]

        if Bolldown[-1] <= LowValue[-1]:
            ShortExitValue = LowValue[-1]
        else:
            ShortExitValue = Bolldown[-1]
        
        ExitValue = (LongExitValue, ShortExitValue)
        
        return BollSignal, ExitValue

    #策略2：弱趋势
    def Bollsignal_wtrend(self, am, paraDict):
        BOLL_MID_MA = paraDict["BOLL_MID_MA_wtrend"]
        BOLL_SD = paraDict["BOLL_SD_wtrend"]/10
        ATR_period = paraDict["ATR_period"]
        ATR_threshold = paraDict["ATR_threshold"]
        ROC_Period = paraDict["ROC_Period"]
        ROC_MA_Period = paraDict["ROC_MA_Period"]

        highma = ta.KAMA(am.high, BOLL_MID_MA)
        lowma = ta.KAMA(am.low, BOLL_MID_MA)
        Bollmid = ta.KAMA(am.close, BOLL_MID_MA)

        STD = (ta.VAR(am.close, BOLL_MID_MA) ** 0.5)
        Bollup = Bollmid + STD * BOLL_SD
        Bolldown = Bollmid - STD * BOLL_SD

        UpValue = (highma + Bollmid)/2 + STD
        LowValue = (lowma + Bollmid)/2 - STD

        highmax = ta.MAX(am.high, BOLL_MID_MA)
        lowmin = ta.MIN(am.low, BOLL_MID_MA)

        ATRvalue = ta.ATR(am.high, am.low, am.close, ATR_period)
        ATRsignal = np.abs(am.close[-1] - am.close[-ATR_period]) / ATRvalue[-1]

        ROCvalue = ta.ROC(am.close, ROC_Period)
        rocMA = ta.MA(ROCvalue, ROC_MA_Period)

        if (ROCvalue[-1] > rocMA[-1]):
            ROCsignal = 1
        else:
            ROCsignal = 0


        Up_upper = (am.close[-1] > Bollup[-1]) and (ATRsignal > ATR_threshold) and (ROCsignal == 1)
        Down_lower = (am.close[-1] < Bolldown[-1]) and (ATRsignal > ATR_threshold) and (ROCsignal == 1)

        if Up_upper:
            BollSignal = 2
        elif Down_lower:
            BollSignal = -2
        else:
            BollSignal = 0

        #出场准备
        if Bollup[-1] >= UpValue[-1]:
            LongExitValue = UpValue[-1]
        else:
            LongExitValue = Bollup[-1]

        if Bolldown[-1] <= LowValue[-1]:
            ShortExitValue = LowValue[-1]
        else:
            ShortExitValue = Bolldown[-1]
        
        ExitValue = (LongExitValue, ShortExitValue)
        
        return BollSignal, ExitValue
    
    #策略3：震荡
    def Bollsignal_ntrend(self, am, paraDict):
        BOLL_MID_MA = paraDict["BOLL_MID_MA_ntrend"]
        BOLL_SD = paraDict["BOLL_SD_ntrend"]/10
        MA_Short_period = paraDict["MA_Short_period"]
        MA_Long_period = paraDict["MA_Long_period"]

        highma = ta.KAMA(am.high, BOLL_MID_MA)
        lowma = ta.KAMA(am.low, BOLL_MID_MA)
        Bollmid = ta.KAMA(am.close, BOLL_MID_MA)

        STD = (ta.VAR(am.close, BOLL_MID_MA) ** 0.5)
        Bollup = Bollmid + STD * BOLL_SD
        Bolldown = Bollmid - STD * BOLL_SD

        MA_Short = ta.KAMA(am.close, MA_Short_period)
        MA_Long = ta.KAMA(am.close, MA_Long_period)

        ATRvalue = ta.ATR(am.high, am.low, am.close, BOLL_MID_MA)

        if (am.close[-1] > Bolldown[-1]) and (am.close[-2] <= Bolldown[-2]) and (MA_Short[-1] > MA_Long[-1]):
            BollSignal = 3
        elif (am.close[-1] < Bollup[-1]) and (am.close[-2] >= Bollup[-2]) and (MA_Short[-1] < MA_Long[-1]):
            BollSignal = -3
        else:
            BollSignal = 0

        return BollSignal, ATRvalue[-1]

