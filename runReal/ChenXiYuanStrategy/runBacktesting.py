"""
展示如何执行策略回测。
"""
from vnpy.trader.app.ctaStrategy import BacktestingEngine
import pandas as pd
from vnpy.trader.utils import htmlplot
import json
import os
from KMAStrategy import KMAStrategy
from datetime import datetime

# 
if __name__ == '__main__':
    #设定回测品种 btc.usd.q:okef IF88:CTP
    symbolName="J:CTP"
    

    # 创建回测引擎
    engine = BacktestingEngine()
    # engine.setDB_URI("mongodb://localhost:27017")
    engine.setDB_URI("mongodb://172.16.11.81:27017")

    # Bar回测
    engine.setBacktestingMode(engine.BAR_MODE)
    engine.setDatabase('VnTrader_1Min_Db_contest')

    # Tick回测
    # engine.setBacktestingMode(engine.TICK_MODE)
    # engine.setDatabase('VnTrader_1Min_Db', 'VnTrader_Tick_Db')

    # 设置回测用的数据起始日期，initHours 默认值为 0
    #engine.setStartDate('20180202 10:00:00')
    #engine.setStartDate('20180202 10:00:00',initHours=10)
    # engine.setStartDate('20180202 10:00:00',initHours=10)
    # engine.setStartDate('20181130 10:00:00',initHours=10)
    #engine.setEndDate('20190321 23:00:00')
    #engine.setDataRange(datetime(2014,1,1),datetime(2015,12,31),datetime(2013,7,1))
    #engine.setDataRange(datetime(2016,1,1),datetime(2017,12,31),datetime(2015,7,1))
    #engine.setDataRange(datetime(2014,1,1),datetime(2017,12,31),datetime(2013,7,1))
    #engine.setDataRange(datetime(2018,1,1),datetime(2019,7,31),datetime(2017,7,1))
    engine.setDataRange(datetime(2019,4,1),datetime(2019,7,31),datetime(2018,7,1))

    # 设置产品相关参数
    engine.setCapital(10000000)  # 设置起始资金，默认值是1,000,000
  
    contracts = [{
                    "symbol":symbolName,

                    "rate" : 0.0005, # 单边手续费
                    "slippage" : 0.5 # 滑价
                    },] 
#                    "size" : 1, # 每点价值
                    #"priceTick" : 0.01, # 最小价格变动
    engine.setContracts(contracts)
    engine.setLog(True,"./log{0}".format(symbolName[:symbolName.find(':')]))
    # 获取当前绝对路径
    path = os.path.split(os.path.realpath(__file__))[0]
    with open(path+"//CTA_setting.json") as f:
        setting = json.load(f)[0]

    # Bar回测
    engine.initStrategy(KMAStrategy, setting)
    
    # 开始跑回测
    engine.runBacktesting()
    
    # 显示回测结果
    engine.showBacktestingResult()
    engine.showDailyResult()
    
    ### 画图分析
    chartLog = pd.DataFrame(engine.strategy.chartLog).set_index('datetime')
    chartLog.head()
    chartLog.to_excel("{0}_chartLog.xlsx".format(symbolName[:symbolName.find(':')]))

    mp = htmlplot.getXMultiPlot(engine, freq="30m")
    mp.addLine(line=chartLog[['close',
    'fastHigh', 'fastLow','slowHigh','slowLow', 'slowHigh2', 'slowLow2',
    'highMax', 'lowMin']].reset_index(),
    colors={'close':'red',
    'fastHigh':'blue','fastLow':'blue','slowHigh':'green','slowLow':'green', 
    'slowHigh2': 'black', 'slowLow2': 'black',
    'highMax': 'orange', 'lowMin': 'orange'}, pos=0)
    mp.addLine(line = chartLog[['atr']].reset_index(), pos = 1)
    mp.resample()
    mp.show()


