from vnpy.trader.vtConstant import *
import numpy as np
import talib as ta
import pandas as pd
from datetime import timedelta, datetime
from vnpy.trader.utils.templates.orderTemplate import * 
from vnpy.trader.app.ctaStrategy import ctaBase
from adxSoupClass import adxSoupSignal

########################################################################
class adxSoupStrategy(OrderTemplate):
    className = 'adxSoup'

    # 参数列表，保存了参数的名称
    paramList = [
                 'author',
                 # 时间周期
                 'timeframeMap',
                 #  总秒，间隔，下单次数
                 'totalSecond', 'stepSecond','orderTime',
                 # 品种列表
                 'symbolList',
                 # envParameter
                 'adxPeriod','adxMaPeriod', 'adxThreshold',
                 # signalParameter 计算信号的参数
                 'hlPeriod','hlExitPeriod',
                 'distanceMin','distanceMax',
                 # 止盈
                 'dangerousMinPct', 'dangerousMaxPct',
                 'pctPeriod', 'clipPct', 'hourCount',
                 'stopControlMin',
                 ]

    # 变量列表，保存了变量的名称
    varList = []
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['posDict', 'eveningDict']

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        super().__init__(ctaEngine, setting)
        self.paraDict = setting
        self.barPeriod = 800
        self.symbol = self.symbolList[0]
        self.lot = 0
        self.trailingPct = 0
        self.algorithm = adxSoupSignal()
        self.lastOrderDict = {'nextExecuteTime': datetime(2000, 1, 1)}


        # varialbes
        self.orderDict = {
                         'order1LongSet':set(), 'order1ShortSet':set(), 
                         'order2LongSet':set(),'order2ShortSet':set(),
                         }
        self.orderAllList = []        
        # 打印全局信号的字典
        self.globalStatus = {}
        self.chartLog = {
                        'datetime':[],
                        'adx':[],
                        'delayHigh':[],
                        'delayLow':[],
                        'newHigh':[],
                        'newLow':[],
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
                self.lastOrderDict['nextExecuteTime'] = self.currentTime + timedelta(minutes=self.stopControlMin)

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
        self.lot = int(10000000/(bar.close*30)*0.7)
        # on bar下触发回测洗价逻辑
        # 定时控制，开始
        self.checkOnPeriodStart(bar)
        # 实盘下单手数按此方法调整
        self.checkOnPeriodEnd(bar)
        # 定时清除已出场的单
        for idSet in self.orderDict.values():
            self.delOrderID(idSet)
        # 执行策略逻辑
        self.strategy(bar)

    def on15MinBar(self, bar):
        engineType = self.getEngineType()  # 判断engine模式
        if engineType != 'backtesting':
            longVolume = self.getHoldVolume(self.orderDict['order1LongSet'])+self.getHoldVolume(self.orderDict['order2LongSet'])
            shortVolume = self.getHoldVolume(self.orderDict['order1ShortSet'])+self.getHoldVolume(self.orderDict['order2ShortSet'])
            self.writeCtaLog('globalStatus%s'%(self.globalStatus))
            self.writeCtaLog('longVolume:%s, shortVolume:%s'%(longVolume, shortVolume))
            self.notifyPosition('longVolume', longVolume, self.author)
            self.notifyPosition('shortVolume', shortVolume, self.author)

    def strategy(self, bar):
        trendPeriod= self.timeframeMap["trendPeriod"]
        signalPeriod= self.timeframeMap["signalPeriod"]
        tradePeriod= self.timeframeMap["tradePeriod"]
        
        # 根据出场信号出场
        exitLong, exitShort = self.exitSignal(bar, signalPeriod, tradePeriod)
        self.exitOrder(bar, exitLong, exitShort)
        
        # 根据进场信号进场
        entrySig = self.entrySignal(trendPeriod, signalPeriod, tradePeriod)
        self.entryOrder(bar, entrySig)

    def isStopControled(self):
        return self.currentTime < self.lastOrderDict['nextExecuteTime']

    def exitSignal(self, bar, signalPeriod, tradePeriod):
        arrayPrepared, amSignal = self.arrayPrepared(signalPeriod)

        exitLong, exitShort = 0, 0
        if arrayPrepared:
            exitHigh, exitLow = self.algorithm.hlExitSignal(amSignal, self.paraDict)
            if bar.high>exitHigh[-2]:
                exitShort = 1
            if bar.low<exitLow[-2]:
                exitLong = 1
        return exitLong, exitShort

    def exitOrder(self, bar, exitLong, exitShort):
        if exitLong:
            for orderID in (
                            self.orderDict['order1LongSet']|self.orderDict['order2LongSet']
                           ):
                op = self._orderPacks[orderID]
                self.composoryClose(op)
        if exitShort:
            for orderID in (
                            self.orderDict['order1ShortSet']|self.orderDict['order2ShortSet']
                           ):
                op = self._orderPacks[orderID]
                self.composoryClose(op)

    def entrySignal(self, trendPeriod, signalPeriod, tradePeriod):
        arrayPrepared1, amTrend = self.arrayPrepared(trendPeriod)
        arrayPrepared2, amSignal = self.arrayPrepared(signalPeriod)
        arrayPrepared3, amTrade = self.arrayPrepared(tradePeriod)

        entrySignal = 0
        if arrayPrepared1 and arrayPrepared2 and arrayPrepared3:
            adxNoTrend, adx = self.algorithm.adxEnv(amTrend, self.paraDict)
            delayHigh, delayLow, newHigh, newLow, dangerous = self.algorithm.soupSignal(amSignal, self.paraDict)

            self.chartLog['datetime'].append(datetime.strptime(amSignal.datetime[-1], "%Y%m%d %H:%M:%S"))
            self.chartLog['adx'].append(adx[-1])
            self.chartLog['delayHigh'].append(delayHigh)
            self.chartLog['delayLow'].append(delayLow)
            self.chartLog['newHigh'].append(newHigh[-1])
            self.chartLog['newLow'].append(newLow[-1])
            
            creatHigh, creatLow = 0, 0
            if delayHigh:
                creatHigh = newHigh[-1]>delayHigh
                revertDn = (amTrade.close[-1]<delayHigh) and (amTrade.close[-2]>delayHigh)
            if delayLow:
                creatLow = newLow[-1]<delayLow
                revertUp = (amTrade.close[-1]>delayLow) and (amTrade.close[-2]<delayLow)

            turpleSoup = 0
            if creatLow and revertUp:
                turpleSoup = 1
            elif creatHigh and revertDn:
                turpleSoup = -1

            self.globalStatus['turpleSoup'] = turpleSoup
            self.globalStatus['adxNoTrend'] = [adxNoTrend, adx[-3:]]
            self.globalStatus['newHigh'] = newHigh[-3:]
            self.globalStatus['delayHigh'] = delayHigh
            self.globalStatus['newLow'] = newLow[-3:]
            self.globalStatus['delayLow'] = delayLow
            self.globalStatus['dangerous'] = dangerous

            if not self.isStopControled():
                if (adxNoTrend==1) and dangerous!='lowDangerous':
                    if (turpleSoup==1):
                        entrySignal = 1
                        self.trailingPct = self.algorithm.pctTrailing(amTrend, self.paraDict)
                    elif (turpleSoup==-1) and dangerous!='highDangerous':
                        entrySignal = -1
                        self.trailingPct = self.algorithm.pctTrailing(amTrend, self.paraDict)
        return entrySignal

    def entryOrder(self, bar, entrySignal):
        buyExecute, shortExecute = self.priceExecute(bar)
        lotSize = self.lot
        orderPos = lotSize//self.orderTime
        if not (self.orderDict['order1LongSet'] or self.orderDict['order1ShortSet']):
            self.orderAllList = []
        if entrySignal>0:
            if not (self.orderDict['order1LongSet']):
                # 如果回测直接下单，如果实盘就分批下单
                stepOrder1 = self.makeStepOrder(ctaBase.CTAORDER_BUY, bar.vtSymbol, buyExecute, max(lotSize, 1), max(orderPos,1), self.totalSecond, self.stepSecond)                 
                orderID1 = stepOrder1.parentID
                self.orderDict['order1LongSet'].add(orderID1)
                self.orderAllList.append(orderID1)
                # 第二单
                stepOrder2 = self.makeStepOrder(ctaBase.CTAORDER_BUY, bar.vtSymbol, buyExecute, max(lotSize, 1), max(orderPos,1), self.totalSecond, self.stepSecond)                 
                orderID2 = stepOrder2.parentID
                self.orderDict['order2LongSet'].add(orderID2)
                op2 = self._orderPacks[orderID2]
                self.setAutoExit(op2, None, bar.close*(1+self.trailingPct))
        elif entrySignal<0:
            if not (self.orderDict['order1ShortSet']):
                # 第一单
                stepOrder1 = self.makeStepOrder(ctaBase.CTAORDER_SHORT, bar.vtSymbol, shortExecute, max(lotSize, 1), max(orderPos,1), self.totalSecond, self.stepSecond)
                orderID1 = stepOrder1.parentID                
                self.orderDict['order1ShortSet'].add(orderID1)
                self.orderAllList.append(orderID1)
                # 第二单
                stepOrder2 = self.makeStepOrder(ctaBase.CTAORDER_SHORT, bar.vtSymbol, shortExecute, max(lotSize, 1), max(orderPos,1), self.totalSecond, self.stepSecond)
                orderID2 = stepOrder2.parentID                
                self.orderDict['order2ShortSet'].add(orderID2)
                op2 = self._orderPacks[orderID2]
                self.setAutoExit(op2, None, bar.close*(1-self.trailingPct))

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