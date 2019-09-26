from vnpy.trader.vtConstant import *
import numpy as np
import talib as ta
from datetime import timedelta, datetime
from vnpy.trader.utils.templates.orderTemplate import * 
from vnpy.trader.app.ctaStrategy import ctaBase
from hlRegressionSignalClass import hlRegressionSignal

########################################################################
class hlRegressionStrategy(OrderTemplate):
    className = 'hlRegression'

    # 参数列表，保存了参数的名称
    paramList = [
                 'author',
                # 时间周期
                 'timeframeMap',
                 #  总秒，间隔，下单次数
                 'totalSecond', 'stepSecond','orderTime',
                 # 品种列表
                 'symbolList',
                 # 计算回归的参数
                 'regPeriod', 'zScorePeriod',
                 # 计算信号的参数
                 'rsrsThreshold',
                 'corPeriod','corThreshold'
                 # 低波动率过滤阈值
                 'volPeriod', 'lowVolThreshold',
                 ]

    # 变量列表，保存了变量的名称
    varList = []

    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['posDict', 'eveningDict']

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        super().__init__(ctaEngine, setting)
        self.paraDict = setting
        self.barPeriod = 1200
        self.symbol = self.symbolList[0]
        self.lastBarTimeDict = {frameStr: datetime(2010,1,1) for frameStr in list(set(self.timeframeMap.values()))}

        # varialbes
        self.orderDict = {'orderLongSet':set(), 'orderShortSet': set()}
        self.algorithm = hlRegressionSignal()
        self.lot = 0
        self.rsrsDirection = 0
        self.correlationDirection = 0

        # 打印全局信号的字典
        self.globalStatus = {}
        self.chartLog = {
                         "datetime":[],
                         "correlation":[],
                         "rsrsAmend":[],
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
    
    # ----------------------------------------------------------------------
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
        self.lot = int(10000000/(bar.close*30)*0.3)
        # on bar下触发回测洗价逻辑
        # start = datetime.now()
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
        self.writeCtaLog('barClose:%s'%(bar.close))

    def strategy(self, bar):
        filterPeriod= self.timeframeMap["filterPeriod"]
        signalPeriod= self.timeframeMap["signalPeriod"]
        # 根据出场信号出场
        self.exitSignal()
        self.exitOrder()

        # 根据进场信号进场
        entrySig = self.entrySignal(signalPeriod, filterPeriod)
        self.entryOrder(entrySig, bar)

    def exitSignal(self):
        pass

    def exitOrder(self):
        if (self.rsrsDirection==-1) or (self.correlationDirection==-1):
            for orderID in list(self.orderDict['orderLongSet']):
                op = self._orderPacks[orderID]
                self.composoryClose(op)
        if (self.rsrsDirection==1) or (self.correlationDirection==1):
            for orderID in list(self.orderDict['orderShortSet']):
                op = self._orderPacks[orderID]
                self.composoryClose(op)

    def entrySignal(self, signalPeriod, FilterPeriod):
        entrySig = 0
        arrayPrepared1, amSignal = self.arrayPrepared(signalPeriod)
        arrayPrepared2, amFilter = self.arrayPrepared(FilterPeriod)
        arrayPrepared = arrayPrepared1 and arrayPrepared2
        np.seterr(all='ignore')
        if arrayPrepared:
            amSignalDatetime = datetime.strptime(amSignal.datetime[-1], "%Y%m%d %H:%M:%S")
            filterCanTrade = self.algorithm.fliterVol(amFilter, self.paraDict)
            # self.globalStatus['am'] = [amSignal.datetime[-1], amFilter.datetime[-1], self.lastBarTimeDict[signalPeriod]]
            if amSignalDatetime>self.lastBarTimeDict[signalPeriod]:
                self.correlationDirection, correlation = self.algorithm.zScoreVolumeCor(amSignal, self.paraDict)
                self.rsrsDirection, rsrsAmend = self.algorithm.regDirection(amSignal, self.paraDict)
                self.lastBarTimeDict[signalPeriod] = amSignalDatetime

                self.globalStatus['rsrsDirection'] = [self.rsrsDirection, rsrsAmend[-3:]]
                self.globalStatus['correlationDirection'] = [self.correlationDirection, correlation[-3:]]
                self.globalStatus['filterCanTrade'] = filterCanTrade

                self.chartLog['datetime'].append(datetime.strptime(amSignal.datetime[-1], "%Y%m%d %H:%M:%S"))
                self.chartLog['correlation'].append(correlation[-1])
                self.chartLog['rsrsAmend'].append(rsrsAmend[-1])

            if (filterCanTrade==1):
                if (self.rsrsDirection == 1) and (self.correlationDirection == 1):
                    if not self.orderDict['orderLongSet']:
                        entrySig = 1
                elif (self.rsrsDirection == -1) and (self.correlationDirection == -1):
                    if not self.orderDict['orderShortSet']:
                        entrySig = -1
        return entrySig

    def entryOrder(self, entrySignal, bar):
        # 避免onTrade没走完就走加仓的方法设置的开关
        buyExecute, shortExecute = self.priceExecute(bar)
        lotSize = self.lot
        if entrySignal ==1:
            if not (self.orderDict['orderLongSet'] or self.orderDict['orderShortSet']):
                for orderID in self.timeLimitOrder(ctaBase.CTAORDER_BUY, bar.vtSymbol, buyExecute, max(lotSize, 1), 120).vtOrderIDs:
                    self.orderDict['orderLongSet'].add(orderID)
                    self.writeCtaLog('orderLong: close: %s, buyExecute: %s, lot: %s'%(bar.close, buyExecute, self.lot))
        elif entrySignal ==-1:
            if not (self.orderDict['orderLongSet'] or self.orderDict['orderShortSet']):
                for orderID in self.timeLimitOrder(ctaBase.CTAORDER_SHORT, bar.vtSymbol, shortExecute, max(lotSize, 1), 120).vtOrderIDs:
                    self.orderDict['orderShortSet'].add(orderID)
                    self.writeCtaLog('orderShort: close: %s, shortExecute: %s, lot: %s'%(bar.close, shortExecute, self.lot))

    # ----------------------------------------------------------------------
    def onOrder(self, order):
        super().onOrder(order)
        pass

    # ----------------------------------------------------------------------
    def onTrade(self, trade):
        super().onTrade(trade)
        pass
    
    def onStopOrder(self, so):
        """停止单推送"""
        pass