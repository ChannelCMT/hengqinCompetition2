from vnpy.trader.vtConstant import *
import numpy as np
import talib as ta
import pandas as pd
from datetime import timedelta, datetime, time
from vnpy.trader.utils.templates.orderTemplate import * 
from vnpy.trader.app.ctaStrategy import ctaBase
from SkewSignalClass_V3 import skewBaseSignal
########################################################################
# 目前版本：未引入加仓管理，未另设出场信号，目前产生反向进场信号时出场，或止盈止损出场。
########################################################################
class SkewBaseStrategy(OrderTemplate):
    className = 'SkewBaseStrategy'
    author = 'Claudio, Wu Jiandong'

    # 参数列表，保存了参数的名称
    paramList = [
                 # 品种列表
                 'symbolList', 'lot',
                 # 时间周期
                 'timeframeMap',
                #  总秒，间隔，下单次数
                 'totalSecond', 'stepSecond', 'orderTime',
                 # 止损止盈
                 'takeProfitLotRatio', 'expectReturn',
                 # 止损比例
                 'stopLossPct', 'stoplossPeriod',
                 # 加仓
                 'addPct', 'addLotTime', 'posTime',
                 # 出场后停止的小时
                 'stopControlTime',
                 # 
                 "fastPeriod", "volumeMaPeriod", "volumeStdMultiple",
                 "skewShortPeriod", "skewShortThreshold",
                 "skewLongPeriod", "skewLongThreshold_left", "skewLongThreshold_right"
                 ]

    # 变量列表，保存了变量的名称
    varList = ['lot']
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['posDict', 'eveningDict']

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        super().__init__(ctaEngine, setting)
        self.paraDict = setting
        self.barPeriod = 600
        self.symbol = self.symbolList[0]
        self.orderAllList = [] # 记录成交的订单，以获取最新订单信息
        # 实例化信号
        self.algorithm = skewBaseSignal()
        # 订单的集合
        self.orderDict = {
                            'orderLongSet':set(), 'orderShortSet':set(),
                            'order2LongSet':set(), 'order2ShortSet':set(),
                            'addLongSet':set(), 'addShortSet':set(),
                         }
        # 画图数据的字典
        self.chartLog = {
                            'datetime':[],
                            'HigherAfterEntry':[],
                            'LowerAfterEntry':[],
                            # 'envMa':[],
                            'volumeUpper':[],
                            'maVolume':[],
                            'shortSkew':[],
                            'longSkew':[],
                            'close':[],
                            # 'skewThreshold_left':[],
                            # 'skewThreshold_right':[]
                        }
        # 打印全局信号的字典
        self.globalStatus = {}

    def prepare_data(self):
        # for timeframe in list(set(self.timeframeMap.values())):
        #     self.registerOnBar(self.symbol, timeframe, None)
        self.envPeriod = self.paraDict["envPeriod"]
        self.signalPeriod = self.paraDict["signalPeriod"]
        self.registerOnBar(self.symbol, self.envPeriod, None)
        self.registerOnBar(self.symbol, self.signalPeriod, None)

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
        self.lastOrderDict = {'nextExecuteTime': datetime(2000, 1, 1)}
        self.stopLossPct = self.paraDict["stopLossPct"]
        self.stoplossPeriod = self.paraDict["stoplossPeriod"]
        self.addPct = self.paraDict["addPct"]
        self.posTime = self.paraDict["posTime"]
        self.expectReturn = self.paraDict["expectReturn"]
        self.takeProfitLot = max(int(self.paraDict["takeProfitLotRatio"]*self.lot), 1)
        self.orderTime = self.paraDict["orderTime"]
        # self.lot = self.paraDict['lot']
        # 由于vnpy无法有效得到60Mk线，通过获得两次30Mink线变化一次来得到60MinK线
        self.Min60Signal = True 
        self.close_signal = None

    ####################################### ↓↓↓↓无需修改区↓↓↓↓ #######################################↓
    def onStart(self):
        self.putEvent()

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
                # 平仓后1小时内不开仓
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

    def tradeTime(self, bar):
        if self.symbol[:2] == 'IF':
            if time(9,30) <= bar.datetime.time() < time(15,0): # IF 使用
                return True
            else:
                return False
        else:
            if time(9,0) <= bar.datetime.time() < time(14,55): # 商品期货使用
                return True
            else:
                return False

    
    def isStopControled(self):
        return self.currentTime < self.lastOrderDict['nextExecuteTime']
    
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
            # 回测时的下单手数按此方法调整
            # self.lot = int(200000 / bar.close)
            
            # 定时清除已出场的单
            self.checkOnPeriodEnd(bar)
            for idSet in self.orderDict.values():
                self.delOrderID(idSet)
            # 执行策略逻辑
            self.lot = self.lotDecide(bar, allCapital=10000000) # 通过API获取总资金量代替
            self.takeProfitLot = max(int(self.paraDict["takeProfitLotRatio"]*self.lot), 1) # 止盈单下单量
            self.strategy(bar)

    def strategy(self, bar):
        signalPeriod = self.signalPeriod
        envPeriod = self.envPeriod
        # 止损
        self.trailstoploss(bar, signalPeriod)
        # 止盈
        self.takeProfit(bar, signalPeriod)
        # 出场
        # exitSig = self.exitSignal(bar, signalPeriod)
        # self.exitOrder(bar, exitSig)
        # 进场
        entrySig = self.entrySignal(bar, envPeriod, signalPeriod)
        self.entryOrder(bar, entrySig)
        # 加仓
        # self.addPosOrder(bar)

    # def exitSignal(self, bar, signalPeriod):
    #     arrayPrepared1, amSignal = self.arrayPrepared(signalPeriod)
    #     maCrossSignal = 0
    #     if arrayPrepared1:
    #         maCrossSignal, _, _ = self.algorithm.emaCross(bar, amSignal, self.paraDict, ExitSignal=True)
    #     return maCrossSignal
    
    def exitOrder(self, bar, exitSig):
        if exitSig==-1:
            for orderID in (self.orderDict['orderLongSet']|self.orderDict['order2LongSet']|self.orderDict['addLongSet']):
                op = self._orderPacks[orderID]
                self.composoryClose(op)
        elif exitSig==1:
            for orderID in (self.orderDict['orderShortSet']|self.orderDict['order2ShortSet']|self.orderDict['addShortSet']):
                op = self._orderPacks[orderID]
                self.composoryClose(op)

    def entrySignal(self, bar, envPeriod, signalPeriod):
        entrySignal = 0
        arrayPrepared1, amSignal = self.arrayPrepared(signalPeriod)
        arrayPrepared2, amEnv = self.arrayPrepared(envPeriod)
        if arrayPrepared1 and arrayPrepared2:
            # 修改成60Min数据
            if amEnv.close[-1] != self.close_signal: 
                self.Min60Signal = not self.Min60Signal
                self.close_signal = amEnv.close[-1]
            # envDirection, envMa = self.algorithm.macdEnvironment(amEnv, self.paraDict, signalControl=True, Min60Signal=self.Min60Signal)
            # volumeSpike, volumeUpper = self.algorithm.volumeSignal(amSignal, self.paraDict)
            volumeSpike, volumeUpper, maVol = self.algorithm.volumeSignal(amEnv, self.paraDict)
            skewShortSignal, skew = self.algorithm.skewShortCal(amSignal, self.paraDict)
            skewLongSignal, skewLong = self.algorithm.skewLongCal(amEnv, self.paraDict)
            # if not self.isStopControled():
            if True:
                # 长期处于下跌趋势，成交量放大（投资者意见分歧），短期收益率分布从左偏转为右偏（短期开始出现上涨趋势），做多
                # if envDirection==-1 and skewLongSignal==-1 and volumeSpike==1 and skewShortSignal==1: 
                if skewLongSignal==-1 and volumeSpike==1 and skewShortSignal==1: 
                    entrySignal = 1
                # 长期处于上涨趋势，成交量放大（投资者意见分歧），短期收益率分布从右偏转为左偏（短期开始出现下跌趋势），做空
                # elif envDirection==1 and skewLongSignal==1 and volumeSpike==1 and skewShortSignal==-1:
                elif skewLongSignal==1 and volumeSpike==1 and skewShortSignal==-1: # 做空
                    entrySignal = -1
            # 记录画图数据
            self.chartLog['datetime'].append(datetime.strptime(amSignal.datetime[-1], "%Y%m%d %H:%M:%S"))
            # self.chartLog['envMa'].append(envMa)
            self.chartLog['volumeUpper'].append(volumeUpper[-1])
            self.chartLog['maVolume'].append(maVol[-1])
            self.chartLog['shortSkew'].append(skew[-1])
            self.chartLog['longSkew'].append(skewLong[-1])
            self.chartLog['close'].append(bar.close)
            # self.chartLog['skewThreshold_left'].append(None)
            # self.chartLog['skewThreshold_right'].append(None)
        return entrySignal

    def entryOrder(self, bar, entrySignal):
        # 是否考虑平仓后进行反向开仓？
        buyExecute, shortExecute = self.priceExecute(bar)
        orderPos = self.lot//self.orderTime
        if not any(self.orderDict.values()): # 多空头均无持仓
            self.orderAllList = [] # 清空orderAllList列表
        else:
            # 出现反向信号则平仓
            self.exitOrder(bar, entrySignal)   
        # 根据信号交易
        if entrySignal == 1:
            if not any([self.orderDict['orderLongSet'], self.orderDict['order2LongSet'], self.orderDict['addLongSet']]):
                # 分批下单
                stepOrder1 = self.makeStepOrder(ctaBase.CTAORDER_BUY, bar.vtSymbol, buyExecute, max(self.lot, 1), max(orderPos,1), self.totalSecond, self.stepSecond)                 
                orderID1 = stepOrder1.parentID
                self.orderDict['orderLongSet'].add(orderID1)
                self.orderAllList.append(orderID1)
                # 止盈单与普通单的下单手数不一样
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
                stepOrder2 = self.makeStepOrder(ctaBase.CTAORDER_SHORT, bar.vtSymbol, shortExecute, max(self.takeProfitLot, 1), max(orderPos,1), self.totalSecond, self.stepSecond)
                orderID2 = stepOrder2.parentID                
                self.orderDict['order2ShortSet'].add(orderID2)
                # self.orderAllList.append(orderID2)

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
    
    #---------------------------------------加仓模块---------------------------------------
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
                    addLotTime = [0.5, 0.8, 0.5]
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