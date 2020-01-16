"""
展示如何执行策略回测。
"""
from vnpy.trader.app.ctaStrategy import BacktestingEngine
import pandas as pd
from vnpy.trader.utils import htmlplot
import json
import os
from datetime import datetime
from DoublePeriodStrategy import DoublePeriodStrategy

# 
if __name__ == '__main__':
    # 创建回测引擎
    engine = BacktestingEngine()
    engine.setDB_URI("mongodb://172.16.11.81:27017")

    # Bar回测
    engine.setBacktestingMode(engine.BAR_MODE)
    engine.setDatabase('VnTrader_1Min_Db_contest')
    engine.setDataRange(datetime(2019,10,1), datetime(2020,1,16), datetime(2018,9,1))

    # 样本内
    # engine.setDataRange(datetime(2014,1,1), datetime(2017,12,31), datetime(2013,7,1)) 
    # engine.setDataRange(datetime(2015,8,1), datetime(2017,12,31), datetime(2015,4,20)) # IH/IC
    # engine.setDataRange(datetime(2015,8,1), datetime(2018,7,31), datetime(2015,4,20)) # 
    # 样本外
    # engine.setDataRange(datetime(2018,1,1), datetime(2019,7,31), datetime(2017,7,1)) 
    # engine.setDataRange(datetime(2018,8,1), datetime(2019,7,31), datetime(2017,7,1)) 
    # 全样本
    # engine.setDataRange(datetime(2014,1,1), datetime(2019,7,31), datetime(2013,7,1)) 
    # engine.setDataRange(datetime(2015,8,1), datetime(2019,7,31), datetime(2015,4,20)) # IH/IC
    # 分段测试
    # engine.setDataRange(datetime(2014,1,1), datetime(2015,6,30), datetime(2013,7,1)) 
    # engine.setDataRange(datetime(2015,7,1), datetime(2016,12,31), datetime(2015,1,1)) 
    # engine.setDataRange(datetime(2017,1,1), datetime(2018,6,30), datetime(2016,7,1)) 
    # engine.setDataRange(datetime(2018,1,1), datetime(2019,7,31), datetime(2017,7,1)) 

    # 获取当前绝对路径
    path = os.path.split(os.path.realpath(__file__))[0]
    # with open(path+"//CTA_setting IF2.json") as f:
    with open(path+"//CTA_setting.json") as f:
        setting = json.load(f)[0]
    print(setting)

    # 设置产品相关参数
    engine.setCapital(10000000)  # 设置起始资金，默认值是1,000,000
    contracts = [{
                    "symbol":None,
                    "size" : 200, # 每点价值
                    "priceTick" : 0.2, # 最小价格变动
                    "rate" : 2/10000, # 单边手续费
                    "slippage" : 0 # 滑价
                    },] 

    multiSymbolList = [
                    # 'IF:CTP',
                    'IC88:CTP',
                    # 'RB:CTP',
                    # 'M:CTP',
                    # 'J:CTP'
                    ]

    for s in multiSymbolList:
        contracts[0]['symbol'] = s
        engine.setContracts(contracts)
        engine.setLog(True, "./log")

        # Bar回测
        setting['symbolList'][0] = contracts[0]['symbol']
        engine.initStrategy(DoublePeriodStrategy, setting)
        
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
        #     # del engine.strategy.chartLog['HigherAfterEntry'][0]
        #     # del engine.strategy.chartLog['LowerAfterEntry'][0]
        #     chartLog = pd.DataFrame(engine.strategy.chartLog).set_index('datetime',drop=False)
        #     # chartLog['erThreshold_low'] = setting['erThreshold_low']
        #     # chartLog['erThreshold_high'] = setting['erThreshold_high']
        #     # chartLog['-erThreshold'] = -chartLog['erThreshold'] 
        #     mp = htmlplot.getXMultiPlot(engine, freq="5m")
        #     mp.addLine(line=chartLog[['fastMa','slowMa','HigherAfterEntry','LowerAfterEntry']].reset_index(), 
        #     colors={"fastMa":"red",'slowMa':'blue','HigherAfterEntry':'orange','LowerAfterEntry':'orange'}, pos=0)
        #     # mp.addLine(line=chartLog[['envMa','er','erThreshold','-erThreshold']].reset_index(), colors={'envMa':"green",'er':'orange','erThreshold':'blue','-erThreshold':'blue'}, pos=1)
        #     mp.addVBar(vbar=chartLog[['datetime','entrySignalLong','entrySignalShort']], colors={'entrySignalLong':'mediumspringgreen','entrySignalShort':'salmon'}, pos=0)
        #     mp.addLine(line=chartLog[['envMa']].reset_index(), colors={'envMa':"green"}, pos=1)

        #     mp.resample()
        #     mp.show()
        #     # print(chartLog.describe())

        # except ValueError: # debug用
        #     for k in engine.strategy.chartLog.keys():
        #         print(k,len(engine.strategy.chartLog[k]))