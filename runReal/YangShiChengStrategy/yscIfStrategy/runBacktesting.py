from vnpy.trader.app.ctaStrategy import BacktestingEngine
import pandas as pd
from vnpy.trader.utils import htmlplot
import json
import os
from datetime import datetime
from strategy import SimpleStrategy


if __name__ == '__main__':
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

    # 设置回测用的数据起始日期，initHours 默认值为 0 (20171229 20180105 20190105 20190529)
    #engine.setDataRange(datetime(2014,1,1), datetime(2017,12,31), datetime(2013,12,1))
    #engine.setDataRange(datetime(2018,1,1), datetime(2019,8,1), datetime(2017,12,1))
    # engine.setDataRange(datetime(2019,6,1), datetime(2019,8,1), datetime(2018,12,1))
    engine.setDataRange(datetime(2019,10,1), datetime(2020,1,16), datetime(2018,9,1))

    # 设置产品相关参数
    engine.setCapital(1000000)  # 设置起始资金，默认值是1,000,000 #IF RB
    contracts = [{
                    "symbol":"IF88:CTP",
                    "size" : 1, # 每点价值
                    "priceTick" : 0.01, # 最小价格变动
                    "rate" : 5/10000, # 单边手续费
                    "slippage" : 0.5 # 滑价
                    },] 

    engine.setContracts(contracts)
    engine.setLog(True, "./logIF88")
    # 获取当前绝对路径
    path = os.path.split(os.path.realpath(__file__))[0]
    with open(path+"//CTA_setting.json") as f:
        setting = json.load(f)[0]

    # Bar回测
    engine.initStrategy(SimpleStrategy, setting)
    
    # 开始跑回测
    engine.runBacktesting()
    
    # 显示回测结果
    engine.showBacktestingResult()
    engine.showDailyResult()
    
    ### 画图分析
    #chartLog = pd.DataFrame(engine.strategy.chartLog).set_index('datetime')
    #mp = htmlplot.getXMultiPlot(engine, freq="15m")
    #mp.addLine(line=chartLog[['Bollup','Bolldown','env_MAX_CLOSE_PRICE','env_MIN_CLOSE_PRICE']].reset_index(),colors={"Bollup":"green","Bolldown":"red",'slowenv_MAX_CLOSE_PRICEMa':'gray','env_MIN_CLOSE_PRICE':'gray'}, pos=0)
    #mp.resample()
    #mp.show()