"""
这里的Demo是一个最简单的双均线策略实现
"""
from vnpy.trader.vtConstant import *
from vnpy.trader.app.ctaStrategy import CtaTemplate
import talib as ta
from datetime import datetime
from datetime import time
from MySignal import MySignal

########################################################################
# 策略继承CtaTemplate

class KMAStrategy(CtaTemplate):

    """KMA策略"""
    className = 'KMAStrategy'
    author = 'Shinie Zen'
    
    # 策略变量
    transactionPrice = 0 # 记录成交价格
    
    # 参数列表
    paramList = [
                 # 时间周期
                 'timeframeMap',
                 # 取Bar的长度
                 'barPeriod',
                 # 信号周期
                 'atrPeriod', 
                 'fastPeriod','slowPeriod', 'slowPeriod2',
                 'channelPeriod',
                 # 止损比例
                 'stopAtrTimes',
                 'stopRevTimes',
                 # 交易品种
                 'symbolList'
                ]    
    
    # 变量列表
    varList = []  
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['posDict', 'eveningDict']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        # 首先找到策略的父类（就是类CtaTemplate），然后把DoubleMaStrategy的对象转换为类CtaTemplate的对象
        super().__init__(ctaEngine, setting)
        self.paraDict = setting
        self.symbol = self.symbolList[0]
        self.tradeAtr = 0
        self.lot = 0
        self.chartLog = {
                'datetime': [],
                'fastHigh': [],
                'fastLow': [],
                'slowHigh': [],
                'slowLow': [],
                'close': [],
                'atr': [],
                'highMax': [],
                'lowMin': [],
                'slowHigh2': [],
                'slowLow2': []
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

    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略"""
        self.setArrayManagerSize(self.barPeriod)
        self.prepare_data()
        self.putEvent()

    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'策略启动')
        self.putEvent()
    
    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略"""
        self.writeCtaLog(u'策略停止')
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送"""
        pass


    def strategy(self, bar):
        print(self.symbol, self.fastPeriod, self.slowPeriod, self.slowPeriod2, self.channelPeriod, 
        self.stopAtrTimes, self.stopRevTimes)

        signalPeriod= self.timeframeMap["signalPeriod"]

        if self.tradeTime(bar):

            self.stoploss(bar)

            self.stopRev(signalPeriod)
            
            shortExitSig,longExitSig = self.exitSignal(signalPeriod)
            self.exitOrder(bar,shortExitSig,longExitSig)
            print('exitSig: ', shortExitSig,longExitSig)

            entrySig,atr = self.entrySignal(signalPeriod)
            self.entryOrder(bar, entrySig, atr)
            print('entrySig: ', entrySig)

    def onBar(self, bar):
        pass

    def on5MinBar(self, bar):
        self.lot = int(10000000/(bar.close*100*0.05)*0.3)
        self.strategy(bar)
        self.writeCtaLog('posDict:%s'%(self.posDict))
        print('posDict:', self.posDict)

    def entrySignal(self, signalPeriod):
        arrayPrepared2, amSignal = self.arrayPrepared(signalPeriod)
        if arrayPrepared2:
            algorithm = MySignal()
            signal, fastHigh, fastLow, slowHigh, slowLow, highMax, lowMin, atr, close = algorithm.entrySignal(amSignal, self.paraDict)
            
            self.chartLog['datetime'].append(datetime.strptime(amSignal.datetime[-1], "%Y%m%d %H:%M:%S"))
            self.chartLog['fastHigh'].append(fastHigh)
            self.chartLog['fastLow'].append(fastLow)
            self.chartLog['slowHigh'].append(slowHigh)
            self.chartLog['slowLow'].append(slowLow)
            self.chartLog['highMax'].append(highMax)
            self.chartLog['lowMin'].append(lowMin)
            self.chartLog['atr'].append(atr)
            self.chartLog['close'].append(close)
        return signal, atr
    

    def entryOrder(self, bar, entrySignal, atr):
        # 如果金叉时手头没有多头持仓
        if (entrySignal==1) and (self.posDict[self.symbol+'_LONG']==0):
            # 如果没有空头持仓，则直接做多
            if  self.posDict[self.symbol+'_SHORT']==0:
                self.buy(self.symbol, bar.close*1.01, self.lot)  # 成交价*1.01发送高价位的限价单，以最优市价买入进场
            # 如果有空头持仓，则先平空，再做多
            elif self.posDict[self.symbol+'_SHORT'] > 0:
                self.cancelAll() # 撤销挂单
                self.cover(self.symbol, bar.close*1.01, self.posDict[self.symbol+'_SHORT']) 
                self.buy(self.symbol, bar.close*1.01, self.lot)
            self.tradeAtr=atr
        # 如果死叉时手头没有空头持仓
        elif (entrySignal==-1) and (self.posDict[self.symbol+'_SHORT']==0):
            if self.posDict[self.symbol+'_LONG']==0:
                self.short(self.symbol, bar.close*0.99, self.lot) # 成交价*0.99发送低价位的限价单，以最优市价卖出进场
            elif self.posDict[self.symbol+'_LONG'] > 0:
                self.cancelAll() # 撤销挂单
                self.sell(self.symbol, bar.close*0.99, self.posDict[self.symbol+'_LONG'])
                self.short(self.symbol, bar.close*0.99, self.lot)
            self.tradeAtr=atr
        # 发出状态更新事件
        self.putEvent()

    def exitSignal(self, signalPeriod):
        arrayPrepared2, amSignal = self.arrayPrepared(signalPeriod)
        if arrayPrepared2:
            algorithm = MySignal()
            shortExitSignal, longExitSignal, slowHigh2, slowLow2 = algorithm.exitSignal(amSignal, self.paraDict)
            self.chartLog['slowHigh2'].append(slowHigh2)
            self.chartLog['slowLow2'].append(slowLow2)
        return shortExitSignal, longExitSignal

    def exitOrder(self, bar,shortExitSig,longExitSig):
        if (shortExitSig==1) and (self.posDict[self.symbol+'_SHORT']>0):
            self.cancelAll() # 撤销挂单
            self.cover(self.symbol, bar.close*1.01, self.posDict[self.symbol+'_SHORT']) 
        if (longExitSig==-1) and (self.posDict[self.symbol+'_LONG']>0):
            self.cancelAll() # 撤销挂单
            self.sell(self.symbol, bar.close*0.99, self.posDict[self.symbol+'_LONG'])

        # 发出状态更新事件
        self.putEvent()

    def stoploss(self, bar):
        """止损策略"""
        if self.posDict[self.symbol+'_LONG']>0:
            if bar.low<self.transactionPrice-self.stopAtrTimes*self.tradeAtr:
                print('多头止损')
                self.cancelAll()
                self.sell(self.symbol, bar.close*0.99, self.posDict[self.symbol+'_LONG'])
        if self.posDict[self.symbol+'_SHORT']>0:
            if bar.high>self.transactionPrice+self.stopAtrTimes*self.tradeAtr:
                print('空头止损')
                self.cancelAll()
                self.cover(self.symbol, bar.close*1.01, self.posDict[self.symbol+'_SHORT'])

    def stopRev(self, signalPeriod):
        arrayPrepared2, amSignal = self.arrayPrepared(signalPeriod)
        longExitLine = self.transactionPrice + self.stopRevTimes * self.tradeAtr
        shortExitLine = self.transactionPrice - self.stopRevTimes * self.tradeAtr
        if arrayPrepared2:
            if self.posDict[self.symbol+'_SHORT'] > 0 and amSignal.close[-1] > shortExitLine > amSignal.close[-2]:
                print('空头止转')
                self.cancelAll()
                self.cover(self.symbol, amSignal.close[-1]*1.01, self.posDict[self.symbol+'_SHORT'])
            if self.posDict[self.symbol+'_LONG'] > 0 and amSignal.close[-1] < longExitLine < amSignal.close[-2]:
                print('多头止转')
                self.cancelAll()
                self.sell(self.symbol, amSignal.close[-1]*0.99, self.posDict[self.symbol+'_LONG'])

    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送"""
        # 对于无需做细粒度委托控制的策略，可以忽略onOrder
        pass
    
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """收到成交推送"""
        if trade.offset == OFFSET_OPEN:  # 判断成交订单类型
            self.transactionPrice = trade.price # 记录成交价格

    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass

    def tradeTime(self,bar):
        if self.symbol=='IF:CTP':
            return True
        else:
            if time(9,0)<=bar.datetime.time()<time(15,0):
                return True
            else:
                return False