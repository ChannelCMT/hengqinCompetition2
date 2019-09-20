from vnpy.trader.app.ctaStrategy import BacktestingEngine
import pandas as pd
from datetime import datetime
from vnpy.trader.utils import htmlplot
import json
import os

if __name__ == '__main__':
    from hlBreakVfDsStrategy import hlBreakVfDsStrategy
    # 创建回测引擎
    engine = BacktestingEngine()
    engine.setDB_URI("mongodb://172.16.11.81:27017")
    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.BAR_MODE)
    engine.setDatabase('VnTrader_1Min_Db_contest')

    # 设置回测用的数据起始日期，initHours 默认值为 0
    # engine.setDataRange(datetime(2014,6,1), datetime(2017,12,31), datetime(2014,1,1))
    # engine.setDataRange(datetime(2018,1,1), datetime(2019,8,31), datetime(2017,6,1))
    engine.setDataRange(datetime(2019,6,1), datetime(2019,8,31), datetime(2018,6,1))

    # 设置产品相关参数
    engine.setCapital(10000000)  # 设置起始资金，默认值是1,000,000
    contracts = [{
                    "symbol":"J:CTP",
                    "size" : 1, # 每点价值
                    "priceTick" : 0.001, # 最小价格变动
                    "rate" : 5/10000, # 单边手续费
                    "slippage" : 0 # 滑价
                    },] 
                    
    engine.setContracts(contracts)
    # engine.setLog(True, "./inSample")
    engine.setLog(True, "./outSample") 


    path = os.path.split(os.path.realpath(__file__))[0]
    with open(path+"//CTA_setting.json") as parameterDict:
        setting = json.load(parameterDict)

    print(setting[0])
    
    engine.initStrategy(hlBreakVfDsStrategy, setting[0])
    
    # 开始跑回测
    engine.runBacktesting()
    
    # 显示回测结果
    engine.showBacktestingResult()
    engine.showDailyResult()
    
    ### 画图分析
    chartDf = pd.DataFrame(engine.strategy.chartLog).drop_duplicates().set_index('datetime')
    mp = htmlplot.getMultiPlot(engine, freq="15m")
    mp.show()
    