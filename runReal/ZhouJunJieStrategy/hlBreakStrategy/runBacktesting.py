"""
展示如何执行策略回测。
"""
from vnpy.trader.app.ctaStrategy import BacktestingEngine
import pandas as pd
from vnpy.trader.utils import htmlplot
import json
import os
from datetime import datetime
from hlBreakStrategyCtp import hlBreakStrategy

# 
if __name__ == '__main__':
    # 创建回测引擎
    engine = BacktestingEngine()
    # engine.setDB_URI("mongodb://localhost:27017")
    engine.setDB_URI("mongodb://172.16.11.81:27017")

    # Bar回测
    engine.setBacktestingMode(engine.BAR_MODE)
    engine.setDatabase('VnTrader_1Min_Db_contest')
    # engine.setDataRange(datetime(2014,1,1), datetime(2017,12,31), datetime(2013,1,1))
    # engine.setDataRange(datetime(2017,12,31), datetime(2019,7,31), datetime(2017,6,1))
    # engine.setDataRange(datetime(2014,3,1), datetime(2019,7,31), datetime(2013,1,1))
    # engine.setDataRange(datetime(2019,5,1),datetime(2019,8,31),datetime(2018,1,1))
    engine.setDataRange(datetime(2019,10,1), datetime(2020,1,16), datetime(2018,9,1))
    


    # 设置产品相关参数
    engine.setCapital(1000000)  # 设置起始资金，默认值是1,000,000
    contracts = [{
                    "symbol":"IF88:CTP",
                    "size" : 1, # 每点价值
                    "priceTick" : 0.01, # 最小价格变动
                    "rate" : 8/10000, # 单边手续费
                    "slippage" : 0.1 # 滑价
                    },] 

    engine.setContracts(contracts)
    engine.setLog(True, "./logIF88")
    # 获取当前绝对路径
    path = os.path.split(os.path.realpath(__file__))[0]
    with open(path+"//CTA_setting.json") as f:
        setting = json.load(f)[0]
    print(setting)

    # Bar回测
    engine.initStrategy(hlBreakStrategy, setting)
    
    # 开始跑回测
    engine.runBacktesting()
    
    # 显示回测结果
    engine.showBacktestingResult()
    engine.showDailyResult()
    
    ### 画图分析
    chartLog = pd.DataFrame(engine.strategy.chartLog).set_index('datetime')
    mp = htmlplot.getXMultiPlot(engine, freq="5m")
    mp.addLine(line=chartLog[['highEntryBand', 'lowEntryBand']].reset_index(), pos=0)
    mp.addLine(line=chartLog['cmiMa'].reset_index(), pos=1)
    mp.addLine(line=chartLog[['atr','rsi']].reset_index(), pos=1)
    mp.addLine(line=chartLog[['lma','sma']].reset_index(), pos=2)
    mp.addLine(line=chartLog[['dsSma','dsLma']].reset_index(), pos=3)
    mp.resample()
    mp.show()