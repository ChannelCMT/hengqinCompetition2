from vnpy.trader.vtConstant import *
import numpy as np
import talib as ta
import pandas as pd
from datetime import timedelta, datetime, time
from vnpy.trader.utils.templates.orderTemplate import * 
from vnpy.trader.app.ctaStrategy import ctaBase
from DoublePeriodSignal_v5 import dpSignal
########################################################################
# 更换数据频率
########################################################################
class DoublePeriodStrategy(OrderTemplate):
    className = 'DoubleMaStrategy'
    author = 'Wu Jiandong'

    # 参数列表，保存了参数的名称
    paramList = [
                 # 品种列表
                 'symbolList',
                 # 时间周期
                 'envPeriod', 'signalPeriod','signal5min',
                #  总秒，间隔，下单次数
                 'totalSecond', 'stepSecond', 'orderTime',
                 # 长周期MACD信号周期，signalPeriod采用默认值即可
                 'fastPeriod', 'slowPeriod',
                 # 长短均线信号周期
                 'EmaFastPeriod', 'EmaSlowPeriod', "EmaFast_Slow",
                 # ATR周期/ER周期和阈值等
                 'atrPeriod', 'er_atrPeriod', 'erThreshold_low', 'erThreshold_high', 
                 'stdLongTimes', 'stdShortTimes', 'close_atrPeriod',
                 # 止损止盈
                 'takeProfitLotRatio', 'expectReturn',
                 # 止损比例
                 'stopLossPct', 'stoplossPeriod'
                 # 加仓
                 'addPct', 'addLotTime', 'posTime'
                 ]

    # 变量列表，保存了变量的名称
    varList = []
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['posDict', 'eveningDict']

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        super().__init__(ctaEngine, setting)
        self.paraDict = setting
        self.barPeriod = 200
        self.lot = 0
        self.symbol = self.symbolList[0]
        self.orderAllList = [] # 记录成交的订单，以获取最新订单信息
        # 实例化信号
        self.algorithm = dpSignal()

        # 订单的集合
        self.orderDict = {
                            'orderLongSet':set(), 'orderShortSet':set(),
                            'order2LongSet':set(), 'order2ShortSet':set(),
                            'addLongSet':set(), 'addShortSet':set(),
                         }
       
        # 画图数据的字典
        self.chartLog = {
                            'datetime':[],
                            'envMa':[],
                            'fastMa':[],
                            'slowMa':[],
                            # 'upAtrFilter':[],
                            # 'dnAtrFilter':[],
                            'HigherAfterEntry':[],
                            'LowerAfterEntry':[],
                            'er':[],
                            'trStd':[],
                            'entrySignalLong':[],
                            'entrySignalShort':[],
                            # 'trendStatus':[]
                        }
        
        # 打印全局信号的字典
        self.globalStatus = {}

    def prepare_data(self):
        # for timeframe in list(set(self.timeframeMap.values())):
        #     self.registerOnBar(self.symbol, timeframe, None)
        self.registerOnBar(self.symbol, self.envPeriod, None)
        self.registerOnBar(self.symbol, self.signalPeriod, None)
        self.registerOnBar(self.symbol, self.signal5min, None)

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
        self.putEvent()
        # 策略参数
        self.nPos = 0
        self.stopLossPct = self.paraDict["stopLossPct"]
        self.stoplossPeriod = self.paraDict["stoplossPeriod"]
        self.addPct = self.paraDict["addPct"]
        self.posTime = self.paraDict["posTime"]
        self.expectReturn = self.paraDict["expectReturn"]
        # self.takeProfitLot = max(int(self.paraDict["takeProfitLotRatio"]*self.lot), 1)
        # 由于vnpy无法有效得到60Mk线，通过获得两次30Mink线变化一次来得到60MinK线
        if self.paraDict["envPeriod"][:-1] == '30':
            self.Min60Control = True
        elif self.paraDict["envPeriod"][:-1] == '60':
            raise Exception("时间设置有误。")
        else:
            self.Min60Control = False
        self.Min60Signal = True 
        self.close_signal = None

    ####################################### ↓↓↓↓无需修改区↓↓↓↓ #######################################↓
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

    def tradeTime(self, bar):
        if self.symbol[:2] in ['IF','IC','IH']:
            if time(9,30) <= bar.datetime.time() < time(15,0): # IF 使用
                return True
            else:
                return False
        else:
            print('不是股指期货。')
            if time(9,0) <= bar.datetime.time() < time(14,55): # 商品期货使用
                return True
            else:
                return False

    def lotDecide(self, bar, allCapital=10000000):
        capital = self.paraDict['capitalRatio'] * allCapital # 当前参数可用最大资金量
        lot = int((capital*0.3)/(bar.close*300*0.1))*0.5
        return lot

    ####################################### ↑↑↑↑无需修改区↑↑↑↑ #######################################↓

    def on5MinBar(self, bar):
        # 必须继承父类方法
        super().onBar(bar)
        # 交易时段执行
        if self.tradeTime(bar):
            # 定时控制，开始
            self.checkOnPeriodStart(bar)
            # 定时清除已出场的单
            self.checkOnPeriodEnd(bar)
            for idSet in self.orderDict.values():
                self.delOrderID(idSet)
            # 执行策略逻辑
            # if self.symbol[:2] == 'IF':
            #     self.lot = int((10000000*0.07)/(bar.close*300*0.1))
            # elif self.symbol[:2] == 'IC':
            #     self.lot = int((10000000*0.07)/(bar.close*200*0.12))
            # else:
            #     raise Exception("品种有误。")

            self.lot = self.lotDecide(bar, allCapital=10000000) # 通过API获取总资金量代替
            self.takeProfitLot = max(int(self.paraDict["takeProfitLotRatio"]*self.lot), 1) # 止盈单下单量
            self.strategy(bar)

    def on15MinBar(self, bar):
        self.writeCtaLog('orderDict:%s'%(self.orderDict))
        self.writeCtaLog('barClose:%s'%(bar.close))
    
    #---------------------------------------策略主体---------------------------------------
    def strategy(self, bar):
        envPeriod = self.envPeriod
        signalPeriod = self.signalPeriod
        signal5min = self.signal5min
        # 止损
        self.trailstoploss(bar, signalPeriod)
        # 止盈
        self.takeProfit(bar, signalPeriod)
        # 出场
        exitSig = self.exitSignal(signal5min, signalPeriod)
        self.exitOrder(bar, exitSig)
        # 进场
        entrySig = self.entrySignal(bar, envPeriod, signalPeriod, signal5min)
        self.entryOrder(bar, entrySig)
        # 加仓
        # self.addPosOrder(bar)

    def exitSignal(self, signal5min, signalPeriod):
        arrayPrepared1, amSignal = self.arrayPrepared(signalPeriod)
        arrayPrepared3, am5MinSig = self.arrayPrepared(signal5min)
        maCrossSignal = 0
        if arrayPrepared1 and arrayPrepared3:
            maCrossSignal, _, _ = self.algorithm.emaCross(am5MinSig, amSignal, self.paraDict, ExitSignal=True)
        return maCrossSignal
    
    def exitOrder(self, bar, exitSig):
        if exitSig==-1:
            for orderID in (self.orderDict['orderLongSet']|self.orderDict['order2LongSet']|self.orderDict['addLongSet']):
                op = self._orderPacks[orderID]
                self.composoryClose(op)
        elif exitSig==1:
            for orderID in (self.orderDict['orderShortSet']|self.orderDict['order2ShortSet']|self.orderDict['addShortSet']):
                op = self._orderPacks[orderID]
                self.composoryClose(op)

    def entrySignal(self, bar, envPeriod, signalPeriod, signal5min):
        entrySignal = 0
        arrayPrepared1, amEnv = self.arrayPrepared(envPeriod)
        arrayPrepared2, amSignal = self.arrayPrepared(signalPeriod)
        arrayPrepared3, am5MinSig = self.arrayPrepared(signal5min)
        if arrayPrepared1 and arrayPrepared2 and arrayPrepared3:
            # 修改成60Min数据
            if amEnv.close[-1] != self.close_signal: 
                self.Min60Signal = not self.Min60Signal
                self.close_signal = amEnv.close[-1]
            envDirection, envMa = self.algorithm.macdEnvironment(amEnv, self.paraDict, signalControl=self.Min60Control, Min60Signal=self.Min60Signal)
            maCrossSignal, fastMa, slowMa = self.algorithm.emaCross(am5MinSig, amSignal, self.paraDict)
            atrFilterSignal, ub, db, trStd = self.algorithm.atrFilter(am5MinSig, amSignal, self.paraDict)
            erSignal, er = self.algorithm.erSignalCal(amSignal, self.paraDict)
            if envDirection==1 and maCrossSignal==1 and atrFilterSignal==1 and erSignal==1: # 做多
                entrySignal = 1
            elif envDirection==-1 and maCrossSignal==-1 and atrFilterSignal==-1 and erSignal==-1: # 做空
                entrySignal = -1
            # 记录画图数据
            # self.chartLog['datetime'].append(datetime.strptime(amSignal.datetime[-1], "%Y%m%d %H:%M:%S"))
            self.chartLog['datetime'].append(bar.datetime)
            self.chartLog['envMa'].append(envMa)
            self.chartLog['fastMa'].append(fastMa[-1])
            self.chartLog['slowMa'].append(slowMa[-1])
            # self.chartLog['upAtrFilter'].append(ub)
            # self.chartLog['dnAtrFilter'].append(db)
            self.chartLog['er'].append(er[-1]*100)
            self.chartLog['trStd'].append(trStd)
            self.chartLog['entrySignalLong'].append(0.99*bar.low if entrySignal==1 else 0)
            self.chartLog['entrySignalShort'].append(0.99*bar.low if entrySignal==-1 else 0)
            # self.chartLog['entrySignalLong'].append(0.99*bar.low if (envDirection==1 and maCrossSignal==1 and atrFilterSignal==1) else 0)
            # self.chartLog['entrySignalShort'].append(0.99*bar.low if (envDirection==-1 and maCrossSignal==-1 and atrFilterSignal==-1) else 0)
            
        return entrySignal

    def entryOrder(self, bar, entrySignal):
        # 是否考虑平仓后进行反向开仓？
        buyExecute, shortExecute = self.priceExecute(bar)
        orderPos = self.lot//self.orderTime
        if not any(self.orderDict.values()): # 多空头均无持仓
            self.orderAllList = [] # 清空orderAllList列表
        else: # 若有持仓，且产生开仓信号，则先反向平仓
            self.exitOrder(bar, entrySignal)
        if entrySignal ==1:
            if not any([self.orderDict['orderLongSet'], self.orderDict['order2LongSet'], self.orderDict['addLongSet']]):
                # 分批下单
                stepOrder1 = self.makeStepOrder(ctaBase.CTAORDER_BUY, bar.vtSymbol, buyExecute, max(self.lot, 1), max(orderPos,1), self.totalSecond, self.stepSecond)                 
                orderID1 = stepOrder1.parentID
                self.orderDict['orderLongSet'].add(orderID1)
                self.orderAllList.append(orderID1)
    
                # 止盈单与普通单的下单手数不一样
                if not (self.takeProfitLot==0):
                    stepOrder2 = self.makeStepOrder(ctaBase.CTAORDER_BUY, bar.vtSymbol, buyExecute, max(self.takeProfitLot, 1), max(orderPos,1), self.totalSecond, self.stepSecond)                 
                    # stepOrder2 = self.makeStepOrder(ctaBase.CTAORDER_BUY, bar.vtSymbol, buyExecute, max(self.lot, 1), max(orderPos,1), self.totalSecond, self.stepSecond)                 
                    orderID2 = stepOrder2.parentID
                    self.orderDict['order2LongSet'].add(orderID2)
                    # self.orderAllList.append(orderID2)
                
        elif entrySignal ==-1:
            if not any([self.orderDict['orderShortSet'], self.orderDict['order2ShortSet'], self.orderDict['addShortSet']]):
                stepOrder1 = self.makeStepOrder(ctaBase.CTAORDER_SHORT, bar.vtSymbol, shortExecute, max(self.lot, 1), max(orderPos,1), self.totalSecond, self.stepSecond)
                orderID1 = stepOrder1.parentID                
                self.orderDict['orderShortSet'].add(orderID1)
                self.orderAllList.append(orderID1)

                # stepOrder2 = self.makeStepOrder(ctaBase.CTAORDER_SHORT, bar.vtSymbol, shortExecute, max(self.lot, 1), max(orderPos,1), self.totalSecond, self.stepSecond)
                if not (self.takeProfitLot==0):
                    stepOrder2 = self.makeStepOrder(ctaBase.CTAORDER_SHORT, bar.vtSymbol, shortExecute, max(self.takeProfitLot, 1), max(orderPos,1), self.totalSecond, self.stepSecond)
                    orderID2 = stepOrder2.parentID                
                    self.orderDict['order2ShortSet'].add(orderID2)
                    # self.orderAllList.append(orderID2)

     # 通过上一张单来获取成交价
    def addPosOrder(self, bar):
        if self.tradeTime(bar):
            buyExecute, shortExecute = self.priceExecute(bar)
            holdLong = len(self.orderDict['orderLongSet']|self.orderDict['order2LongSet'])>0
            holdShort = len(self.orderDict['orderShortSet']|self.orderDict['order2ShortSet'])>0
            
            if not (holdLong or holdShort): # 空仓
                self.nPos = 0
            elif self.orderAllList:
                lastOrderID = self.orderAllList[-1]
                op = self._orderPacks[lastOrderID]
                entryCost = op.order.price_avg
                if entryCost!=0:
                    addLotTime = [1, 2, 3]
                    if op.order.direction == constant.DIRECTION_LONG and (self.nPos < self.posTime):
                        # 浮盈达到加仓条件
                        if ((bar.close/entryCost - 1) >= self.addPct) and ((bar.close/entryCost - 1)<=2*self.addPct):
                            self.nPos += 1
                            # addPosLot = self.lot*self.addLotTime
                            addPosLot = self.lot*addLotTime[self.nPos-1]
                            for orderID in self.timeLimitOrder(ctaBase.CTAORDER_BUY, bar.vtSymbol, buyExecute, max(addPosLot,1), 60).vtOrderIDs:
                                # self.globalStatus['addPos'] = (self.nPos, addPosLot)
                                self.orderAllList.append(orderID)
                                self.orderDict['addLongSet'].add(orderID)
                    elif op.order.direction == constant.DIRECTION_SHORT and (self.nPos < self.posTime):
                        if ((entryCost/bar.close - 1) >= self.addPct) and ((entryCost/bar.close - 1) <= 2*self.addPct):
                            self.nPos += 1
                            # addPosLot = self.lot*self.addLotTime
                            addPosLot = self.lot*addLotTime[self.nPos-1]
                            for orderID in self.timeLimitOrder(ctaBase.CTAORDER_SHORT, bar.vtSymbol, shortExecute, max(addPosLot,1), 60).vtOrderIDs:
                                # self.globalStatus['addPos'] = (self.nPos, addPosLot)
                                self.orderAllList.append(orderID)
                                self.orderDict['addShortSet'].add(orderID)
    
    #---------------------------------------止损模块---------------------------------------
    def trailstoploss(self, bar, signalPeriod):  
        # 吊灯止损
        arrayPrepared1, amSignal = self.arrayPrepared(signalPeriod)
        if arrayPrepared1:
            orderLong = self.orderDict['orderLongSet']|self.orderDict['order2LongSet']|self.orderDict['addLongSet']
            orderShort = self.orderDict['orderShortSet']|self.orderDict['order2ShortSet']|self.orderDict['addShortSet']
            if not (orderLong|orderShort): # 空仓
                self.chartLog['LowerAfterEntry'].append(None)
                self.chartLog['HigherAfterEntry'].append(None)
            else: # 持仓则读取上一订单进场价格
                lastOrderId = self.orderAllList[-1]
                opLast = self._orderPacks[lastOrderId]
                entryCost = opLast.order.price_avg
                if orderLong and orderShort:
                    print(self.orderDict.items())
                    raise Exception('同时持仓，有问题')
            if orderLong: # 多头持仓
                self.LowerAfterEntry = max(self.LowerAfterEntry, entryCost, min(amSignal.low[-self.stoplossPeriod+1:].min(), bar.low))
                stopLongPrice = self.LowerAfterEntry-bar.open*self.stopLossPct
                self.chartLog['LowerAfterEntry'].append(stopLongPrice)
                self.chartLog['HigherAfterEntry'].append(None)
                if bar.low < stopLongPrice:
                    for orderId in orderLong:
                        op = self._orderPacks[orderId]
                        self.composoryClose(op)
            else:
                self.LowerAfterEntry = 0
            if orderShort: # 空头持仓
                self.HigherAfterEntry = min(self.HigherAfterEntry, entryCost, max(amSignal.high[-self.stoplossPeriod+1:].max(), bar.high))
                stopShortPrice = self.HigherAfterEntry+bar.open*self.stopLossPct
                self.chartLog['LowerAfterEntry'].append(None)
                self.chartLog['HigherAfterEntry'].append(stopShortPrice)
                if bar.high > stopShortPrice:
                    for orderId in orderShort:
                        op = self._orderPacks[orderId]
                        self.composoryClose(op)
            else:
                self.HigherAfterEntry = 10**7
                
    #---------------------------------------止盈模块---------------------------------------
    def takeProfit(self, bar, signalPeriod):
        # 固定比例止盈
        arrayPrepared1, _ = self.arrayPrepared(signalPeriod)
        if arrayPrepared1:
            if self.orderDict['order2LongSet']:
                orderID = list(self.orderDict['order2LongSet'])[0]
                entryCost = self._orderPacks[orderID].order.price_avg
                if bar.high > entryCost*(1+self.expectReturn):
                    for orderId in self.orderDict['order2LongSet']:
                        op = self._orderPacks[orderId]
                        self.composoryClose(op)
            elif self.orderDict['order2ShortSet']:
                orderID = list(self.orderDict['order2ShortSet'])[0]
                entryCost = self._orderPacks[orderID].order.price_avg
                if bar.low < entryCost*(1-self.expectReturn):
                    for orderId in self.orderDict['order2ShortSet']:
                        op = self._orderPacks[orderId]
                        self.composoryClose(op)

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