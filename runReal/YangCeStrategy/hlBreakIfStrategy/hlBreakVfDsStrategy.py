from vnpy.trader.vtConstant import *
import numpy as np
import talib as ta
import pandas as pd
from datetime import timedelta, datetime
from vnpy.trader.utils.templates.orderTemplate import * 
from vnpy.trader.app.ctaStrategy import ctaBase
from hlBreakSignalClass import hlBreakSignal

########################################################################
class hlBreakVfDsStrategy(OrderTemplate):
    className = 'hlBreakVfDs'

    # 参数列表，保存了参数的名称
    paramList = [
                 'author',
                 # 品种列表
                 'symbolList',
                 # envParameter 计算ADX环境的参数
                 'adxPeriod', 'adxLowThreshold',
                 'adxHighThreshold','adxMaxPeriod',
                 # signalParameter 计算信号的参数
                 'hlEntryPeriod','hlExitPeriod',
                 # 出场后停止的小时
                 'stopControlTime',
                 # 波动率过滤阈值
                 'volPeriod','highVolthreshold', 'lowVolthreshold',
                 # 加仓信号指标
                 'dsthreshold','dsPeriod',
                 'dsSemaPeriod', 'dsLemaPeriod',
                 # 止盈
                 'takeProfitPct',
                 # 价格变化百分比加仓， 加仓的乘数
                 'addPct','addMultipler','lotMultipler',
                 # 可加仓的次数
                 'posTime',
                 # 时间周期
                 'timeframeMap',
                 #  总秒，间隔，下单次数
                 'totalSecond', 'stepSecond','orderTime'
                 ]

    # 变量列表，保存了变量的名称
    varList = []
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['posDict', 'eveningDict']

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        super().__init__(ctaEngine, setting)
        self.paraDict = setting
        self.barPeriod = 500
        self.symbol = self.symbolList[0]
        self.lot = 0

        # varialbes
        self.orderDict = {'orderFirstLongSet':set(), 'orderFirstShortSet':set(), 
                         'orderSecondLongSet':set(),'orderSecondShortSet':set(),
                         'addLongSet':set(), 'addShortSet':set()}
        
        self.orderLastList = []
        self.lastOrderDict = {'nextExecuteTime': datetime(2000, 1, 1)}
        self.nPos = 0

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
                self.lastOrderDict['nextExecuteTime'] = self.currentTime + timedelta(hours=self.stopControlTime)
    
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
        self.lot = int(10000000/(bar.close*30)*0.3*0.5)
        # on bar下触发回测洗价逻辑
        self.checkOnPeriodStart(bar)
        # 定时清除已出场的单
        self.checkOnPeriodEnd(bar)
        for idSet in self.orderDict.values():
            self.delOrderID(idSet)
        # 执行策略逻辑
        self.strategy(bar)

    def on15MinBar(self, bar):
        longVolume = self.getHoldVolume(self.orderDict['orderFirstLongSet'])+self.getHoldVolume(self.orderDict['orderSecondLongSet'])+self.getHoldVolume(self.orderDict['addLongSet'])
        shortVolume = self.getHoldVolume(self.orderDict['orderFirstShortSet'])+self.getHoldVolume(self.orderDict['orderSecondShortSet'])+self.getHoldVolume(self.orderDict['addShortSet'])
        self.writeCtaLog('globalStatus%s'%(self.globalStatus))
        self.writeCtaLog('longVolume:%s, shortVolume:%s'%(longVolume, shortVolume))
        self.writeCtaLog('barClose%s'%(bar.close))

    def strategy(self, bar):
        envPeriod= self.timeframeMap["envPeriod"]
        filterPeriod= self.timeframeMap["filterPeriod"]
        signalPeriod= self.timeframeMap["signalPeriod"]
        tradePeriod= self.timeframeMap["tradePeriod"]
        addPosPeriod = self.timeframeMap["addPosPeriod"]
                
        # 根据出场信号出场
        highExitBand, lowExitBand, erCanAddPos= self.exitSignal(envPeriod, signalPeriod, addPosPeriod)
        if len(highExitBand) and len(lowExitBand):
            self.exitOrder(bar, highExitBand, lowExitBand, erCanAddPos)
        
        # 根据进场信号进场
        entrySig = self.entrySignal(envPeriod, filterPeriod, signalPeriod, tradePeriod)
        self.entryOrder(bar, entrySig)

        # 根据信号加仓
        addPosSig = self.addPosSignal(addPosPeriod)
        self.addPosOrder(bar, addPosSig)

    def isStopControled(self):
        return self.currentTime < self.lastOrderDict['nextExecuteTime']

    def exitSignal(self, envPeriod, signalPeriod, addPosPeriod):
        highExitBand, lowExitBand = np.array([]) , np.array([])
        dsCanAddPos = 0
        arrayPrepared1, amEnv = self.arrayPrepared(envPeriod)
        arrayPrepared2, amSignal = self.arrayPrepared(signalPeriod)
        arrayPrepared3, amAddPos = self.arrayPrepared(addPosPeriod)

        if arrayPrepared1 and arrayPrepared2 and arrayPrepared3:
            algorithm = hlBreakSignal()
            adxCanTrade, adxTrend = algorithm.adxEnv(amEnv, self.paraDict)
            if adxCanTrade ==1:
                highExitBand, lowExitBand = algorithm.hlExitWideBand(amSignal, self.paraDict)
            else:
                highExitBand, lowExitBand = algorithm.hlExitNorrowBand(amSignal, self.paraDict)
            dsCanAddPos, dsSma, dsLma = algorithm.dsAdd(amAddPos, self.paraDict)
        return highExitBand, lowExitBand, dsCanAddPos

    def exitOrder(self, bar, highExitBand, lowExitBand, dsCanAddPos):
        exitTouchLowest = (bar.low<lowExitBand[-2])
        exitTouchHighest = (bar.high>highExitBand[-2])

        if exitTouchLowest:
            for orderID in (self.orderDict['orderFirstLongSet']|self.orderDict['orderSecondLongSet']|self.orderDict['addLongSet']):
                op = self._orderPacks[orderID]
                self.composoryClose(op)
        elif exitTouchHighest:
            for orderID in (self.orderDict['orderFirstShortSet']|self.orderDict['orderSecondShortSet']|self.orderDict['addShortSet']):
                op = self._orderPacks[orderID]
                self.composoryClose(op)
        
        if not dsCanAddPos:
            if exitTouchHighest and len(self.orderDict['addLongSet'])>0:
                for orderID in self.orderDict['addLongSet']:
                    op = self._orderPacks[orderID]
                    self.composoryClose(op)
            if exitTouchLowest and len(self.orderDict['addShortSet'])>0:
                for orderID in self.orderDict['addShortSet']:
                    op = self._orderPacks[orderID]
                    self.composoryClose(op)

    def entrySignal(self, envPeriod, filterPeriod, signalPeriod, tradePeriod):
        entrySignal = 0
        arrayPrepared1, amEnv = self.arrayPrepared(envPeriod)
        arrayPrepared2, amFilter = self.arrayPrepared(filterPeriod)
        arrayPrepared3, amSignal = self.arrayPrepared(signalPeriod)
        arrayPrepared4, amTrade = self.arrayPrepared(tradePeriod)

        arrayPrepared = arrayPrepared1 and arrayPrepared2 and arrayPrepared3 and arrayPrepared4
        if arrayPrepared:
            algorithm = hlBreakSignal()
            adxCanTrade, adxTrend = algorithm.adxEnv(amEnv, self.paraDict)
            filterCanTrade, highVolPos = algorithm.fliterVol(amFilter, self.paraDict)
            if adxCanTrade ==1:
                highEntryBand, lowEntryBand = algorithm.hlEntryNorrowBand(amSignal, self.paraDict)
                filterVCanTrade = algorithm.filterNorrowPatternV(amSignal, self.paraDict)            
            else:
                highEntryBand, lowEntryBand = algorithm.hlEntryWideBand(amSignal, self.paraDict)
                filterVCanTrade = algorithm.filterWidePatternV(amSignal, self.paraDict)
            breakHighest = (amTrade.close[-1]>highEntryBand[-2]) and (amTrade.close[-2]<=highEntryBand[-2])
            breakLowest = (amTrade.close[-1]<lowEntryBand[-2]) and (amTrade.close[-2]>=lowEntryBand[-2])
            
            self.globalStatus['adxCanTrade'] = adxCanTrade
            self.globalStatus['filterCanTrade'] = filterCanTrade
            self.globalStatus['breakHighest'] = breakHighest
            self.globalStatus['breakLowest'] = breakLowest
            self.globalStatus['adxTrend'] = adxTrend[-1]
            self.globalStatus['highEntryBand'] = highEntryBand[-1]
            self.globalStatus['lowEntryBand'] = lowEntryBand[-1]

            if highVolPos:
                self.lotMultipler = 0.5
            else:
                self.lotMultipler = 1

            if (filterCanTrade == 1) and (filterVCanTrade==1):
                if not self.isStopControled():
                    if breakHighest:
                        entrySignal = 1
                    elif breakLowest:
                        entrySignal = -1
        return entrySignal

    def entryOrder(self, bar, entrySignal):
        buyExecute, shortExecute = self.priceExecute(bar)
        lotSize = int(self.lot * self.lotMultipler//2)
        orderPos = int(lotSize//self.orderTime)
        if entrySignal ==1:
            if not (self.orderDict['orderFirstLongSet'] or self.orderDict['orderSecondLongSet']):
                # 如果回测直接下单，如果实盘就分批下单
                    # for orderID in self.timeLimitOrder(ctaBase.CTAORDER_BUY, self.symbol, buyExecute, self.lot, 120).vtOrderIDs:
                stepOrder1 = self.makeStepOrder(ctaBase.CTAORDER_BUY, bar.vtSymbol, buyExecute, max(lotSize, 1), max(orderPos,1), self.totalSecond, self.stepSecond)                 
                orderID1 = stepOrder1.parentID
                self.orderDict['orderFirstLongSet'].add(orderID1)
                self.orderLastList.append(orderID1)
                # 第二单
                stepOrder2 = self.makeStepOrder(ctaBase.CTAORDER_BUY, bar.vtSymbol, buyExecute, max(lotSize, 1), max(orderPos,1), self.totalSecond, self.stepSecond)                 
                orderID2 = stepOrder2.parentID
                self.orderDict['orderSecondLongSet'].add(orderID2)
                self.orderLastList.append(orderID2)
                op = self._orderPacks[orderID2]
                self.setAutoExit(op,None, bar.close*(1+self.takeProfitPct))

        elif entrySignal ==-1:
            if not (self.orderDict['orderFirstShortSet'] or self.orderDict['orderSecondShortSet']):
                    # for orderID in self.timeLimitOrder(ctaBase.CTAORDER_SHORT, self.symbol, shortExecute, self.lot, 120).vtOrderIDs:
                # 第一单
                stepOrder1 = self.makeStepOrder(ctaBase.CTAORDER_SHORT, bar.vtSymbol, shortExecute, max(lotSize, 1), max(orderPos,1), self.totalSecond, self.stepSecond)
                orderID1 = stepOrder1.parentID                
                self.orderDict['orderFirstShortSet'].add(orderID1)
                self.orderLastList.append(orderID1)
                # 第二单
                stepOrder2 = self.makeStepOrder(ctaBase.CTAORDER_SHORT, bar.vtSymbol, shortExecute, max(lotSize, 1), max(orderPos,1), self.totalSecond, self.stepSecond)
                orderID2 = stepOrder2.parentID                
                self.orderDict['orderSecondShortSet'].add(orderID2)
                self.orderLastList.append(orderID2)
                op = self._orderPacks[orderID2]
                self.setAutoExit(op, None, bar.close*(1-self.takeProfitPct))

    # 计算可加仓的信号
    def addPosSignal(self, addPosPeriod):
        dsCanAddPos = 0
        arrayPrepared, amAddPos = self.arrayPrepared(addPosPeriod)
        if arrayPrepared:
            algorithm = hlBreakSignal()
            dsCanAddPos, dsSma, dsLma = algorithm.dsAdd(amAddPos, self.paraDict)
        return dsCanAddPos

    # 通过上一张单来获取成交价
    def addPosOrder(self, bar, addPosSignal):
        buyExecute, shortExecute = self.priceExecute(bar)
        holdLong = len(self.orderDict['orderFirstLongSet']|self.orderDict['orderSecondLongSet'])>0
        holdShort = len(self.orderDict['orderFirstShortSet']|self.orderDict['orderSecondShortSet'])>0
        
        algorithm = hlBreakSignal()
        if not (holdLong or holdShort):
            self.nPos = 0
            self.orderLastList = []
        else:
            lastOrderID = self.orderLastList[-1]
            op = self._orderPacks[lastOrderID]
            lastOrder = op.order.price_avg
            if lastOrder!=0:
                if addPosSignal:
                    if op.order.direction == constant.DIRECTION_LONG and (self.nPos < self.posTime):
                        if ((bar.close/lastOrder - 1) >= self.addPct) and ((bar.close/lastOrder - 1)<=2*self.addPct):
                            self.nPos += 1
                            addPosLot = algorithm.addLotList(self.paraDict)[self.nPos-1]*self.lot*self.lotMultipler
                            for orderID in self.timeLimitOrder(ctaBase.CTAORDER_BUY, bar.vtSymbol, buyExecute, max(addPosLot,1), 60).vtOrderIDs:
                                self.globalStatus['addPos'] = (self.nPos, addPosLot)
                                self.orderLastList.append(orderID)
                                addOp = self._orderPacks[orderID]
                                self.orderDict['addLongSet'].add(orderID)                    
                    elif op.order.direction == constant.DIRECTION_SHORT and (self.nPos < self.posTime):
                        if ((lastOrder/bar.close - 1) >= self.addPct) and ((lastOrder/bar.close - 1) <= 2*self.addPct):
                            self.nPos += 1
                            addPosLot = algorithm.addLotList(self.paraDict)[self.nPos-1]*self.lot*self.lotMultipler
                            for orderID in self.timeLimitOrder(ctaBase.CTAORDER_SHORT, bar.vtSymbol, shortExecute, max(addPosLot,1), 60).vtOrderIDs:
                                self.globalStatus['addPos'] = (self.nPos, addPosLot)
                                self.orderLastList.append(orderID)
                                addOp = self._orderPacks[orderID]
                                self.orderDict['addShortSet'].add(orderID)

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