"""
带量能的布林线突破策略

交易规则：
捕捉到以下信号时，分别开平仓做多做空：
做多：价格突破布林线上轨且成交量巨大；
做空：价格跌破布林线中轨且成交量巨大；
平仓：
　　多单信号1：价格回归到布林线上轨；
　　多单信号2：价格跌破布林线中轨且成交量巨大；
　　空单信号1：价格恢复至布林线下轨；
　　空单信号2：价格突破布林线中轨且成交量巨大；
"""

from vnpy.trader.vtConstant import *
from vnpy.trader.app.ctaStrategy import CtaTemplate
import talib as ta
from datetime import datetime
from Price_VolumeSignal import Price_Volume

########################################################################
# 策略继承CtaTemplate
class Price_VolumeStrategy(CtaTemplate):
    """量价交易策略"""
    className = 'Price_VolumeStrategy'
    author = 'Raingo'
    
    # 策略变量
    transactionPrice = None # 记录成交价格
    
    # 参数列表
    paramList = [
                 # 时间周期
                 'timeframeMap',
                 # 取Bar的长度
                 'barPeriod',
                 # 止损比例
                 'stoplossPct',
                 # 交易品种
                 'symbolList',
                 # 交易手数
                 'lot',
                 # 加仓次数
                 "posTime",
                 # 加仓时机
                 'addPct'
                ]    
    
    # 变量列表
    varList = ['transactionPrice']  
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['posDict', 'eveningDict']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting): # setting在CTA_setting.json中
        # 首先找到策略的父类（就是类CtaTemplate），然后把Price_VolumeStrategy的对象转换为类CtaTemplate的对象
        super().__init__(ctaEngine, setting)
        self.paraDict = setting
        self.symbol = self.symbolList[0]
        self.nPos = 0

        self.chartLog = {
                'datetime':[],
                'Pup':[],  # 布林线上轨
                'Pmid':[], # 布林线中轨
                'Plow':[], # 布林线下轨
                'close':[] # 价格
                }

    def prepare_data(self):
        for timeframe in list(set(self.timeframeMap.values())):
            self.registerOnBar(self.symbol, timeframe, None)

    def arrayPrepared(self, period):
        am = self.getArrayManager(self.symbol, period)
        if not am.inited: # 是否有足够的bar数
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
    
    # 止损
    def stoploss(self, bar):
        if self.posDict[self.symbol+'_LONG']>0:
            if bar.low<self.transactionPrice*(1-self.stoplossPct):
                self.cancelAll()
                self.sell(self.symbol, bar.close*0.99, self.posDict[self.symbol+'_LONG'])
        if self.posDict[self.symbol+'_SHORT']>0:
            if bar.high>self.transactionPrice*(1+self.stoplossPct):
                self.cancelAll()
                self.cover(self.symbol, bar.close*1.01, self.posDict[self.symbol+'_SHORT'])
    # 主策略
    def strategy(self, bar):
        print('Price_VolumeStrategy')
        signalPeriod= self.timeframeMap["signalPeriod"]
        # 根据出场信号出场
        exitSig = self.exitSignal(signalPeriod)
        print('exitSig:', exitSig)
        self.exitOrder(bar, exitSig)

        # 根据进场信号进场
        entrySig = self.entrySignal(signalPeriod)
        print('entrySig:', entrySig)
        self.entryOrder(bar, entrySig)

        # 触发止损
        if exitSig == 0:
            self.stoploss(bar)
        
        # 加仓
        self.addPosOrder(bar)
    
    def on5MinBar(self, bar):
        super().onBar(bar)
        self.lot = int(10000000/(bar.close*30)*0.7)
        self.strategy(bar)
        self.writeCtaLog('posDict:%s'%(self.posDict))
        print('posDict:', self.posDict)

    
    # 出场信号
    def exitSignal(self, signalPeriod):
        arrayPrepared, amSignal = self.arrayPrepared(signalPeriod)
        SellSignal = 0
        if arrayPrepared:
            algorithm = Price_Volume()
            close,BuySignal,SellSignal,Pup,Pmid,Plow = algorithm.PVSignal(amSignal, self.paraDict)
        return SellSignal
    
    # 平仓策略
    def exitOrder(self, bar, exitSignal):
        if self.posDict[self.symbol+'_LONG']>0:
            if (exitSignal==1):
                self.cancelAll()
                self.sell(self.symbol, bar.close*0.99, self.posDict[self.symbol+'_LONG'])
        elif self.posDict[self.symbol+'_SHORT']>0:
            if (exitSignal==-1):
                self.cancelAll()
                self.cover(self.symbol, bar.close*1.01, self.posDict[self.symbol+'_SHORT'])
    
    # 进场信号
    def entrySignal(self, signalPeriod):
        arrayPrepared, amSignal = self.arrayPrepared(signalPeriod)
        BuySignal = 0
        if arrayPrepared:
            algorithm = Price_Volume()
            close,BuySignal,SellSignal,Pup,Pmid,Plow = algorithm.PVSignal(amSignal, self.paraDict)
            
            self.chartLog['datetime'].append(datetime.strptime(amSignal.datetime[-1], "%Y%m%d %H:%M:%S"))
            self.chartLog['Pup'].append(Pup)
            self.chartLog['Pmid'].append(Pmid)
            self.chartLog['Plow'].append(Plow)
            self.chartLog['close'].append(close)
            
        return BuySignal
    
    # 开仓策略
    def entryOrder(self, bar, entrySignal):
        # 如果空仓时
        if (self.posDict[self.symbol+'_LONG']==0) and (self.posDict[self.symbol+'_SHORT']==0):
            if entrySignal==1:
                self.buy(self.symbol, bar.close*1.01, 2*self.lot)
            elif entrySignal==-1:
                self.short(self.symbol, bar.close*0.99, self.lot)
        self.putEvent()
        
        
        # self.entryOrder(maCrossSignal)
    
    def addPosOrder(self, bar):
        lastOrder=self.transactionPrice
        if self.posDict[self.symbol+'_LONG'] ==0 and self.posDict[self.symbol + "_SHORT"] == 0:
            self.nPos = 0
        # 反马丁格尔加仓模块______________________________________
        if (self.posDict[self.symbol+'_LONG']!=0 and self.nPos < self.posTime):    # 持有多头仓位并且加仓次数不超过3次
            if bar.close/lastOrder-1>= self.addPct:   # 计算盈利比例,达到2%
                self.nPos += 1  # 加仓次数减少 1 次
                addLot = self.lot*(2**self.nPos)
                self.buy(self.symbol,bar.close*1.02,addLot)  # 加仓 2手、4手、8手
        elif (self.posDict[self.symbol + "_SHORT"] != 0 and self.nPos < self.posTime):    # 持有空头仓位并且加仓次数不超过3次
            if lastOrder/bar.close-1 >= self.addPct:   # 计算盈利比例,达到2%
                self.nPos += 1  # 加仓次数减少 1 次
                addLot = self.lot*(2**self.nPos)
                self.short(self.symbol,bar.close*0.98,addLot)  # 加仓 2手、4手、8手
    
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