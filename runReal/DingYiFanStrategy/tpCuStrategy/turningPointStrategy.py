"""
这里的Demo是一个最简单的双均线策略实现
"""
from vnpy.trader.vtConstant import *
from vnpy.trader.app.ctaStrategy import CtaTemplate
import talib as ta
from datetime import datetime
import numpy as np
from turningPointSignal import tpSignal

########################################################################
# 策略继承CtaTemplate
class TurningPointStrategy(CtaTemplate):
    """转折点策略"""
    className = 'TurningPointStrategy'
    author = 'Right.Ding'
    
    # 策略变量
    transactionPrice = None # 记录成交价格
    
    # 参数列表
    paramList = [
                 # 时间周期
                 'timeframeMap',
                 # 交易品种
                 'symbolList',
                 # 取Bar的长度
                 'barPeriod',
                 # 环境周期
                 'envPeriod',

                 'nBar',
                 'base_range',
                 'back_range',

                 'ma_period',
                 'sp_length',
                 'profit_r',
                 'loss_r',
                 'change_r1',
                 'change_r2',
                 'dif_r1',
                 'dif_r2',

                 'posTime',
                 'addPct'
                ]    
    
    # 变量列表
    varList = []  
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['posDict', 'eveningDict']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        # 首先找到策略的父类（就是类CtaTemplate），然后把TurningPointStrategy的对象转换为类CtaTemplate的对象
        super().__init__(ctaEngine, setting)
        self.paraDict = setting
        self.symbol = self.symbolList[0]
        self.lot = 0
        self.chartLog = {
                'datetime':[],
                'close':[],
                'envMa':[],
                'outline1':[],
                'outline2':[],

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
        self.out_pos = [0,None]
    
    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略"""
        self.writeCtaLog(u'策略停止')
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送"""
        pass
    
    def stoploss(self, bar):
        if self.posDict[self.symbol+'_LONG']>0:
            if bar.low<self.transactionPrice*(1-self.stoplossPct):
                self.cancelAll()
                self.sell(self.symbol, bar.close*0.99, self.posDict[self.symbol+'_LONG'])
        if self.posDict[self.symbol+'_SHORT']>0:
            if bar.high>self.transactionPrice*(1+self.stoplossPct):
                self.cancelAll()
                self.cover(self.symbol, bar.close*1.01, self.posDict[self.symbol+'_SHORT'])

    def strategy(self, bar):
        envPeriod= self.timeframeMap["envPeriod"]
        exitPeriod= self.timeframeMap["exitPeriod"]
        addPeriod= self.timeframeMap["addPeriod"]
        # 根据进场信号进场
        if self.posDict[self.symbol+'_LONG']==0 and self.posDict[self.symbol+'_SHORT']==0:
            entrySig, out_po = self.entrySignal(envPeriod)
            if out_po[0] != 0:
                self.out_pos = out_po
            self.entryOrder(bar, entrySig)

        # 根据出场信号出场
        if self.posDict[self.symbol+'_LONG']!=0 or self.posDict[self.symbol+'_SHORT']!=0:
            exitSig = self.exitSignal(exitPeriod, self.out_pos)
            self.exitOrder(bar, exitSig)

            # 加仓判断
            # if exitSig == 0 and self.out_pos[4]:
            #     # 如果没有触发止盈止损，且未加过仓
            #     addSig = self.addSignal(addPeriod, self.out_pos)
            #     self.addOrder(bar, addSig)
        
        # 盈利加仓
        # self.addPosOrder1(bar)
        # 亏损加仓
        # self.addPosOrder2(bar)

    def onBar(self, bar):
        pass

    def on5MinBar(self, bar):
        self.lot = int(10000000/(bar.close*5*0.09)*0.3*0.25)
        self.strategy(bar)
        self.writeCtaLog('posDict:%s'%(self.posDict))
        self.writeCtaLog('barClose:%s'%(bar.close))

    def exitSignal(self, exitPeriod, ot_pos):
        arrayPrepared, am = self.arrayPrepared(exitPeriod)
        exitSign = 0
        if arrayPrepared:
            envMa = ta.MA(am.close, self.ma_period)
            self.chartLog['envMa'].append(envMa[-1])
            if ot_pos[0] == 1:
                self.chartLog['datetime'].append(datetime.strptime(am.datetime[-1], "%Y%m%d %H:%M:%S"))
                self.chartLog['close'].append(am.close[-1])
                self.chartLog['outline1'].append(ot_pos[1])
                self.chartLog['outline2'].append(self.transactionPrice+ot_pos[3])
                if am.close[-1] < ot_pos[1]:
                    exitSign = -1
                    # print("多头止损", am.close[-1]-self.transactionPrice)
                # elif am.close[-1] > ot_pos[1]+ot_pos[3]:
                elif am.close[-1] > self.transactionPrice+ot_pos[3]:
                    exitSign = -1
                    # print("多头止盈", am.close[-1]-self.transactionPrice)
                if am.close[-1] > ot_pos[2]:
                    self.out_pos[1] = self.out_pos[1] + self.change_r1*(am.close[-1] - ot_pos[2])
                    self.out_pos[2] = am.close[-1]
                    # print(self.out_pos)
                elif am.close[-1] < ot_pos[2]:
                    self.out_pos[3] = self.out_pos[3] + self.change_r2*(am.close[-1] - ot_pos[2])
                    self.out_pos[2] = am.close[-1]
                
            elif ot_pos[0] == -1:
                self.chartLog['datetime'].append(datetime.strptime(am.datetime[-1], "%Y%m%d %H:%M:%S"))
                self.chartLog['close'].append(am.close[-1])
                self.chartLog['outline1'].append(ot_pos[1])
                self.chartLog['outline2'].append(self.transactionPrice-ot_pos[3])
                if am.close[-1] > ot_pos[1]:
                    exitSign = 1
                    # print("空头止损", self.transactionPrice-am.close[-1])
                # elif am.close[-1] < ot_pos[1]-ot_pos[3]:
                elif am.close[-1] < self.transactionPrice-ot_pos[3]:
                    exitSign = 1
                    # print("空头止盈", self.transactionPrice-am.close[-1])
                if am.close[-1] < ot_pos[2]:
                    self.out_pos[1] = self.out_pos[1] + self.change_r1*(am.close[-1] - ot_pos[2])
                    self.out_pos[2] = am.close[-1]
                    # print(self.out_pos)
                elif am.close[-1] > ot_pos[2]:
                    self.out_pos[3] = self.out_pos[3] - self.change_r2*(am.close[-1] - ot_pos[2])
                    self.out_pos[2] = am.close[-1]

        return exitSign

    def exitOrder(self, bar, exitSig):
        if self.posDict[self.symbol+'_LONG']>0:
            if exitSig==-1:
                self.cancelAll()
                self.sell(self.symbol, bar.close*0.99, self.posDict[self.symbol+'_LONG'])
        if self.posDict[self.symbol+'_SHORT']>0:
            if exitSig==1:
                self.cancelAll()
                self.cover(self.symbol, bar.close*1.01, self.posDict[self.symbol+'_SHORT'])

    def entrySignal(self, envPeriod):
        arrayPrepared, amEnv = self.arrayPrepared(envPeriod)
        entrySignal = 0
        ot_pos = np.array([0])
        if arrayPrepared:
            algorithm = tpSignal()
            # 多头返回的list [1, 止损低点, 理论买入价, 期望止盈幅度, True, count]
            # 空头返回的list [-1, 止损高点, 理论卖出价, 期望止盈幅度, True, count]
            # 无信号返回list [0, None]
            ot_pos,envMa = algorithm.trendDirection(amEnv, self.paraDict)
            entrySignal = ot_pos[0]

            outline1 = amEnv.close[-1]
            outline2 = amEnv.close[-1]
            if entrySignal != 0:
                outline1 = ot_pos[1]
                if entrySignal > 0:
                    outline2 = ot_pos[2]+ot_pos[3]
                elif entrySignal < 0:
                    outline2 = ot_pos[2]-ot_pos[3]
            #     print(ot_pos[0]*(ot_pos[2]-ot_pos[1]),"损-益",ot_pos[3])
            #     print(ot_pos[0], ot_pos[4], ot_pos[5])

            self.chartLog['datetime'].append(datetime.strptime(amEnv.datetime[-1], "%Y%m%d %H:%M:%S"))
            self.chartLog['close'].append(amEnv.close[-1])
            self.chartLog['envMa'].append(envMa[-1])
            self.chartLog['outline1'].append(outline1)
            self.chartLog['outline2'].append(outline2)
            
        return entrySignal, ot_pos

    def addSignal(self, addPeriod, ot_pos):
        arrayPrepared, am = self.arrayPrepared(addPeriod)
        addSign = 0
        if arrayPrepared:
            # half_p = 0.5 * (self.transactionPrice + ot_pos[1])
            
            if ot_pos[0] == 1:
                half_p = self.transactionPrice + 0.5 * ot_pos[3]
                change = (am.close[-1]-am.low[-1])/am.low[-1] > 0.005
                if am.low[-1] < half_p < am.close[-1]:
                    addSign = 1
                    self.out_pos[4] = False
                    self.out_pos[3] = 0.4 * self.out_pos[3]

            elif ot_pos[0] == -1:
                half_p = self.transactionPrice - 0.5 * ot_pos[3]
                change = (am.high[-1]-am.close[-1])/am.high[-1] > 0.005
                if am.high[-1] > half_p > am.close[-1]:
                    addSign = 1
                    self.out_pos[4] = False
                    self.out_pos[3] = 0.4 * self.out_pos[3]

        return addSign

    def entryOrder(self, bar, entrySignal):
        if (entrySignal==1) and (self.posDict[self.symbol+'_LONG']==0):
            if  self.posDict[self.symbol+'_SHORT']==0:
                self.buy(self.symbol, bar.close*1.01, self.lot)  # 成交价*1.01发送高价位的限价单，以最优市价买入进场
            elif self.posDict[self.symbol+'_SHORT'] > 0:
                self.cancelAll() # 撤销挂单
                self.cover(self.symbol, bar.close*1.01, self.posDict[self.symbol+'_SHORT']) 
                self.buy(self.symbol, bar.close*1.01, self.lot)

        elif (entrySignal==-1) and (self.posDict[self.symbol+'_SHORT']==0):
            if self.posDict[self.symbol+'_LONG']==0:
                self.short(self.symbol, bar.close*0.99, self.lot) # 成交价*0.99发送低价位的限价单，以最优市价卖出进场
            elif self.posDict[self.symbol+'_LONG'] > 0:
                self.cancelAll() # 撤销挂单
                self.sell(self.symbol, bar.close*0.99, self.posDict[self.symbol+'_LONG'])
                self.short(self.symbol, bar.close*0.99, self.lot)
        self.putEvent()

    def addOrder(self, bar, addSignal):
        if addSignal==1:
            self.out_pos[4]=False
            if self.out_pos[0]==1:
                self.buy(self.symbol, bar.close*1.01, self.lot)

            elif self.out_pos[0]==-1:
                self.short(self.symbol, bar.close*0.99, self.lot)
            self.putEvent()


        # self.entryOrder(maCrossSignal)

    def addPosOrder1(self, bar):
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
        
    def addPosOrder2(self, bar):
        lastOrder=self.transactionPrice
        if self.posDict[self.symbol+'_LONG'] ==0 and self.posDict[self.symbol + "_SHORT"] == 0:
                self.nPos = 0
        # 马丁格尔加仓模块______________________________________
        if (self.posDict[self.symbol+'_LONG']!=0 and self.nPos < self.posTime):    # 持有多头仓位并且加仓次数不超过3次
            if lastOrder/bar.close-1>= self.addPct:   # 计算亏损比例,达到2%
                self.nPos += 1  # 加仓次数减少 1 次
                addLot = self.lot*(2**self.nPos)
                self.buy(self.symbol,bar.close*1.02,addLot)  # 加仓 2手、4手、8手
        elif (self.posDict[self.symbol + "_SHORT"] != 0 and self.nPos < self.posTime):    # 持有空头仓位并且加仓次数不超过3次
            if bar.close/lastOrder-1 >= self.addPct:   # 计算亏损比例,达到2%
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