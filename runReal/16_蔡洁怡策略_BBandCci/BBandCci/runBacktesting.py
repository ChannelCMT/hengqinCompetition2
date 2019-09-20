"""
展示如何执行策略回测。
"""
from vnpy.trader.app.ctaStrategy import BacktestingEngine
import pandas as pd
from datetime import datetime
from vnpy.trader.utils import htmlplot
import json
import os

if __name__ == '__main__':
    from BBandCciStrategy import BBandCciStrategy
    # 创建回测引擎
    engine = BacktestingEngine()
    engine.setDB_URI("mongodb://172.16.11.81:27017")
    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.BAR_MODE)
    # 设置使用的历史数据库
    engine.setDatabase('VnTrader_1Min_Db_contest')

    # 设置回测用的数据起始日期，initHours 默认值为 0
    # engine.setDataRange(datetime(2014,6,1), datetime(2017,12,31), datetime(2014,1,1))
    engine.setDataRange(datetime(2018,1,1), datetime(2019,8,31), datetime(2017,6,1))
    # engine.setDataRange(datetime(2014,6,1), datetime(2019,8,31), datetime(2014,1,1))

    # 设置产品相关参数
    engine.setCapital(10)  # 设置起始资金，默认值是1,000,000
    contracts = [{
                    "symbol":"IF:CTP",
                    "size" : 1, # 每点价值
                    "priceTick" : 0.001, # 最小价格变动
                    "rate" : 8/10000, # 单边手续费
                    "slippage" : 0 # 滑价
                    },] 

    engine.setContracts(contracts)
    engine.setLog(True, "./outSample")

    path = os.path.split(os.path.realpath(__file__))[0]
    with open(path+"//CTA_setting.json") as parameterDict:
        setting = json.load(parameterDict)

    print(setting[0])
    
    engine.initStrategy(BBandCciStrategy, setting[0])
    
    # 开始跑回测
    engine.runBacktesting()
    
    # 显示回测结果
    engine.showBacktestingResult()
    engine.showDailyResult()
    
    ### 画图分析
    chartLog = pd.DataFrame(engine.strategy.chartLog).set_index('datetime')
    # print(chartDf)
    mp = htmlplot.getXMultiPlot(engine, freq="15m")
    mp.addLine(line=chartLog[['bPctValue', 'cciSignal']].reset_index(), pos=1)
    mp.addLine(line=chartLog[['bandWidthValue', 'bandWidthMax']].reset_index(), pos=2)
    mp.resample()
    mp.show()