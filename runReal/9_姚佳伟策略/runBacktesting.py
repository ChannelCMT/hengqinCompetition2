"""
展示如何执行策略回测。
"""
from vnpy.trader.app.ctaStrategy import BacktestingEngine
import pandas as pd
from vnpy.trader.utils import htmlplot
import json
import os
from JarvisStrategy import JarvisStrategy
from datetime import datetime
# 
if __name__ == '__main__':
    # 创建回测引擎
    engine = BacktestingEngine()
    engine.setDB_URI("mongodb://localhost:27017")
    # engine.setDB_URI("mongodb://192.168.4.132:27017")

    # Bar回测
    engine.setBacktestingMode(engine.BAR_MODE)
    engine.setDatabase('VnTrader_1Min_Db')

    # Tick回测
    # engine.setBacktestingMode(engine.TICK_MODE)
    # engine.setDatabase('VnTrader_1Min_Db', 'VnTrader_Tick_Db')

    # 设置回测用的数据起始日期，initHours 默认值为 0
    engine.setDataRange(datetime(2014,1,1), datetime(2019,7,31), datetime(2013,10,18))
    # engine.setStartDate('20160603 10:00:00',initHours=10)
    # engine.setStartDate('20180323 10:00:00',initHours=10)
    # engine.setStartDate('20171130 10:00:00',initHours=10)
    # engine.setEndDate('20190325 23:00:00')

    # 设置产品相关参数
    engine.setCapital(1000000)  # 设置起始资金，默认值是1,000,000
    contracts = [{
                    "symbol":"IF:CTP",
                    "size" : 1, # 每点价值
                    "priceTick" : 0.01, # 最小价格变动
                    "rate" : 5/10000, # 单边手续费
                    "slippage" : 0.5 # 滑价
                    },] 

    engine.setContracts(contracts)
    engine.setLog(True, "./logIF")
    # 获取当前绝对路径
    path = os.path.split(os.path.realpath(__file__))[0]
    with open(path+"//CTA_setting.json") as f:
        setting = json.load(f)[0]

    # Bar回测
    engine.initStrategy(JarvisStrategy, setting)
    
    # 开始跑回测
    engine.runBacktesting()
    
    # 显示回测结果
    engine.showBacktestingResult()
    engine.showDailyResult()
    
    ### 画图分析
    chartLog = pd.DataFrame(engine.strategy.chartLog).set_index('datetime')
    mp = htmlplot.getXMultiPlot(engine, freq="25m")
    mp.addLine(line=chartLog[['upperBand', 'lowerBand']].reset_index(), colors={"upperBand": "yellow",'lowerBand':'green'}, pos=0)
    mp.resample()
    mp.show()