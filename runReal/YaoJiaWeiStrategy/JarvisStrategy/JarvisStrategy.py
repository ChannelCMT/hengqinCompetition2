"""
这里的Demo是一个最简单的双均线策略实现
"""

from __future__ import division
from vnpy.trader.vtConstant import *
from vnpy.trader.app.ctaStrategy import CtaTemplate
import talib as ta
import numpy as np
from datetime import datetime
from JarvisSignalClass import JarvisSignal


########################################################################
# 策略继承CtaTemplate
class JarvisStrategy(CtaTemplate):
    className = 'JarvisStrategy'
    author = 'Jarvis'
    
    # 策略变量
    transactionPrice = {} # 记录成交价格
    
     # 参数列表
    paramList = [
                 'symbolList', 'barPeriod', 'lot',
                 'timeframeMap',
                 'atrPeriod', 'smallAtrTime','bigAtrTime',
                 'fastperiod', 'slowperiod','signalperiod',
                 'BBandPeriod', 'adxPeriod',"emaPeriod1",
                 'fastk_period','slowk_period','slowk_matype','slowd_period','slowd_matype',
                 'stopAtrTime',
                 'lowVolThreshold',
                 'hlMaPeriod','maPeriod',
                 "posTime", 'addPct'
                ]    
    
    # 变量列表
    varList = ['transactionPrice']  
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['posDict', 'eveningDict']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        # 首先找到策略的父类（就是类CtaTemplate），然后把DoubleMaStrategy的对象转换为类CtaTemplate的对象
        super().__init__(ctaEngine, setting)
        self.paraDict = setting
        self.symbol = self.symbolList[0]
        self.transactionPrice = None # 生成成交价格的字典
        self.trendStatus = None
        self.nPos = 0

        self.chartLog = {
                'datetime':[],
                'upperBand':[],
                'lowerBand':[]
                }

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
    
    def onBar(self, bar):
        pass

    def on5MinBar(self, bar):
        self.strategy(bar)
        self.lot = int(10000000/(bar.close*30)*0.3)
        self.writeCtaLog('posDict:%s'%(self.posDict))
        print('posDict:', self.posDict)


    def strategy(self, bar):
        signalPeriod= self.timeframeMap["signalPeriod"]
        # 根据出场信号出场
        trendStatus, exitLongBandSignal, exitShortBandSignal, atr = self.exitSignal(signalPeriod)
        exitStatus = self.exitOrder(bar, trendStatus, exitLongBandSignal, exitShortBandSignal, atr)

        # 根据进场信号进场
        filterCanTrade, breakUpperBand, breakLowerBand = self.entrySignal(signalPeriod)
        if not exitStatus:
            self.entryOrder(bar, filterCanTrade, breakUpperBand, breakLowerBand, trendStatus)

        self.addPosOrder(bar)

    def exitSignal(self, signalPeriod):
        arrayPrepared, amSignal = self.arrayPrepared(signalPeriod)
        algorithm = JarvisSignal()
        trendStatus = 0
        exitLongBandSignal, exitShortBandSignal = 0, 0
        if arrayPrepared:
            trendStatus = algorithm.Env(amSignal, self.paraDict)
            exitLongBandSignal, exitShortBandSignal = algorithm.maExit(amSignal, self.paraDict)
            atr = algorithm.atrStoploss(amSignal, self.paraDict)
        return trendStatus, exitLongBandSignal, exitShortBandSignal, atr

    def exitOrder(self, bar, trendStatus, exitLongBandSignal, exitShortBandSignal, atr):
        exitStatus = 0
        # 执行出场条件
        if trendStatus==0:
        #if trendStatus==1 or trendStatus==-1:
            if exitLongBandSignal and self.posDict[self.symbol+'_LONG']>0:
                self.sell(self.symbol, bar.close*0.99, self.posDict[self.symbol+'_LONG'])
                exitStatus = 1
            if exitShortBandSignal and self.posDict[self.symbol+'_SHORT']>0:
                self.cover(self.symbol, bar.close*1.01, self.posDict[self.symbol+'_SHORT'])
                exitStatus = 1
        else:
            # 止损出场
            longStop, shortStop = None, None
            if self.transactionPrice:
                longStop = self.transactionPrice-self.stopAtrTime*atr[-1]
                shortStop = self.transactionPrice+self.stopAtrTime*atr[-1]
            # 洗价器
            if (self.posDict[self.symbol+'_LONG'] > 0):
                if (bar.low < longStop):
                    # print('LONG stopLoss')
                    self.cancelAll()
                    self.sell(self.symbol,bar.close*0.99, self.posDict[self.symbol+'_LONG'])
                    exitStatus = 1
            elif (self.posDict[self.symbol+'_SHORT'] > 0):
                if (bar.high > shortStop):
                    # print('SHORT stopLoss')
                    self.cancelAll()
                    self.cover(self.symbol,bar.close*1.01, self.posDict[self.symbol+'_SHORT'])
                    exitStatus = 1
        return exitStatus


    def entrySignal(self, signalPeriod):
        arrayPrepared, amSignal = self.arrayPrepared(signalPeriod)
        algorithm = JarvisSignal()
        breakUpperBand, breakLowerBand = 0, 0
        if arrayPrepared:
            trendStatus = algorithm.Env(amSignal, self.paraDict)
            filterCanTrade = algorithm.filterLowAtr(amSignal, self.paraDict)
            if trendStatus ==0:
                breakUpperBand, breakLowerBand, upperBand, lowerBand = algorithm.breakBandSignal(amSignal, self.paraDict)
            elif trendStatus==1 or trendStatus==-1:
                breakUpperBand, breakLowerBand, upperBand, lowerBand = algorithm.breakTrendBand(amSignal, self.paraDict)
                # 画图记录数据
            self.chartLog['datetime'].append(datetime.strptime(amSignal.datetime[-1], "%Y%m%d %H:%M:%S"))
            self.chartLog['upperBand'].append(upperBand)
            self.chartLog['lowerBand'].append(lowerBand)
            
        return filterCanTrade, breakUpperBand, breakLowerBand

    def entryOrder(self, bar, filterCanTrade, breakUpperBand, breakLowerBand, trendStatus):
        if filterCanTrade==1:
            if trendStatus==1 or trendStatus==0:
                if breakUpperBand and (self.posDict[self.symbol+'_LONG']==0):
                    if  self.posDict[self.symbol+'_SHORT']==0:
                        self.buy(self.symbol, bar.close*1.01, self.lot)  # 成交价*1.01发送高价位的限价单，以最优市价买入进场
                    # 如果有空头持仓，则先平空，再做多
                    elif self.posDict[self.symbol+'_SHORT'] > 0:
                        self.cancelAll() # 撤销挂单
                        self.cover(self.symbol, bar.close*1.01, self.posDict[self.symbol+'_SHORT']) 
                        self.buy(self.symbol, bar.close*1.01, self.lot)
            elif trendStatus==-1 or trendStatus==0:
                if breakLowerBand and (self.posDict[self.symbol+'_SHORT']==0):
                    if  self.posDict[self.symbol+'_LONG']==0:
                        self.short(self.symbol, bar.close*0.99, self.lot) # 成交价*0.99发送低价位的限价单，以最优市价卖出进场
                    elif self.posDict[self.symbol+'_LONG'] > 0:
                        self.cancelAll() # 撤销挂单
                        self.sell(self.symbol, bar.close*0.99, self.posDict[self.symbol+'_LONG'])
                        self.short(self.symbol, bar.close*0.99, self.lot)

    def addPosOrder(self, bar):
        lastOrder=self.transactionPrice
        if self.posDict[self.symbol+'_LONG'] ==0 and self.posDict[self.symbol + "_SHORT"] == 0:
            self.nPos = 0
        # 反马丁格尔加仓模块______________________________________
        if (self.posDict[self.symbol+'_LONG']!=0 and self.nPos < self.posTime):    # 持有多头仓位并且加仓次数不超过3次
            if bar.close/lastOrder-1>= self.addPct:   # 计算盈利比例,达到2%
                self.nPos += 1  # 加仓次数减少 1 次
                addLot = self.lot*(2**self.nPos)
                self.buy(self.symbol,bar.close*1.02,addLot)  # 加仓 2手、4手、8手
        elif (self.posDict[self.symbol + "_SHORT"] != 0 and self.nPos < self.posTime):    # 持有空头仓位并且加仓次数不超过3次
            if lastOrder/bar.close-1 >= self.addPct:   # 计算盈利比例,达到2%
                self.nPos += 1  # 加仓次数减少 1 次
                addLot = self.lot*(2**self.nPos)
                self.short(self.symbol,bar.close*0.98,addLot)  # 加仓 2手、4手、8手
    
    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送"""
        if order.offset == OFFSET_OPEN:  # 判断成交订单类型
            self.transactionPrice = order.price_avg # 记录成交价格
        # 对于无需做细粒度委托控制的策略，可以忽略onOrder
        pass
    
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """收到成交推送"""
        pass
    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass