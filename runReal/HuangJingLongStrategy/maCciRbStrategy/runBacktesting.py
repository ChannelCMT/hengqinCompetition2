"""
展示如何执行策略回测。
"""
from vnpy.trader.app.ctaStrategy import BacktestingEngine
import pandas as pd
from vnpy.trader.utils import htmlplot
import json
from datetime import datetime

if __name__ == '__main__':
    from cciStrategy import cciStrategy
    # 创建回测引擎
    engine = BacktestingEngine()
    engine.setDB_URI("mongodb://172.16.11.81:27017")

    # Bar回测
    engine.setBacktestingMode(engine.BAR_MODE)
    engine.setDatabase('VnTrader_1Min_Db_contest')

    # engine.setDataRange(datetime(2014,6,1), datetime(2017,12,31), datetime(2014,1,1))
    # engine.setDataRange(datetime(2018,1,1), datetime(2019,8,31), datetime(2017,6,1))
    # engine.setDataRange(datetime(2014,6,1), datetime(2019,8,31), datetime(2014,1,1))
    engine.setDataRange(datetime(2019,10,1), datetime(2020,1,16), datetime(2018,9,1))

    # 设置产品相关参数
    engine.setCapital(10000000)  # 设置起始资金，默认值是1,000,000
    contracts = [{
                    "symbol":"RB88:CTP",
                    "size" : 1, # 每点价值
                    "priceTick" : 0.001, # 最小价格变动
                    "rate" : 5/10000, # 单边手续费
                    "slippage" : 0.005 # 滑价
                    },] 
                    
    engine.setContracts(contracts)
    engine.setLog(True, "./outSample") 
    
    with open("CTA_setting.json") as parameterDict:
        setting = json.load(parameterDict)
    
    engine.initStrategy(cciStrategy, setting[0])
    
    # 开始跑回测
    engine.runBacktesting()
    
    # 显示回测结果
    engine.showBacktestingResult()
    engine.showDailyResult()
    
    ### 画图分析
    chartLog = pd.DataFrame(engine.strategy.chartLog).set_index('datetime')
    # print(chartDf)
    mp = htmlplot.getXMultiPlot(engine, freq="15m")
    mp.addLine(line=chartLog[['ma']].reset_index(), pos=0)
    mp.addLine(line=chartLog[['cciIndicator']].reset_index(), pos=1)
    mp.resample()
    mp.show()
 