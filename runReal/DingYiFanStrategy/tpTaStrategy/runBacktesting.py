"""
展示如何执行策略回测。
"""
from vnpy.trader.app.ctaStrategy import BacktestingEngine
import pandas as pd
from vnpy.trader.utils import htmlplot
import json
import os
from datetime import datetime
from turningPointStrategy import TurningPointStrategy

# 
if __name__ == '__main__':
    # 创建回测引擎
    engine = BacktestingEngine()
    engine.setDB_URI("mongodb://172.16.11.81:27017")
    # engine.setDB_URI("mongodb://192.168.4.132:27017")

    # Bar回测
    engine.setBacktestingMode(engine.BAR_MODE)
    engine.setDatabase('VnTrader_1Min_Db_contest')

    # Tick回测
    # engine.setBacktestingMode(engine.TICK_MODE)
    # engine.setDatabase('VnTrader_1Min_Db', 'VnTrader_Tick_Db')

    # 设置回测用的数据起始日期，initHours 默认值为 0
    # engine.setDataRange(datetime(2014,2,21), datetime(2014,4,1), datetime(2013,11,4))
    # engine.setDataRange(datetime(2014,2,18), datetime(2017,12,31), datetime(2013,11,4))
    # engine.setDataRange(datetime(2017,12,31), datetime(2019,8,2), datetime(2016,6,3))
    # engine.setDataRange(datetime(2016,8,1), datetime(2019,8,2), datetime(2015,11,4))
    engine.setDataRange(datetime(2019,10,1), datetime(2020,1,16), datetime(2018,9,1))


    # 设置产品相关参数
    engine.setCapital(10000000)  # 设置起始资金，默认值是1,000,000
    contracts = [{
                    "symbol":"TA88:CTP",
                    "size" : 1, # 每点价值
                    "priceTick" : 0.01, # 最小价格变动
                    "rate" : 5/10000, # 单边手续费
                    "slippage" : 0.5 # 滑价
                    },] 

    engine.setContracts(contracts)
    name = "./log_"+contracts[0]["symbol"][:-4]
    engine.setLog(True, name)
    # 获取当前绝对路径
    path = os.path.split(os.path.realpath(__file__))[0]
    with open(path+"//CTA_setting.json") as f:
        setting = json.load(f)[0]

    # Bar回测
    engine.initStrategy(TurningPointStrategy, setting)
    
    # 开始跑回测
    engine.runBacktesting()
    
    # 显示回测结果
    engine.showBacktestingResult()
    engine.showDailyResult()
    
    ### 画图分析
    # chartLog = pd.DataFrame(engine.strategy.chartLog).set_index('datetime')
    # mp = htmlplot.getXMultiPlot(engine, freq="60m")
    # # mp.addLine(line=chartLog[['envMa','close']].reset_index(), colors={"envMa": "green", "close":"blue"}, pos=0)
    # mp.addLine(line=chartLog[['close','outline1','outline2']].reset_index(), colors={"close":"blue", "outline1": "green", "outline2": "red"}, pos=0)
    # mp.resample()
    # mp.show()