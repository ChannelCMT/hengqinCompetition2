from vnpy.trader.vtConstant import *
import numpy as np
import talib as ta
import pandas as pd
from datetime import timedelta, datetime
from vnpy.trader.utils.templates.orderTemplate import * 
from vnpy.trader.app.ctaStrategy import ctaBase
from ratelSignalClass import ratelSignal

########################################################################
class ratelStrategy(OrderTemplate):
    className = 'hlStrategy'
    author = 'Ivan'

    # 参数列表，保存了参数的名称
    paramList = [
                 # 品种列表
                 'symbolList',
                 # 时间周期
                 'timeframeMap',
                 # signalParameter 计算信号的参数
                 'hlEntryPeriod','hlExitPeriod',
                 ]

    # 变量列表，保存了变量的名称
    varList = ['lot']
    # 同步列表，保存了需要保存到数据库的变量名称

    syncList = ['posDict', 'eveningDict']

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        super().__init__(ctaEngine, setting)
        self.paraDict = setting
        self.barPeriod = 300
        self.symbol = self.symbolList[0]
        self.lot = 0
        # 实例化信号
        self.algorithm = ratelSignal()

        # 策略的个数
        self.strategyNumbers = 10

        # 订单的集合
        self.orderDict = {
                            'orderLongSet0':set(), 'orderShortSet0':set(),
                            'orderLongSet1':set(), 'orderShortSet1':set(),
                            'orderLongSet2':set(), 'orderShortSet2':set(),
                            'orderLongSet3':set(), 'orderShortSet3':set(),
                            'orderLongSet4':set(), 'orderShortSet4':set(),
                            'orderLongSet5':set(), 'orderShortSet5':set(),
                            'orderLongSet6':set(), 'orderShortSet6':set(),
                            'orderLongSet7':set(), 'orderShortSet7':set(),
                            'orderLongSet8':set(), 'orderShortSet8':set(),
                            'orderLongSet9':set(), 'orderShortSet9':set(),
                         }
       
        # # 画图数据的字典
        # self.chartLog = {
        #                     'datetime':[],
        #                     'highEntryBand':[],
        #                     'lowEntryBand':[]
        #                 }
        
        # 打印全局信号的字典
        self.globalStatus = {}

    def prepare_data(self):
        for timeframe in list(set(self.timeframeMap.values())):
            self.registerOnBar(self.symbol, timeframe, None)

    def arrayPrepared(self, period):
        am = self.getArrayManager(self.symbol, period)
        if not am.inited:
            return False, None
        else:
            return True, am
    # ----------------------------------------------------------------------
    def onInit(self):
        self.setArrayManagerSize(self.barPeriod)
        self.prepare_data()
        self.mail("chushihuaaaaaaaaaaaaaaaaaaaaaaaaa")
        self.putEvent()

    # ----------------------------------------------------------------------
    def onStart(self):
        self.putEvent()

    # ----------------------------------------------------------------------
    def onStop(self):
        self.putEvent()

    # 定时清除已经出场的单
    def delOrderID(self, orderSet):
        for orderId in list(orderSet):
            op = self._orderPacks[orderId]
            # 检查是否完全平仓
            if self.orderClosed(op):
                # 在记录中删除
                orderSet.discard(orderId)
    
    # 获得执行价格
    def priceExecute(self, bar):
        if bar.vtSymbol in self._tickInstance:
            tick = self._tickInstance[bar.vtSymbol]
            if tick.datetime >= bar.datetime:
                return tick.upperLimit * 0.99, tick.lowerLimit*1.01
        return bar.close*1.02, bar.close*0.98

    # 获取当前的持有仓位
    def getHoldVolume(self, orderSet):
        pos = 0
        for orderID in orderSet:
            op = self._orderPacks[orderID]
            holdVolume = op.order.tradedVolume
            pos+= holdVolume
        return pos

    def on5MinBar(self, bar):
        # 必须继承父类方法
        super().onBar(bar)
        self.lot = int(10000000/(bar.close*30)*0.6)
        # on bar下触发回测洗价逻辑
        # 定时控制，开始
        self.checkOnPeriodStart(bar)
        # 定时清除已出场的单
        self.checkOnPeriodEnd(bar)
        for idSet in self.orderDict.values():
            self.delOrderID(idSet)
        # 执行策略逻辑
        self.strategy(bar)

    def strategy(self, bar):
        signalPeriod= self.timeframeMap["signalPeriod"]
        # 根据出场信号出场
        exitSignal = self.exitSignal(signalPeriod)
        self.exitOrder(bar, exitSignal)
        
        # 根据进场信号进场
        entrySig = self.entrySignal(signalPeriod)
        self.entryOrder(bar, entrySig)

    def exitSignal(self,signalPeriod):
        exitSignal = list()
        arrayPrepared, amSignal = self.arrayPrepared(signalPeriod)
        if arrayPrepared:
            # 计算退出信号
            for i in range(self.strategyNumbers):
                exitSignal.append(self.algorithm.myexit(amSignal, self.paraDict, i))
            # 限定单笔最大亏损
            for j in range(self.strategyNumbers):
                if (self.orderDict['orderLongSet%s'%j]):
                    for orderID in (self.orderDict['orderLongSet%s'%j]):
                        op = self._orderPacks[orderID]
                        if (op.order.price - amSignal.close[-1]) > 400:
                            exitSignal[j] = -1
                if (self.orderDict['orderShortSet%s'%j]):
                    for orderID in (self.orderDict['orderShortSet%s'%j]):
                        op = self._orderPacks[orderID]
                        if (amSignal.close[-1] - op.order.price) > 400:
                            exitSignal[j] = 1
            return exitSignal

    def exitOrder(self, bar, exitSignal):
        for index, item in enumerate(exitSignal):
            if item==-1:
                for orderID in (self.orderDict['orderLongSet%s'%index]):
                    op = self._orderPacks[orderID]
                    self.composoryClose(op)
            elif item==1:
                for orderID in (self.orderDict['orderShortSet%s'%index]):
                    op = self._orderPacks[orderID]
                    self.composoryClose(op)

    def entrySignal(self, signalPeriod):
        entrySignal = list()
        arrayPrepared, amSignal = self.arrayPrepared(signalPeriod)
        
        if arrayPrepared:
            for i in range(self.strategyNumbers):
                entrySignal.append(self.algorithm.myentry(amSignal, self.paraDict, i))
        return entrySignal

    def entryOrder(self, bar, entrySignal):
        buyExecute, shortExecute = self.priceExecute(bar)
        for index, item in enumerate(entrySignal):
            if item ==1:
                if (not (self.orderDict['orderLongSet%s'%index])) and (not (self.orderDict['orderShortSet%s'%index])):
                    # 限时下单
                    for orderID in self.timeLimitOrder(ctaBase.CTAORDER_BUY, self.symbol, buyExecute, int(self.lot/self.strategyNumbers), 120).vtOrderIDs:
                        self.orderDict['orderLongSet%s'%index].add(orderID)

            elif item ==-1:
                if (not (self.orderDict['orderLongSet%s'%index])) and (not (self.orderDict['orderShortSet%s'%index])):
                    for orderID in self.timeLimitOrder(ctaBase.CTAORDER_SHORT, self.symbol, shortExecute, int(self.lot/self.strategyNumbers), 120).vtOrderIDs:
                        self.orderDict['orderShortSet%s'%index].add(orderID)

 # ----------------------------------------------------------------------
    def onOrder(self, order):
        super().onOrder(order)
        pass

    # ----------------------------------------------------------------------
    # 成交后用成交价设置第一张止损止盈
    def onTrade(self, trade):
        pass

    def onStopOrder(self, so):
        pass