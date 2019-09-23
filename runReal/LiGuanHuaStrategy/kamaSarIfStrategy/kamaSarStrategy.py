from vnpy.trader.vtConstant import *
import numpy as np
import talib as ta
from datetime import timedelta, datetime
from vnpy.trader.utils.templates.orderTemplate import * 
from vnpy.trader.app.ctaStrategy import ctaBase
from kamaSarClass import kamaSarSignal


########################################################################
class kamaSarStrategy(OrderTemplate):
    className = 'kamaSarStrategy'
    author = 'ChannelCMT'

    # 参数列表，保存了参数的名称
    paramList = [
                 # 品种列表
                 'symbolList',
                 # signalParameter 计算信号的参数
                 'sarAcceleration',
                 'kamaPeriod', 'kamaFastest', "kamaSlowest",
                 'smaPeriod',
                 # 低波动率过滤阈值
                 'volPeriod', 'lowVolThreshold',
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
        self.barPeriod = 200
        self.symbol = self.symbolList[0]
        self.lastBarTimeDict = {frameStr: datetime(2010,1,1) for frameStr in list(set(self.timeframeMap.values()))}
        self.algorithm = kamaSarSignal()
        self.kamaDirection = 0
        self.lot = 0

        # varialbes
        self.orderDict = {'orderLongSet':set(), 'orderShortSet': set()}
        self.orderLastList = []
        self.lastOrderDict = {'nextExecuteTime': datetime(2000, 1, 1)}
        self.nPos = 0
        # 打印全局信号的字典
        self.globalStatus = {}
        self.chartLog = {
                        'datetime':[],
                        'sar': [],
                        'kama':[],
                        'sma':[],
                        'dsSma':[],
                        'dsLma':[]
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
                # self.lastOrderDict['nextExecuteTime'] = self.currentTime + timedelta(hours=self.stopControlTime)
    
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
    
    def on5MinBar(self, bar):
        # 必须继承父类方法
        super().onBar(bar)
        # on bar下触发回测洗价逻辑
        # 定时控制，开始
        self.checkOnPeriodStart(bar)
        # 回测时的下单手数按此方法调整
        self.lot = int(10000000/(bar.close*30)*0.6*0.3)
    # 定时清除已出场的单
        self.checkOnPeriodStart(bar)
        self.checkOnPeriodEnd(bar)

        for idSet in self.orderDict.values():
            self.delOrderID(idSet)
        # 执行策略逻辑
        self.strategy(bar)

    def on15MinBar(self, bar):
        engineType = self.getEngineType()  # 判断engine模式
        if engineType != 'backtesting':
            self.writeCtaLog('globalStatus%s'%(self.globalStatus))
            self.writeCtaLog('firstVolume:%s, secondVolume:%s'%(self.getHoldVolume(self.orderDict['orderLongSet']), self.getHoldVolume(self.orderDict['orderShortSet'])))
        else:
            pass
    def strategy(self, bar):
        signalPeriod= self.timeframeMap["signalPeriod"]
        filterPeriod= self.timeframeMap["filterPeriod"]

        # 根据出场信号出场
        exitSig = self.exitSignal(signalPeriod)
        self.exitOrder(exitSig)

        # 根据进场信号进场
        entrySig = self.entrySignal(filterPeriod, signalPeriod)
        self.entryOrder(bar, entrySig)

        # 根据信号加仓
        # addPosSig = self.addPosSignal(addPosPeriod)
        # self.addPosOrder(bar, addPosSig)

    # def isStopControled(self):
    #     return self.currentTime < self.lastOrderDict['nextExecuteTime']

    def exitSignal(self, signalPeriod):
        exitSignal = 0
        arrayPrepared, amSignal = self.arrayPrepared(signalPeriod)

        if arrayPrepared:
            signalDirection, _ = self.algorithm.sarSignal(amSignal, self.paraDict)
            if signalDirection==-1:
                exitSignal = 1
            elif signalDirection==1:
                exitSignal = -1
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

    def entrySignal(self, filterPeriod, signalPeriod):
        entrySignal = 0
        arrayPrepared, amSignal = self.arrayPrepared(signalPeriod)
        amSignalDatetime = datetime.strptime(amSignal.datetime[-1], "%Y%m%d %H:%M:%S")

        if arrayPrepared:
            if amSignalDatetime>self.lastBarTimeDict[signalPeriod]:
                self.kamaDirection, kama, sma = self.algorithm.kamaSignal(amSignal, self.paraDict)
                self.lastBarTimeDict[signalPeriod] = amSignalDatetime
                signalDirection, sar = self.algorithm.sarSignal(amSignal, self.paraDict)
                preferTrade, canTrade, dsSma, dsLma =  self.algorithm.dsEnv(amSignal, self.paraDict)
                
                self.globalStatus['signalDirection'] = signalDirection
                self.chartLog['datetime'].append(datetime.strptime(amSignal.datetime[-1], "%Y%m%d %H:%M:%S"))
                self.chartLog['sar'].append(sar[-1])
                self.chartLog['kama'].append(kama)
                self.chartLog['sma'].append(sma)
                self.chartLog['dsSma'].append(dsSma[-1])
                self.chartLog['dsLma'].append(dsLma[-1])

                if preferTrade:
                    if (signalDirection==1):
                        entrySignal = 1
                    elif (signalDirection==-1):
                        entrySignal = -1
                if canTrade:
                    if (signalDirection==1) and (self.kamaDirection==1):
                        entrySignal = 1
                    elif (signalDirection==-1) and (self.kamaDirection==-1):
                        entrySignal = -1
        return entrySignal

    def entryOrder(self, bar, entrySignal):
        buyExecute, shortExecute = self.priceExecute(bar)
        if entrySignal ==1:
            if not self.orderDict['orderLongSet']:
                # 如果回测直接下单，如果实盘就分批下单
                longPos = self.lot//self.orderTime
                    # for orderID in self.timeLimitOrder(ctaBase.CTAORDER_BUY, self.symbol, buyExecute, self.lot, 120).vtOrderIDs:
                stepOrder = self.makeStepOrder(ctaBase.CTAORDER_BUY, bar.vtSymbol, buyExecute, self.lot, longPos, self.totalSecond, self.stepSecond)
                orderID = stepOrder.parentID
                self.orderDict['orderLongSet'].add(orderID)
                self.orderLastList.append(orderID)

        elif entrySignal ==-1:
            if not self.orderDict['orderShortSet']:
                shortPos = self.lot//self.orderTime
                stepOrder = self.makeStepOrder(ctaBase.CTAORDER_SHORT, bar.vtSymbol, shortExecute, self.lot, shortPos, self.totalSecond, self.stepSecond)
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