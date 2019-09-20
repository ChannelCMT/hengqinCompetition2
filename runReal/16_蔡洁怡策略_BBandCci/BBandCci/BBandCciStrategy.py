from vnpy.trader.vtConstant import *
import numpy as np
import talib as ta
from datetime import timedelta, datetime
from vnpy.trader.utils.templates.orderTemplate import * 
from vnpy.trader.app.ctaStrategy import ctaBase
from BBandSignalClass import BBandSignal
########################################################################
class BBandCciStrategy(OrderTemplate):
    className = 'BBandCci'

    # 参数列表，保存了参数的名称
    paramList = [
                 'author',
                 # 时间周期
                 'timeframeMap',
                 #  总秒，间隔，下单次数
                 'totalSecond', 'stepSecond','orderTime',
                 # 品种列表
                 'symbolList',
                 # signalParameter 计算信号的参数
                 'bandPeriod','bBandEntry','limitPeriod','atrTime',
                 'bandWidthThreshold', 'bPctThreshold', 'bandFilterThreshold',
                 "cciThreshold"
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
        self.lot = 0
        self.algorithm = BBandSignal()
        self.entrySig = 0
        self.symbol = self.symbolList[0]

        self.lowestPrice = 999999
        self.shortStop = 999999
        self.highestPrice = 0
        self.longStop = 0


        # varialbes
        self.orderDict = {'orderLongSet':set(), 'orderShortSet':set()}
        self.orderLastList = []

        # 打印全局信号的字典
        self.globalStatus = {}
        self.chartLog = {
                'datetime':[],
                'bandWidthValue':[],
                'bandWidthMax':[],
                'bPctValue':[],
                'cciSignal': []
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
    
    # 获得执行价格
    def priceExecute(self, bar):
        if bar.vtSymbol in self._tickInstance:
            tick = self._tickInstance[bar.vtSymbol]
            if tick.datetime >= bar.datetime:
                return tick.upperLimit * 0.99, tick.lowerLimit*1.01
        return bar.close*1.02, bar.close*0.98

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
        # start = datetime.now()
        engineType = self.getEngineType()  # 判断engine模式
        if engineType == 'backtesting': # 回测时下单手数设置的是一次下多少个币，实盘需要根据情况转化为合约张数
            # 定时控制，开始
            self.checkOnPeriodStart(bar)
            # 实盘下单手数按此方法调整
            self.checkOnPeriodEnd(bar)
            # 定时清除已出场的单
            for idSet in self.orderDict.values():
                self.delOrderID(idSet)
            # 执行策略逻辑
            self.strategy(bar)
            # print('debug',(datetime.now()-start).total_seconds())

    def on15MinBar(self, bar):
        self.writeCtaLog('globalStatus%s'%(self.globalStatus))
        self.writeCtaLog('longVolume:%s, shortVolume:%s'%(self.getHoldVolume(self.orderDict['orderLongSet']), self.getHoldVolume(self.orderDict['orderShortSet'])))
        self.notifyPosition('longVolume', self.getHoldVolume(self.orderDict['orderLongSet']), self.author)
        self.notifyPosition('shortVolume', self.getHoldVolume(self.orderDict['orderShortSet']), self.author)

    def strategy(self, bar):
        signalPeriod= self.timeframeMap["signalPeriod"]
        
        # 根据出场信号出场
        exitSig = self.exitSignal(bar, signalPeriod)
        self.exitOrder(exitSig)

        # 根据进场信号进场
        self.entrySignal(signalPeriod)
        self.entryOrder(bar)

    def exitSignal(self, bar, signalPeriod):
        arrayPrepared1, amSignal = self.arrayPrepared(signalPeriod)
        exitSignal = 0
        if arrayPrepared1:
            stopLossAtr = self.algorithm.atrStopLoss(amSignal, self.paraDict)
            if not self.orderDict['orderLongSet']:
                self.highestPrice = 0
                self.longStop = 0
            else:
                self.highestPrice = max(bar.high,self.highestPrice)
                self.longStop = max(self.highestPrice-stopLossAtr[-1], self.longStop)
                if bar.low<=self.longStop:
                    exitSignal = 'exitLong'
            if not self.orderDict['orderShortSet']:
                self.lowestPrice = 999999
                self.shortStop = 999999
            else:
                self.lowestPrice = min(bar.low,self.shortStop)
                self.shortStop = min(self.lowestPrice+stopLossAtr[-1], self.shortStop)
                if bar.high>=self.shortStop:
                    exitSignal = 'exitShort'
        return exitSignal
    
    def exitOrder(self, exitSignal):
        if (exitSignal=='exitLong') or (self.entrySig==-1):
            for orderID in (self.orderDict['orderLongSet']):
                op = self._orderPacks[orderID]
                self.composoryClose(op)
        elif (exitSignal=='exitShort') or (self.entrySig==1):
            for orderID in (self.orderDict['orderShortSet']):
                op = self._orderPacks[orderID]
                self.composoryClose(op)

    def entrySignal(self, signalPeriod):
        self.entrySig = 0
        arrayPrepared, amSignal = self.arrayPrepared(signalPeriod)
        if arrayPrepared:
            stdStatus, bandWidthValue, bandWidthMax = self.algorithm.bandWidth(amSignal, self.paraDict)
            bDirection, bPctValue = self.algorithm.bPct(amSignal, self.paraDict)
            cciStatus, cciSignal = self.algorithm.cciIndicator(amSignal, self.paraDict)

            self.globalStatus['stdStatus'] = [stdStatus, bandWidthValue[-3:], bandWidthMax[-3:]]
            self.globalStatus['bDirection'] = [bDirection, bPctValue[-3:]]
            self.globalStatus['cciStatus'] = [cciStatus, cciSignal[-3:]]

            self.chartLog['datetime'].append(datetime.strptime(amSignal.datetime[-1], "%Y%m%d %H:%M:%S"))
            self.chartLog['bandWidthValue'].append(bandWidthValue[-1])
            self.chartLog['bandWidthMax'].append(bandWidthMax[-1])
            self.chartLog['bPctValue'].append(bPctValue[-1])
            self.chartLog['cciSignal'].append(cciSignal[-1])

            if (stdStatus == 1) :
                if (bDirection==1) and (cciStatus==1):
                    self.entrySig = 1
                if (bDirection==-1) and (cciStatus==-1):
                    self.entrySig = -1

    def entryOrder(self, bar):
        buyExecute, shortExecute = self.priceExecute(bar)
        if self.entrySig ==1:
            if not self.orderDict['orderLongSet']:
                # 如果回测直接下单，如果实盘就分批下单
                longPos = self.lot//self.orderTime
                stepOrder = self.makeStepOrder(ctaBase.CTAORDER_BUY, bar.vtSymbol, buyExecute, max(self.lot, 1), max(longPos, 1), self.totalSecond, self.stepSecond)                 
                orderID = stepOrder.parentID
                self.orderDict['orderLongSet'].add(orderID)
                self.orderLastList.append(orderID)

        elif self.entrySig ==-1:
            if not self.orderDict['orderShortSet']:
                shortPos = self.lot//self.orderTime
                stepOrder = self.makeStepOrder(ctaBase.CTAORDER_SHORT, bar.vtSymbol, shortExecute, max(self.lot, 1), max(shortPos, 1), self.totalSecond, self.stepSecond)
                orderID = stepOrder.parentID                
                self.orderDict['orderShortSet'].add(orderID)
                self.orderLastList.append(orderID)

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