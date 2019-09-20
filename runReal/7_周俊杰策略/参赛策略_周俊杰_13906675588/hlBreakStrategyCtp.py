from vnpy.trader.vtConstant import *
import numpy as np
import talib as ta
import pandas as pd
from datetime import timedelta, datetime
from vnpy.trader.utils.templates.orderTemplate import * 
from vnpy.trader.app.ctaStrategy import ctaBase
from hlBreakSignalClass import hlBreakSignal

########################################################################
class hlBreakStrategy(OrderTemplate):
    className = 'hlBreak'
    author = 'abc'

    # 参数列表，保存了参数的名称
    paramList = [
                # 品种列表
                 'symbolList', 
                 # 时间周期
                 'timeframeMap',
                 #  总秒，间隔，下单次数
                 'totalSecond', 'stepSecond', 'orderTime',
                 #补充唐奇安通道参数,rsi,soup
                 'hlEntryPeriod','hlExitPeriod','rsiPeriod','hlPeriod','delayPeriod','trendPeriod'
                 # signalParameter 计算信号的参数
                 'keltnerentrywindow','keltnerentrydev','keltnerexitwindow','keltnerexitdev'
                 # Density 密度指标参数
                 'dsPeriod', 'dsThreshold', 'bandTime',
                 # cmi 指标参数
                 'cmiPeriod', 'cmiMaPeriod', 'cmiThreshold','AtrPeriod',
                 # 止损止盈
                 'holdDay', 'expectReturn',
                 # 加仓
                 'addPct', 'addLotTime', 'posTime',
                 #复刻冠军参数
                 'csdev1','csdev2','bandAtr','fastPeriod','slowPeriod','largePeriod'
                 ]

    # 变量列表，保存了变量的名称
    varList = ['lot']
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['posDict', 'eveningDict']

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        super().__init__(ctaEngine, setting)
        self.paraDict = setting
        self.barPeriod = 900
        self.nPos = 0
        self.lot = 0
        self.symbol = self.symbolList[0]
        self.orderAllList = []
        # 实例化信号
        self.algorithm = hlBreakSignal()

        # 订单的集合
        self.orderDict = {
                            'orderLongSet':set(), 'orderShortSet':set(),
                            'order2LongSet':set(), 'order2ShortSet':set(),
                            'addLongSet':set(), 'addShortSet':set(),

                         }
       
        # 画图数据的字典
        self.chartLog = {
                            'datetime':[],
                            'highEntryBand':[],
                            'lowEntryBand':[],
                            # 'density': [],
                            'dsSma': [],
                            'dsLma': [],
                            'cmiMa':[],
                            'atr':[],
                            'rsi':[],
                            'sma':[],
                            'lma':[],
                            'ema':[]
                            # 'delayHigh':[],
                            # 'delayLow':[],
                            # 'newHigh':[],
                            # 'newLow':[],
                        }
        
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

    def moveStopLoss(self, bar, orderSet):
        if len(self.orderAllList)>0:
            lastOrderId = self.orderAllList[-1]
            opLast = self._orderPacks[lastOrderId]
            entryCost =  opLast.order.price_avg
            slGap = entryCost*self.protectPct
            for orderId in list(orderSet):
                op = self._orderPacks[orderId]
                # 通过改一张单绑定的AutoExitInfo属性修改止损止盈
                if self.isAutoExit(op):
                    # print('ready2MoveSl')
                    if op.order.direction == constant.DIRECTION_LONG:
                        if (bar.high - entryCost) >= slGap:
                            # print('moveLongSl')
                            self.setAutoExit(op, entryCost)
                            self.globalStatus['longTrailingStopLoss'] = entryCost
                    elif op.order.direction == constant.DIRECTION_SHORT:
                        if (entryCost - bar.low) >= slGap:
                            # print('moveShortSl')
                            self.setAutoExit(op, entryCost)
                            self.globalStatus['shortTrailingStopLoss'] = entryCost

    def on5MinBar(self, bar):
        # 必须继承父类方法
        super().onBar(bar)
        self.lot = int(10000000/(bar.close*30)*0.7)
        # on bar下触发回测洗价逻辑
        # 定时控制，开始
        self.checkOnPeriodStart(bar)
        # 定时清除已出场的单
        self.checkOnPeriodEnd(bar)
        for idSet in self.orderDict.values():
            self.delOrderID(idSet)
            # self.moveStopLoss(bar, idSet)
        # 执行策略逻辑
        self.strategy(bar)

    def strategy(self, bar):
        signalPeriod= self.timeframeMap["signalPeriod"]
        # 根据出场信号出场
        highExitBand, lowExitBand,sma,lma,maCrossSignal,ema = self.exitSignal(signalPeriod)
        self.exitOrder(bar, highExitBand, lowExitBand,sma,lma,maCrossSignal,ema)
        
        # 根据进场信号进场
        entrySig = self.entrySignal(signalPeriod)
        self.entryOrder(bar, entrySig)

        self.addPosOrder(bar)

    def exitSignal(self,signalPeriod):
        highExitBand, lowExitBand = np.array([]) , np.array([])
        
        arrayPrepared, amSignal = self.arrayPrepared(signalPeriod)

        if arrayPrepared:
            highExitBand, lowExitBand = self.algorithm.keltnerexitBand(amSignal, self.paraDict)
            maCrossSignal, sma, lma, ema = self.algorithm.maCross(amSignal,self.paraDict)
        return highExitBand, lowExitBand,sma,lma,maCrossSignal,ema
    
    def exitOrder(self, bar, highExitBand, lowExitBand,sma,lma,maCrossSignal,ema):
        exitTouchLowest = (bar.low<lowExitBand[-2]) and sma[-1]<lma[-1]
        exitTouchHighest = (bar.high>highExitBand[-2]) #and sma[-1]>lma[-1]

        if exitTouchLowest:
            for orderID in (self.orderDict['orderLongSet']|self.orderDict['order2LongSet']|self.orderDict['addLongSet']):
                op = self._orderPacks[orderID]
                self.composoryClose(op)
        elif exitTouchHighest:
            for orderID in (self.orderDict['orderShortSet']|self.orderDict['order2ShortSet']|self.orderDict['addShortSet']):
                op = self._orderPacks[orderID]
                self.composoryClose(op)

    def entrySignal(self, signalPeriod):
        entrySignal = 0
        arrayPrepared, amSignal = self.arrayPrepared(signalPeriod)

        if arrayPrepared:
            dsEnvStatus, dsSma, dsLma = self.algorithm.dsEnvUp(amSignal, self.paraDict)
            cmiEnvStatus, cmiMa = self.algorithm.cmiEnv(amSignal, self.paraDict)
            atr,atrGreat = self.algorithm.atr(amSignal,self.paraDict)
            maCrossSignal, sma, lma, ema = self.algorithm.maCross(amSignal,self.paraDict)
            # up,down = self.algorithm.consolidation(amSignal)
            rsiDirection, rsi = self.algorithm.rsiSignal(amSignal, self.paraDict)
            #delayHigh, delayLow, newHigh, newLow = self.algorithm.soupSignal(amSignal, self.paraDict)
            
            if  cmiEnvStatus and atrGreat : #and dsEnvStatus:
                # highEntryBand, lowEntryBand = self.algorithm.keltnerentryBand(amSignal, self.paraDict)
                highEntryBand, lowEntryBand = self.algorithm.hlEntryBand(amSignal,self.paraDict)
            else:
                # delayHigh, delayLow, newHigh, newLow = self.algorithm.soupSignal(amSignal, self.paraDict)               
                highEntryBand, lowEntryBand = self.algorithm.keltnerentryBand(amSignal, self.paraDict)
                # if up:
                #     highEntryBand, lowEntryBand = self.algorithm.csBandUp(amSignal, self.paraDict)
                # elif down:
                #     highEntryBand, lowEntryBand = self.algorithm.csBandDown(amSignal, self.paraDict)
                
            breakHighest = (amSignal.close[-1]>highEntryBand[-2]) and (amSignal.close[-2]<=highEntryBand[-2]) #and (rsiDirection > 0)
            breakLowest = (amSignal.close[-1]<lowEntryBand[-2]) and (amSignal.close[-2]>=lowEntryBand[-2]) #and (rsiDirection < 0)
            
            backHighest = (amSignal.close[-1]<highEntryBand[-2]) and (amSignal.close[-2]>=highEntryBand[-2])
            backLowest = (amSignal.close[-1]>lowEntryBand[-2]) and (amSignal.close[-2]<=lowEntryBand[-2])

            # creatHigh = newHigh[-1]>delayHigh
            # creatLow = newLow[-1]<delayLow
            # revertDn = (amSignal.close[-1]<delayHigh) and (amSignal.close[-2]>=delayHigh)
            # revertUp = (amSignal.close[-1]>delayLow) and (amSignal.close[-2]<=delayLow)
            # turpleSoup = 0


            # if creatLow and revertUp: #and (rsiDirection == 1):
            #     turpleSoup = 1
            #     #entrySignal = 1
            # elif creatHigh and revertDn :#and (rsiDirection == -1):
            #     turpleSoup = -1
            #     #entrySignal = -1

            self.globalStatus['breakHighest'] = breakHighest
            self.globalStatus['breakLowest'] = breakLowest
            self.globalStatus['bakcLowest'] = backLowest
            self.globalStatus['backHighest'] = backHighest
            self.globalStatus['highEntryBand'] = highEntryBand[-1]
            self.globalStatus['lowEntryBand'] = lowEntryBand[-1]
            self.globalStatus['cmiMa'] = cmiMa[-1]
            self.globalStatus['dsSma'] = dsSma[-1]
            self.globalStatus['dsLma'] = dsLma[-1]
            self.globalStatus['atr'] = atr[-1]
            self.globalStatus['lma'] = lma[-1]
            self.globalStatus['sma'] = sma[-1]
            self.globalStatus['ema'] = ema[-1]
            self.globalStatus['maCrossSignal'] = maCrossSignal
            # self.globalStatus['up'] = up
            # self.globalStatus['down'] = down
            # self.globalStatus['turpleSoup'] = turpleSoup
            self.globalStatus['rsiDirection'] = rsiDirection
            self.globalStatus['rsi'] = rsi[-1]
            # self.chartLog['delayHigh'].append(delayHigh)
            # self.chartLog['delayLow'].append(delayLow)
            # self.chartLog['newHigh'].append(newHigh[-1])
            # self.chartLog['newLow'].append(newLow[-1])
            
            
            self.chartLog['datetime'].append(datetime.strptime(amSignal.datetime[-1], "%Y%m%d %H:%M:%S"))
            self.chartLog['highEntryBand'].append(highEntryBand[-1])
            self.chartLog['lowEntryBand'].append(lowEntryBand[-1])
            self.chartLog['cmiMa'].append(cmiMa[-1])
            self.chartLog['dsSma'].append(dsSma[-1])
            self.chartLog['dsLma'].append(dsLma[-1]) 
            self.chartLog['atr'].append(atr[-1])
            self.chartLog['rsi'].append(rsi[-1]) 
            self.chartLog['lma'].append(lma[-1])
            self.chartLog['sma'].append(sma[-1])  
            self.chartLog['ema'].append(ema[-1])        
            
            
            if  atrGreat and cmiEnvStatus:
                if breakHighest and sma[-1]<=lma[-1]  : #and (rsiDirection == 1):
                    entrySignal = 1
                elif breakLowest and sma[-1]<=lma[-1] : #and (rsiDirection == -1):           
                    entrySignal = -1
            else:
                if breakHighest and sma[-1]>=lma[-1] : #and (rsiDirection == 1):
                    entrySignal = 1
                elif breakLowest and sma[-1]>=lma[-1] : #and (rsiDirection == -1):           
                    entrySignal = 1  
                                                         
        return entrySignal

    def entryOrder(self, bar, entrySignal):
        buyExecute, shortExecute = self.priceExecute(bar)
        orderPos = self.lot//self.orderTime
        if not (self.orderDict['orderLongSet'] or self.orderDict['orderShortSet']):
            self.orderAllList = []
        if entrySignal ==1:
            if not (self.orderDict['orderLongSet'] or self.orderDict['order2LongSet']):
                # 分批下单
                stepOrder1 = self.makeStepOrder(ctaBase.CTAORDER_BUY, bar.vtSymbol, buyExecute, max(self.lot, 1), max(orderPos,1), self.totalSecond, self.stepSecond)                 
                orderID1 = stepOrder1.parentID
                self.orderDict['orderLongSet'].add(orderID1)
                self.orderAllList.append(orderID1)
    
                stepOrder2 = self.makeStepOrder(ctaBase.CTAORDER_BUY, bar.vtSymbol, buyExecute, max(self.lot, 1), max(orderPos,1), self.totalSecond, self.stepSecond)                 
                orderID2 = stepOrder2.parentID
                self.orderDict['order2LongSet'].add(orderID2)
                op = self._orderPacks[orderID2]
                self.setConditionalClose(op, int(timedelta(days=self.holdDay).total_seconds()), self.expectReturn)

        elif entrySignal ==-1:
            if not (self.orderDict['orderShortSet'] or self.orderDict['order2ShortSet']):
                stepOrder1 = self.makeStepOrder(ctaBase.CTAORDER_SHORT, bar.vtSymbol, shortExecute, max(self.lot, 1), max(orderPos,1), self.totalSecond, self.stepSecond)
                orderID1 = stepOrder1.parentID                
                self.orderDict['orderShortSet'].add(orderID1)
                self.orderAllList.append(orderID1)

                stepOrder2 = self.makeStepOrder(ctaBase.CTAORDER_SHORT, bar.vtSymbol, shortExecute, max(self.lot, 1), max(orderPos,1), self.totalSecond, self.stepSecond)
                orderID2 = stepOrder2.parentID                
                self.orderDict['order2ShortSet'].add(orderID2)
                op = self._orderPacks[orderID2]
                self.setConditionalClose(op, int(timedelta(days=self.holdDay).total_seconds()), self.expectReturn)

     # 通过上一张单来获取成交价
    def addPosOrder(self, bar):
        buyExecute, shortExecute = self.priceExecute(bar)
        holdLong = len(self.orderDict['orderLongSet']|self.orderDict['order2LongSet'])>0
        holdShort = len(self.orderDict['orderShortSet']|self.orderDict['order2ShortSet'])>0
        
        if not (holdLong or holdShort):
            self.nPos = 0
            self.orderAllList = []
        elif self.orderAllList:
            lastOrderID = self.orderAllList[-1]
            op = self._orderPacks[lastOrderID]
            entryCost = op.order.price_avg
            if entryCost!=0:
                if op.order.direction == constant.DIRECTION_LONG and (self.nPos < self.posTime):
                    if ((bar.close/entryCost - 1) >= self.addPct) and ((bar.close/entryCost - 1)<=2*self.addPct):
                        self.nPos += 1
                        addPosLot = self.lot*(2**self.nPos)#self.addLotTime
                        for orderID in self.timeLimitOrder(ctaBase.CTAORDER_BUY, bar.vtSymbol, buyExecute, max(addPosLot,1), 60).vtOrderIDs:
                            self.globalStatus['addPos'] = (self.nPos, addPosLot)
                            self.orderAllList.append(orderID)
                            self.orderDict['addLongSet'].add(orderID)
                elif op.order.direction == constant.DIRECTION_SHORT and (self.nPos < self.posTime):
                    if ((entryCost/bar.close - 1) >= self.addPct) and ((entryCost/bar.close - 1) <= 2*self.addPct):
                        self.nPos += 1
                        addPosLot = self.lot*(2**self.nPos)#self.addLotTime
                        for orderID in self.timeLimitOrder(ctaBase.CTAORDER_SHORT, bar.vtSymbol, shortExecute, max(addPosLot,1), 60).vtOrderIDs:
                            self.globalStatus['addPos'] = (self.nPos, addPosLot)
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