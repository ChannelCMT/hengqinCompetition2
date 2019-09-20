from vnpy.trader.utils import optimize
from turningPointStrategy import TurningPointStrategy
from datetime import datetime
import os
import json
import numpy as np

def setConfig(root=None):
    # 设置策略类
    optimize.strategyClass = TurningPointStrategy
    # 设置缓存路径，如果不设置则不会缓存优化结果。
    optimize.root = root
    # 设置引擎参数
    optimize.engineSetting = {
        # "timeRange": {
        #     "tradeStart": datetime(2017, 12, 31),
        #     "tradeEnd": datetime(2019, 8, 2),
        #     "historyStart": datetime(2016, 6, 3)
        # },
        # "timeRange": {
        #     "tradeStart": datetime(2014, 2, 18),
        #     "tradeEnd": datetime(2017, 12, 31),
        #     "historyStart": datetime(2013, 11, 4)
        # },
        "timeRange": {
            "tradeStart": datetime(2014, 2, 18),
            "tradeEnd": datetime(2019, 8, 2),
            "historyStart": datetime(2013, 11, 4)
        },
        "dbURI": "localhost",
        "bardbName": "vnTrader_1Min_Db",

        "contract":[{
                    "symbol":"JD:CTP",
                    "size" : 1, # 每点价值
                    "priceTick" : 0.01, # 最小价格变动
                    "slippage": 0.5,
                    "rate": 5/10000,
                    }]
    }
    # 设置策略固定参数
    optimize.globalSetting = {
        "symbolList": ["J:CTP"],  # 修改品种必须通过 CTA_setting.json，这里是无效的
        "barPeriod": 150,
    }
    # 设置策略优化参数
    optimize.paramsSetting = {
            # 'nBar': range(7,17,1),
            # 'base_range': np.arange(0.01, 0.021, 0.005),
            # 'back_range': np.arange(-0.007, 0, 0.002),

            # 'symbolList': [["J:CTP"], ["IF:CTP"], ["RB:CTP"], ["AG:CTP"], ["ZN:CTP"], ["TA:CTP"], ["AU:CTP"]],
            # 'symbolList': [["I:CTP"], ["SR:CTP"], ["CF:CTP"], ["BU:CTP"]],
            # 'ma_period': range(3,10,1),
            # 'profit_r': np.arange(0.8, 1.21, 0.1),
            # 'loss_r': np.arange(0.4, 0.71, 0.1),
            # 'sp_length': range(4,10,1),
            # 'change_r1': np.arange(0.1, 0.51, 0.2),
            # 'change_r2': np.arange(0, 1.01, 0.2),
            # 'dif_r1': np.arange(0.3, 1.01, 0.1),
            'dif_r2': np.arange(1.2, 1.41, 0.1),
            # 'posTime': range(1,3,1),
            # 'addPct': np.arange(0.005, 0.021, 0.005),
    }
    path = os.path.split(os.path.realpath(__file__))[0]
    with open(path+"//CTA_setting.json") as f:
        globalSetting = json.load(f)[0]
    optimize.globalSetting = globalSetting
    optimize.initOpt()

# 并行优化 无缓存
def runSimpleParallel():
    start = datetime.now()
    print("run simple | start: %s -------------------------------------------" % start)
    setConfig()
    # optimize.runParallel() 并行优化，返回回测结果
    report = optimize.runParallel()
    print(report)
    report.sort_values(by = 'sharpeRatio', ascending=False, inplace=True)
    # 将结果保存成csv
    file_name = 'opt-'+start.strftime("%m-%d-%H-%M")+'.csv'
    report.to_csv(file_name)   # 记录保存在一个与开始时间关联的csv文件
    # report.to_csv('opt_IF88.csv')     # 这一行的问题是，csv文件如果没关闭，整个优化结果都会丢失
     
    end = datetime.now()
    print("run simple | end: %s | expire: %s -----------------------------" % (end, end-start))

def main():
    runSimpleParallel()

if __name__ == '__main__':
    main()
