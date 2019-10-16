"""
展示如何执行策略回测。
"""
from vnpy.trader.app.ctaStrategy import BacktestingEngine
import pandas as pd
from vnpy.trader.utils import htmlplot
import json
import os
from datetime import datetime
from SkewBaseStrategy_V3 import SkewBaseStrategy

# 
if __name__ == '__main__':
    # 创建回测引擎
    engine = BacktestingEngine()
    engine.setDB_URI("mongodb://localhost:27017")

    # Bar回测
    engine.setBacktestingMode(engine.BAR_MODE)
    engine.setDatabase('VnTrader_1Min_Db')
    # 样本内
    # engine.setDataRange(datetime(2014,1,1), datetime(2017,12,31), datetime(2013,7,1)) 
    # 样本外
    engine.setDataRange(datetime(2018,1,1), datetime(2019,7,31), datetime(2017,7,1)) 
    # 全样本
    # engine.setDataRange(datetime(2014,1,1), datetime(2019,7,31), datetime(2013,7,1)) 
    # 简单测试
    # engine.setDataRange(datetime(2018,3,23), datetime(2019,3,22), datetime(2017,5,1)) # 测试用

    # 获取当前绝对路径
    path = os.path.split(os.path.realpath(__file__))[0]
    with open(path+"//CTA_setting_IF.json") as f:
    # with open(path+"//CTA_setting.json") as f:
        setting = json.load(f)[0]
    print(setting)

    # 设置产品相关参数
    engine.setCapital(10000000)  # 设置起始资金，默认值是1,000,000
    contracts = [{
                    "symbol":'IF:CTP',
                    "size" : 300, # 每点价值
                    "priceTick" : 0.2, # 最小价格变动
                    "rate" : 2/10000, # 单边手续费
                    "slippage" : 0 # 滑价
                    },] 

    multiSymbolList = [
                    'IF:CTP',
                    # 'Y:CTP',
                    # 'M:CTP',
                    # 'I:CTP',
                    # 'FU:CTP',
                    # 'M:CTP',
                    # 'I:CTP',
                    # 'J:CTP',
                    ]

    for s in multiSymbolList:
        contracts[0]['symbol'] = s
        engine.setContracts(contracts)
        engine.setLog(True, "./log")

        # Bar回测
        setting['symbolList'][0] = contracts[0]['symbol']
        engine.initStrategy(SkewBaseStrategy, setting)
        
        # 开始跑回测
        engine.runBacktesting()
        
        # 显示回测结果
        showFigture = 1
        if showFigture == True:
            engine.showBacktestingResult()
            engine.showDailyResult()
        else:
            engine.showBacktestingResult(showFig=False)
            engine.showDailyResult(showFig=False)
        
        
        # # ### 画图分析
        # try:
        #     chartLog = pd.DataFrame(engine.strategy.chartLog).set_index('datetime', drop=False)
        #     chartLog['SkewLongThreshold'] = setting['skewLongThreshold_left']
        #     chartLog['-SkewLongThreshold'] = -chartLog['SkewLongThreshold']
        #     # chartLog['skewThreshold_right'] = setting['skewThreshold_right']
        #     # print(chartLog.describe()) # 查看信号分布
        #     mp = htmlplot.getXMultiPlot(engine, freq="5m")
        #     mp.addLine(line=chartLog[['HigherAfterEntry','LowerAfterEntry']].reset_index(), colors={'HigherAfterEntry':'orange','LowerAfterEntry':'orange'}, pos=0)
        #     mp.addLine(line=chartLog[['shortSkew','longSkew','SkewLongThreshold','-SkewLongThreshold']].reset_index(), 
        #     colors={'shortSkew':"green", 'longSkew':'blue','SkewLongThreshold':'red','-SkewLongThreshold':'red'}, pos=1)
        #     # mp.addVBar(vbar=chartLog[['datetime','maVolume']], colors={'maVolume':'blue'}, pos=2)
        #     mp.addLine(line=chartLog[['maVolume','volumeUpper']].reset_index(), colors={'maVolume':'blue','volumeUpper':'green'}, pos=2)
        #     mp.resample()
        #     mp.show()

        # except ValueError: # 测试用，忽略
        #     for k in engine.strategy.chartLog.keys():
        #         print(k,len(engine.strategy.chartLog[k]))