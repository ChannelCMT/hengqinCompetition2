from vnpy.trader.vtConstant import *
from vnpy.trader.app.ctaStrategy import CtaTemplate
import talib as ta
from datetime import datetime
from datetime import time
from MYSignal import mySignal


class myStrategy(CtaTemplate):
    className = 'MYStrategy'
    author = 'FJH'
    
    transactionPrice = None
    paramList = [
    'timeframeMap',
    'signalPeriod',
    'symbolList',
    'barPeriod',

    'macdPeriod',
    'macdsignalPeriod',
    'macdhistPeriod',

    'atrPeriod',
    'maPeriod',
    'stopwinPeriod',
    'stopAtrTime',
    'posTime',
    'addPct' 
    ]
    varList = []
    syncList = ['posDict','eveningDict']

    def __init__(self, ctaEngine, setting):
        super().__init__(ctaEngine, setting)
        self.paraDict = setting
        self.symbol = self.symbolList[0]
        self.lot = 0
        self.chartLog = {
            'datetime' : [],
            'close' : [],
            'macdsignal': [],
            'macdhist': [],
            'macd':[],
            'atr' : []
        }
    
    def prepare_data(self):
        for timeframe in list(set(self.timeframeMap.values())):
            self.registerOnBar(self.symbol,timeframe,None)
    
    def arrayPrepared(self,period):
        am = self.getArrayManager(self.symbol,period)
        if not am.inited:
            return False,None
        else:
            return True,am
    
    def onInit(self):
        self.setArrayManagerSize(self.barPeriod)
        self.prepare_data()
        self.putEvent()

    def onStart(self):
        self.writeCtaLog(u'策略启动')
        self.putEvent()

    def onStop(self):
        self.writeCtaLog(u'策略停止')
        self.putEvent()

    def onTick(self,tick):
        pass

    def tradeTime(self,bar):
        if time(9,0) <= bar.datetime.time() < time(15,0):
            return True
        else:
            return False

    def onBar(self, bar):
        pass
    def on5MinBar(self, bar):
        self.lot = int(10000000/(bar.close)*0.3)
        self.writeCtaLog('posDict:%s'%(self.posDict))
        # print('posDict:', self.posDict)

    def on15MinBar(self,bar):
        self.strategy(bar)

    def entrySignal(self,signalPeriod):
        arrayPrepared,amSignal = self.arrayPrepared(signalPeriod)
        if arrayPrepared:
            algorithm = mySignal()
            Signal, macd, macdsignal, macdhist = algorithm.Signal(amSignal,self.paraDict)
            atr = algorithm.ATR(amSignal,self.paraDict)
            
            self.chartLog['datetime'].append(datetime.strptime(amSignal.datetime[-1],"%Y%m%d %H:%M:%S"))
            self.chartLog['close'].append(amSignal.close[-1])
            self.chartLog['macdhist'].append(macdhist)
            self.chartLog['macdsignal'].append(macdsignal)
            self.chartLog['macd'].append(macd)
            self.chartLog['atr'].append(atr)
        return Signal

    def entryOrder(self, bar, Signal):
        if self.tradeTime(bar):
        # 如果金叉时手头没有多头持仓
            if (Signal==1) and (self.posDict[self.symbol+'_LONG']==0):
            # 如果没有空头持仓，则直接做多
                if  self.posDict[self.symbol+'_SHORT']==0:
                    self.buy(self.symbol, bar.close*1.01, self.lot)  # 成交价*1.01发送高价位的限价单，以最优市价买入进场
            # 如果有空头持仓，则先平空，再做多
                elif self.posDict[self.symbol+'_SHORT'] > 0:
                    self.cancelAll() # 撤销挂单
                    self.cover(self.symbol, bar.close*1.01, self.posDict[self.symbol+'_SHORT']) 
                    self.buy(self.symbol, bar.close*1.01, self.lot )

        # 如果死叉时手头没有空头持仓
            elif (Signal==-1) and (self.posDict[self.symbol+'_SHORT']==0):
                if self.posDict[self.symbol+'_LONG']==0:
                    self.short(self.symbol, bar.close*0.99,self.lot ) # 成交价*0.99发送低价位的限价单，以最优市价卖出进场
                elif self.posDict[self.symbol+'_LONG'] > 0:
                    self.cancelAll() # 撤销挂单
                    self.sell(self.symbol, bar.close*0.99, self.posDict[self.symbol+'_LONG'])
                    self.short(self.symbol, bar.close*0.99,self.lot )

        # 发出状态更新事件
        self.putEvent()
    
    def stoploss(self, bar,signalPeriod):
        arrayPrepared,amSignal = self.arrayPrepared(signalPeriod)
        if arrayPrepared:
            algorithm = mySignal()
            atr = algorithm.ATR(amSignal,self.paraDict)
            if self.tradeTime(bar):
                if self.posDict[self.symbol+'_LONG']>0:
                    if bar.low < (self.transactionPrice-self.stopAtrTime*atr[-1]) or bar.datetime.time() == time(14,55):
                        self.cancelAll()
                        self.sell(self.symbol, bar.close*0.99, self.posDict[self.symbol+'_LONG'])
                        print('-99')
                if self.posDict[self.symbol+'_SHORT']>0:
                    if bar.high > (self.transactionPrice-self.stopAtrTime*atr[-1]) or bar.datetime.time() == time(14,55) :
                        self.cancelAll()
                        self.cover(self.symbol, bar.close*1.01, self.posDict[self.symbol+'_SHORT'])
                        print('-99')

    def stopwin(self, bar,signalPeriod):
        arrayPrepared,amSignal = self.arrayPrepared(signalPeriod)
        if arrayPrepared:
            algorithm = mySignal()
            longwinPrice, shortwinPrice = algorithm.stopwin(amSignal,self.paraDict)
            if self.tradeTime(bar):
                if self.posDict[self.symbol+'_LONG']>0:
                    if bar.close < longwinPrice:
                        self.cancelAll()
                        self.sell(self.symbol, bar.close*0.99, self.posDict[self.symbol+'_LONG'])
                        print('99')
                if self.posDict[self.symbol+'_SHORT']>0:
                    if bar.close > shortwinPrice:
                        self.cancelAll()
                        self.cover(self.symbol, bar.close*1.01, self.posDict[self.symbol+'_SHORT'])
                        print('99')
  
    def addPosOrder(self, bar):
        lastOrder=self.transactionPrice
        if self.posDict[self.symbol+'_LONG'] ==0 and self.posDict[self.symbol + "_SHORT"] == 0:
            self.nPos = 0
        if self.posDict[self.symbol+'_LONG']!=0 and self.nPos < self.posTime:   
            if bar.close/lastOrder-1>= self.addPct:   
                self.nPos += 1  
                addLot = self.lot*(0.5**self.nPos)
                self.buy(self.symbol,bar.close*1.02,addLot)
                print('66')
        elif self.posDict[self.symbol + "_SHORT"] != 0 and self.nPos < self.posTime:   
            if lastOrder/bar.close-1 >= self.addPct:  
                self.nPos += 1  
                addLot = self.lot*(0.5**self.nPos)
                self.short(self.symbol,bar.close*0.98,addLot)
                print('66')

    def strategy(self, bar):
        print('strategystrategystrategystrategystrategy')
        signalPeriod= self.timeframeMap["signalPeriod"]
        entrySig = self.entrySignal(signalPeriod)
        self.entryOrder(bar,entrySig)
        print('entrySig:', entrySig)
        self.stoploss(bar,signalPeriod)
        self.stopwin(bar,signalPeriod)
        self.addPosOrder(bar)

    def onOrder(self, order):
        pass

    def onTrade(self, trade):
        if trade.offset == OFFSET_OPEN: 
            self.transactionPrice = trade.price
        
    def onStopOrder(self, so):
        pass
                    
        


