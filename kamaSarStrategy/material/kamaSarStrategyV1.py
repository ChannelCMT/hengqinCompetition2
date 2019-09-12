from vnpy.trader.vtConstant import *
import numpy as np
import talib as ta
from datetime import timedelta, datetime
from vnpy.trader.utils.templates.orderTemplate import * 
from vnpy.trader.app.ctaStrategy import ctaBase
from adxSarClass import adxSarSignal


########################################################################
class adxSarStrategy(OrderTemplate):
    className = 'adxSarStrategy'
    author = 'ChannelCMT'

    # 参数列表，保存了参数的名称
    paramList = [
                 # 分批进场手数
                 'lot',
                 # 品种列表
                 'symbolList',
                 # envParameter 计算ADX环境的参数
                 'adxPeriod', 'adxMaPeriod', 'adxMaType', 'adxThreshold',
                 # signalParameter 计算信号的参数
                 'sarAcceleration','maPeriod', 'maType',
                 # 止损止盈参数
                 "takeProfitPct", "stopLossPct",
                 # 时间周期
                 'timeframeMap',
                 #  总秒，间隔，下单次数
                 'totalSecond', 'stepSecond','orderTime'
                 ]

    # 变量列表，保存了变量的名称
    varList = [
               'nPos'
               ]

    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['posDict', 'eveningDict']

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        super().__init__(ctaEngine, setting)

        self.paraDict = setting
        self.barPeriod = 600
        engineType = self.getEngineType()  # 判断engine模式
        self.symbol = self.symbolList[0]

        # varialbes
        self.orderDict = {'orderLongSet':set(), 'orderShortSet': set()}
        # 打印全局信号的字典
        self.globalStatus = {}
        self.chartLog = {
                        'datetime':[],
                        'sar': [],
                        'trendMa': [],
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


    # 获取当前的持有仓位
    def getHoldVolume(self, orderSet):
        pos = 0
        for orderID in orderSet:
            op = self._orderPacks[orderID]
            holdVolume = op.order.tradedVolume
            closedVolume = self.orderClosedVolume(op)
            pos+= (holdVolume-closedVolume)
        return pos
    
    # 实盘在5sBar中洗价
    def on5sBar(self, bar):
        self.checkOnPeriodStart(bar)
        self.checkOnPeriodEnd(bar)
        for idSet in self.orderDict.values():
            self.delOrderID(idSet)

    def onBar(self, bar):
        # 必须继承父类方法
        super().onBar(bar)
        # on bar下触发回测洗价逻辑
        engineType = self.getEngineType()  # 判断engine模式
        if engineType == 'backtesting':
            # 定时控制，开始
            self.checkOnPeriodStart(bar)
            # 回测时的下单手数按此方法调整
            self.lot = int(200000 / bar.close)
        # 定时清除已出场的单
            self.checkOnPeriodStart(bar)
            self.checkOnPeriodEnd(bar)

            for idSet in self.orderDict.values():
                self.delOrderID(idSet)

        # 执行策略逻辑
        self.strategy(bar)

    def on5MinBar(self, bar):
        engineType = self.getEngineType()  # 判断engine模式
        if engineType != 'backtesting':
            self.writeCtaLog('globalStatus%s'%(self.globalStatus))
            self.writeCtaLog('firstVolume:%s, secondVolume:%s'%(self.getHoldVolume(self.orderDict['orderLongSet']), self.getHoldVolume(self.orderDict['orderShortSet'])))
        else:
            pass

    def strategy(self, bar):
        trendPeriod= self.timeframeMap["trendPeriod"]
        signalPeriod= self.timeframeMap["signalPeriod"]

        # 根据出场信号出场
        exitSig = self.exitSignal(trendPeriod, signalPeriod)
        self.exitOrder(exitSig)

        # 根据进场信号进场
        entrySig = self.entrySignal(trendPeriod, signalPeriod)
        self.entryOrder(bar, entrySig)

    def isStopControled(self):
        return self.currentTime < self.lastOrderDict['nextExecuteTime']

    def exitSignal(self, trendPeriod, signalPeriod):
        exitSignal = 0
        arrayPrepared1, amTrend = self.arrayPrepared(trendPeriod)
        arrayPrepared2, amSignal = self.arrayPrepared(signalPeriod)

        algorithm = adxSarSignal()
        # if arrayPrepared1:
        #     trendDirection, trendMa = algorithm.maSignal(amTrend, self.paraDict)
        #     signalDirection, sar = algorithm.sarSignal(amSignal, self.paraDict)

        #     if trendDirection==-1 or signalDirection==-1:
        #         exitSignal = 1
        #     elif trendDirection==1 or signalDirection==1:
        #         exitSignal = -1
        #     else:
        #         exitSignal = 0
        return exitSignal
    
    def exitOrder(self, exitSignal):
        if exitSignal == 1:
            for orderID in (self.orderDict['orderLongSet']):
                op = self._orderPacks[orderID]
                self.composoryClose(op)
        elif exitSignal==-1:
            for orderID in (self.orderDict['orderShortSet']):
                op = self._orderPacks[orderID]
                self.composoryClose(op)

    def entrySignal(self, trendPeriod, signalPeriod):
        entrySignal = 0
        arrayPrepared1, amTrend = self.arrayPrepared(trendPeriod)
        arrayPrepared2, amSignal = self.arrayPrepared(signalPeriod)
        arrayPrepared = arrayPrepared1 and arrayPrepared2
        algorithm = adxSarSignal()        
        if arrayPrepared:
            trendDirection, trendMa = algorithm.maSignal(amTrend, self.paraDict)            
            signalDirection, sar = algorithm.sarSignal(amSignal, self.paraDict)

            self.globalStatus['trendDirection'] = trendDirection
            self.globalStatus['signalDirection'] = signalDirection
            self.globalStatus['trendMa'] = trendMa[-1]
            self.globalStatus['sar'] = sar[-1]

            self.chartLog['datetime'].append(datetime.strptime(amSignal.datetime[-1], "%Y%m%d %H:%M:%S"))
            self.chartLog['sar'].append(sar[-1])
            self.chartLog['trendMa'].append(trendMa[-1])

            if (signalDirection==1) and (trendDirection==1):
                entrySignal = 1
            elif (signalDirection==-1) and (trendDirection==-1):
                entrySignal = -1
        return entrySignal

    def entryOrder(self, bar, entrySignal):
        buyExecute, shortExecute = self.priceExecute(bar)
        if entrySignal ==1:
            if self.orderDict['orderShortSet']:
                for orderID in (self.orderDict['orderShortSet']):
                    op = self._orderPacks[orderID]
                    self.composoryClose(op)
            if not self.orderDict['orderLongSet']:
                # 如果回测直接下单，如果实盘就分批下单
                longPos = self.lot//self.orderTime
                    # for orderID in self.timeLimitOrder(ctaBase.CTAORDER_BUY, self.symbol, buyExecute, self.lot, 120).vtOrderIDs:
                stepOrder = self.makeStepOrder(ctaBase.CTAORDER_BUY, bar.vtSymbol, buyExecute, self.lot, longPos, self.totalSecond, self.stepSecond)
                orderID = stepOrder.parentID
                self.orderDict['orderLongSet'].add(orderID)

        elif entrySignal ==-1:
            if self.orderDict['orderLongSet']:
                for orderID in (self.orderDict['orderLongSet']):
                    op = self._orderPacks[orderID]
                    self.composoryClose(op)
            if not self.orderDict['orderShortSet']:
                shortPos = self.lot//self.orderTime
                stepOrder = self.makeStepOrder(ctaBase.CTAORDER_SHORT, bar.vtSymbol, shortExecute, self.lot, shortPos, self.totalSecond, self.stepSecond)
                orderID = stepOrder.parentID                
                self.orderDict['orderShortSet'].add(orderID)

    # ----------------------------------------------------------------------
    def onOrder(self, order):
        super().onOrder(order)
        if order.status == STATUS_UNKNOWN:
            self.mail(u'出现未知订单，需要策略师外部干预,ID:%s, symbol:%s,direction:%s,offset:%s'
                      % (order.vtOrderID, order.vtSymbol, order.direction, order.offset))
        if order.status == STATUS_REJECTED:
            self.mail(u'Rejected,ID:%s, symbol:%s,direction:%s,offset:%s,拒单信息:%s'
                      % (order.vtOrderID, order.vtSymbol, order.direction, order.offset,order.rejectedInfo))
        if order.thisTradedVolume != 0:
            content = u'成交信息播报,ID:%s, symbol:%s, directionL%s, offset:%s, price:%s'%\
                      (order.vtOrderID, order.vtSymbol, order.direction, order.offset, order.price_avg)
            self.mail(content)
        self.setStop(order)

    def setStop(self, order):
        op = self._orderPacks.get(order.vtOrderID, None)
        # 判断是否该策略下的开仓
        if op:
            # 如果没有加过仓就设置初始的止损止盈
            if order.offset == constant.OFFSET_OPEN:
                if order.price_avg!=0:
                    slGap = order.price_avg*self.stopLossPct
                    tpGap = order.price_avg*self.takeProfitPct
                    if order.direction == constant.DIRECTION_LONG:
                        if op.vtOrderID in self.orderDict['orderLongSet']:
                            self.setAutoExit(op, (order.price_avg-slGap), order.price_avg+tpGap)
                            op.info['slGap'] = slGap
                            self.globalStatus['orderLongGap'] = {'SL': order.price_avg-slGap, 'TP': order.price_avg+tpGap}
                    elif order.direction == constant.DIRECTION_SHORT:
                        if op.vtOrderID in self.orderDict['orderShortSet']:
                            self.setAutoExit(op, (order.price_avg+slGap), order.price_avg-tpGap)
                            op.info['slGap'] = slGap                            
                            self.globalStatus['orderFirstShort'] = {'SL': order.price_avg+slGap, 'TP': order.price_avg-tpGap}

    # ----------------------------------------------------------------------
    # 成交后用成交价设置第一张止损止盈
    def onTrade(self, trade):
        pass

    def onStopOrder(self, so):
        pass