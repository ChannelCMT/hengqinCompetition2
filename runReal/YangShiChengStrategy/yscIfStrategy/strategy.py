from vnpy.trader.vtConstant import *
from vnpy.trader.app.ctaStrategy import CtaTemplate
import talib as ta
import numpy as np
from datetime import *
from strategy_signal import strategySignal

########################################################################
# 策略继承CtaTemplate
class SimpleStrategy(CtaTemplate):
    """一个简单的策略"""
    className = 'SimpleStrategy'
    author = 'YANG'
    
    # 策略变量
    transactionPrice = None # 记录成交价格
    
    # 参数列表
    paramList = [
                 # 时间周期
                 'timeframeMap',
                 # 取Bar的长度
                 'barPeriod',
                 # 30min环境信号
                 'Env_trend_period', 'Env_trend_value', 'trend_condition_period', 'EfficiencyRation_threshold',
                 # 强趋势
                 'BOLL_MID_MA_strend', 'BOLL_SD_strend',
                 # 较强趋势
                 'BOLL_MID_MA_wtrend', 'BOLL_SD_wtrend', 'ATR_period', 'ATR_threshold', 'ROC_Period', 'ROC_MA_Period',
                 #震荡
                 'BOLL_MID_MA_ntrend', 'BOLL_SD_ntrend', 'MA_Short_period', 'MA_Long_period', 'ntrend_Stop_Time',
                 # 加仓条件和次数
                 'addTime', 'addlot', 'addPre',
                 # 交易品种
                 'symbolList', 'Capital'
                ]    
    
    # 变量列表
    varList = []  
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['posDict', 'eveningDict']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        super().__init__(ctaEngine, setting)
        self.paraDict = setting
        self.symbol = self.symbolList[0]
        self.lot = 0
        self.wlot = 0
        self.chartLog = {
                'datetime':[],}
        
        self.Long_signal_entry = 0
        self.Long_add_entry = 0

        self.Short_signal_entry = 0
        self.Short_add_entry = 0

        self.cum_profit = 0

        self.pre_Env_signal = 0

    def prepare_data(self):
        for timeframe in list(set(self.timeframeMap.values())):
            self.registerOnBar(self.symbol, timeframe, None)

    def arrayPrepared(self, period):
        am = self.getArrayManager(self.symbol, period)
        if not am.inited:
            return False, None
        else:
            return True, am

    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略"""
        self.setArrayManagerSize(self.barPeriod)
        self.prepare_data()
        self.putEvent()

    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'策略启动')
        self.putEvent()
    
    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略"""
        self.writeCtaLog(u'策略停止')
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送"""
        pass
    
    def tradeTime(self, bar):
        if time(9,0) <= bar.datetime.time() < time(15,0):
            return True
        else:
            return False

    def strategy(self, bar):
        signalPeriod = self.timeframeMap["signalPeriod"]

        arrayPrepared1, am15 = self.arrayPrepared(signalPeriod)
        if arrayPrepared1:
            algorithm = strategySignal()
            Env_signal = algorithm.trend_filter_15min(am15, self.paraDict)
            ExitStatus = 0

            #趋势
            if Env_signal == 1:
                trendConditionSignal = algorithm.trend_condition(am15, self.paraDict)

                #强趋势出场
                if (self.Long_signal_entry == 1) or (self.Short_signal_entry == 1):
                    Entrysignal, Exit_value_strend = algorithm.Bollsignal_strend(am15, self.paraDict)
                    ExitStatus = self.exitOrder(bar, am15, Exit_value_strend)

                #弱趋势出场
                elif (self.Long_signal_entry == 2) or (self.Short_signal_entry == 2) or (self.Long_signal_entry == 3) or (self.Short_signal_entry == 3):
                    if self.pre_Env_signal != 0:
                        Entrysignal, Exit_value_wtrend = algorithm.Bollsignal_wtrend(am15, self.paraDict)
                        ExitStatus = self.exitOrder(bar, am15, Exit_value_wtrend)
                        

                #强趋势进场
                if not ExitStatus:
                    if trendConditionSignal == 3:
                        Entry_signal_strend, Exitvalue = algorithm.Bollsignal_strend(am15, self.paraDict)
                        self.entryOrder(bar, Entry_signal_strend, am15)
                    #弱趋势进场
                    elif trendConditionSignal == 2:
                        Entry_signal_wtrend, Exitvalue = algorithm.Bollsignal_wtrend(am15, self.paraDict)
                        self.entryOrder(bar, Entry_signal_wtrend, am15) 
                    
                    self.addPosOrder(bar, am15)

            #震荡
            else:
                if (self.Long_signal_entry == 1) or (self.Short_signal_entry == 1): #强趋势出场
                    Entrysignal, Exit_value_strend = algorithm.Bollsignal_strend(am15, self.paraDict)
                    ExitStatus = self.exitOrder(bar, am15, Exit_value_strend)
                    
                elif (self.Long_signal_entry == 2) or (self.Short_signal_entry == 2): #弱趋势出场
                    Entrysignal, Exit_value_wtrend = algorithm.Bollsignal_wtrend(am15, self.paraDict)
                    ExitStatus = self.exitOrder(bar, am15, Exit_value_wtrend)

                else: 
                    #震荡出场
                    Entry_signal_ntrend, ATR = algorithm.Bollsignal_ntrend(am15, self.paraDict)

                    if self.pre_Env_signal != 1:
                        if (self.Long_signal_entry == 3) or (self.Short_signal_entry == 3):
                            ExitStatus = self.exitOrder_ZD(bar)
                    
                    #震荡进场
                    if not ExitStatus:
                        self.entryOrder(bar, Entry_signal_ntrend, am15)
                        self.stoploss(bar, ATR)
                
            self.pre_Env_signal = Env_signal
 
            #self.chartLog['datetime'].append(datetime.strptime(am15.datetime[-1], "%Y%m%d %H:%M:%S"))
    
    def onBar(self, bar):
        pass

    def on5MinBar(self, bar):
        self.lot = int(10000000/(bar.close*30)*0.3*0.4)
        self.wlot = int(10000000/(bar.close*30)*0.3*0.3)
        self.strategy(bar)
        self.writeCtaLog('posDict:%s'%(self.posDict))
        self.writeCtaLog('barClose%s'%(bar.close))

    def entrySignal(self, am):
        pass

    def exitSignal(self):
        pass

    def exitOrder(self, bar, am, Exit_value):
        exitStatus = 0
        if self.tradeTime(bar):
            if (self.posDict[self.symbol+'_LONG'] > 0):
                if am.close[-1] < Exit_value[0]:
                    self.cancelAll()
                    self.sell(self.symbol, bar.close*0.99, self.posDict[self.symbol+'_LONG'])
                    self.Long_signal_entry = 0
                    self.Long_add_entry = 0
                    self.cum_profit = 0
                    exitStatus = 1

            if (self.posDict[self.symbol+'_SHORT'] > 0):           
                if am.close[-1] > Exit_value[1]:
                    self.cancelAll()
                    self.cover(self.symbol, bar.close*1.01, self.posDict[self.symbol+'_SHORT'])
                    self.Short_signal_entry = 0
                    self.Short_add_entry = 0
                    self.cum_profit = 0
                    exitStatus = 1

        return exitStatus 
    
    def exitOrder_ZD(self, bar):
        exitStatus = 0
        if self.tradeTime(bar):
            if (self.posDict[self.symbol+'_LONG'] > 0):
                last_entry_price = self.transactionPrice
                profit = bar.close - last_entry_price

                if (profit > 0):
                    profit_precent = profit / last_entry_price

                    if (profit_precent > self.cum_profit):
                        self.cum_profit = profit_precent
                    
                    if (self.cum_profit >= 0.02):
                        if profit_precent < (self.cum_profit - 0.01):
                            self.cancelAll()
                            self.sell(self.symbol, bar.close*0.99, self.posDict[self.symbol+'_LONG'])
                            self.Long_signal_entry = 0
                            self.Long_add_entry = 0
                            self.cum_profit = 0
                            exitStatus = 1

                    elif (self.cum_profit < 0.02) and (self.cum_profit > 0.005):
                        if profit_precent < (self.cum_profit - 0.005):
                            self.cancelAll()
                            self.sell(self.symbol, bar.close*0.99, self.posDict[self.symbol+'_LONG'])
                            self.Long_signal_entry = 0
                            self.Long_add_entry = 0
                            self.cum_profit = 0
                            exitStatus = 1

            if (self.posDict[self.symbol+'_SHORT'] > 0):
                last_entry_price = self.transactionPrice
                profit = last_entry_price - bar.close

                if (profit > 0):
                    profit_precent = profit / last_entry_price

                    if (profit_precent > self.cum_profit):
                        self.cum_profit = profit_precent
                    
                    if (self.cum_profit >= 0.02):
                        if profit_precent < (self.cum_profit - 0.01):
                            self.cancelAll()
                            self.cover(self.symbol, bar.close*1.01, self.posDict[self.symbol+'_SHORT'])
                            self.Short_signal_entry = 0
                            self.Short_add_entry = 0
                            self.cum_profit = 0
                            exitStatus = 1
                            
                    elif (self.cum_profit < 0.02) and (self.cum_profit > 0.005):
                        if profit_precent < (self.cum_profit - 0.005):
                            self.cancelAll()
                            self.cover(self.symbol, bar.close*1.01, self.posDict[self.symbol+'_SHORT'])
                            self.Short_signal_entry = 0
                            self.Short_add_entry = 0
                            self.cum_profit = 0
                            exitStatus = 1
        return exitStatus

    def stoploss(self, bar, atr):
        if self.tradeTime(bar):
            if (self.posDict[self.symbol+'_LONG'] > 0):
                if bar.close < (self.transactionPrice - atr * self.ntrend_Stop_Time):
                    self.cancelAll()
                    self.sell(self.symbol, bar.close*0.99, self.posDict[self.symbol+'_LONG'])
                    self.Long_signal_entry = 0
                    self.Long_add_entry = 0
                    self.cum_profit = 0

            if (self.posDict[self.symbol+'_SHORT'] > 0):
                if bar.close > (self.transactionPrice + atr * self.ntrend_Stop_Time):
                    self.cancelAll()
                    self.cover(self.symbol, bar.close*1.01, self.posDict[self.symbol+'_SHORT'])
                    self.Short_signal_entry = 0
                    self.Short_add_entry = 0
                    self.cum_profit = 0


    def entryOrder(self, bar, entrySignal, am):
        if self.tradeTime(bar):
            available_lot = self.Capital / am.close[-1]
            
            # 强趋势进场
            if (entrySignal == 1) and (self.Long_signal_entry != 1) and (self.posDict[self.symbol+'_LONG'] <= np.around(available_lot * 0.6)): 
                s_lot = np.around(available_lot * self.lot)
                # 如果没有空头持仓，则直接做多
                if  self.posDict[self.symbol+'_SHORT']==0:
                    self.buy(self.symbol, bar.close*1.01, s_lot)  # 成交价*1.01发送高价位的限价单，以最优市价买入进场
                # 如果有空头持仓，则先平空，再做多
                elif self.posDict[self.symbol+'_SHORT'] > 0:
                    self.cancelAll() # 撤销挂单
                    self.cover(self.symbol, bar.close*1.01, self.posDict[self.symbol+'_SHORT']) 
                    self.buy(self.symbol, bar.close*1.01, s_lot)

                self.Long_signal_entry = 1           

            # 如果做空时手头没有空头持仓
            elif (entrySignal == -1) and (self.Short_signal_entry != 1) and (self.posDict[self.symbol+'_SHORT'] <= np.around(available_lot * 0.6)):
                s_lot = np.around(available_lot * self.lot)
                if self.posDict[self.symbol+'_LONG']==0:
                    self.short(self.symbol, bar.close*0.99, s_lot) # 成交价*0.99发送低价位的限价单，以最优市价卖出进场
                elif self.posDict[self.symbol+'_LONG'] > 0:
                    self.cancelAll() # 撤销挂单
                    self.sell(self.symbol, bar.close*0.99, self.posDict[self.symbol+'_LONG'])
                    self.short(self.symbol, bar.close*0.99, s_lot)

                self.Short_signal_entry = 1

            #弱趋势进场
            if (entrySignal == 2) and (self.Long_signal_entry != 2) and (self.posDict[self.symbol+'_LONG'] <= np.around(available_lot * 0.3)): 
                s_lot = np.around(available_lot * self.wlot)
                # 如果没有空头持仓，则直接做多
                if  self.posDict[self.symbol+'_SHORT']==0:
                    self.buy(self.symbol, bar.close*1.01, s_lot)  # 成交价*1.01发送高价位的限价单，以最优市价买入进场
                # 如果有空头持仓，则先平空，再做多
                elif self.posDict[self.symbol+'_SHORT'] > 0:
                    self.cancelAll() # 撤销挂单
                    self.cover(self.symbol, bar.close*1.01, self.posDict[self.symbol+'_SHORT']) 
                    self.buy(self.symbol, bar.close*1.01, s_lot)

                self.Long_signal_entry = 2           

            # 如果做空时手头没有空头持仓
            elif (entrySignal == -2) and (self.Short_signal_entry != 2) and (self.posDict[self.symbol+'_SHORT'] <= np.around(available_lot * 0.3)):
                s_lot = np.around(available_lot * self.wlot)
                if self.posDict[self.symbol+'_LONG']==0:
                    self.short(self.symbol, bar.close*0.99, s_lot) # 成交价*0.99发送低价位的限价单，以最优市价卖出进场
                elif self.posDict[self.symbol+'_LONG'] > 0:
                    self.cancelAll() # 撤销挂单
                    self.sell(self.symbol, bar.close*0.99, self.posDict[self.symbol+'_LONG'])
                    self.short(self.symbol, bar.close*0.99, s_lot)

                self.Short_signal_entry = 2

            #震荡进场
            if (entrySignal == 3) and (self.Long_signal_entry == 0): 
                s_lot = np.around(available_lot * self.wlot)
                # 如果没有空头持仓，则直接做多
                if  self.posDict[self.symbol+'_SHORT']==0:
                    self.buy(self.symbol, bar.close*1.01, s_lot)  # 成交价*1.01发送高价位的限价单，以最优市价买入进场
                # 如果有空头持仓，则先平空，再做多
                elif self.posDict[self.symbol+'_SHORT'] > 0:
                    self.cancelAll() # 撤销挂单
                    self.cover(self.symbol, bar.close*1.01, self.posDict[self.symbol+'_SHORT']) 
                    self.buy(self.symbol, bar.close*1.01, s_lot)

                self.Long_signal_entry = 3           

            # 如果做空时手头没有空头持仓
            elif (entrySignal == -3) and (self.Short_signal_entry == 0):
                s_lot = np.around(available_lot * self.wlot)
                if self.posDict[self.symbol+'_LONG']==0:
                    self.short(self.symbol, bar.close*0.99, s_lot) # 成交价*0.99发送低价位的限价单，以最优市价卖出进场
                elif self.posDict[self.symbol+'_LONG'] > 0:
                    self.cancelAll() # 撤销挂单
                    self.sell(self.symbol, bar.close*0.99, self.posDict[self.symbol+'_LONG'])
                    self.short(self.symbol, bar.close*0.99, s_lot)

                self.Short_signal_entry = 3

            # 发出状态更新事件
            self.putEvent()

    def addPosOrder(self, bar, am):
        last_entry_price = self.transactionPrice
        available_lot = self.Capital / am.close[-1]
        add_lot = np.around(available_lot * self.addlot)
        # 反马丁格尔加仓模块
        if (self.posDict[self.symbol+'_LONG'] != 0) and (self.Long_add_entry <= self.addTime) and (self.posDict[self.symbol+'_LONG'] <= np.around(available_lot * 0.7)):    # 持有多头仓位并且加仓次数不超过1次
            if (bar.close/last_entry_price-1) >= self.addPre:  
                self.Long_add_entry += 1
                self.buy(self.symbol, bar.close*1.01, add_lot)  
        elif (self.posDict[self.symbol + "_SHORT"] != 0) and (self.Short_add_entry <= self.addTime) and (self.posDict[self.symbol+'_SHORT'] <= np.around(available_lot * 0.7)):    # 持有空头仓位并且加仓次数不超过1次
            if (last_entry_price/bar.close-1) >= self.addPre:   
                self.Short_add_entry += 1
                self.short(self.symbol, bar.close*0.99, add_lot)

    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送"""
        # 对于无需做细粒度委托控制的策略，可以忽略onOrder
        pass
    
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """收到成交推送"""
        if trade.offset == OFFSET_OPEN:  # 判断成交订单类型
            self.transactionPrice = trade.price # 记录成交价格

    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass