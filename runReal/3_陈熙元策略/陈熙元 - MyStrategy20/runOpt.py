from vnpy.trader.utils import optimize
from MyStrategy import KMAStrategy
from datetime import datetime
import os
import json

optList=['RB:CTP','CU:CTP','AU:CTP','BU:CTP','FU:CTP','SC:CTP',
        'M:CTP','Y:CTP','C:CTP','J:CTP','I:CTP','ME:CTP','SR:CTP','CF:CTP',
        'IF:CTP']
symbolName="J:CTP"

def setConfig(root=None):
    # 设置策略类
    optimize.strategyClass = KMAStrategy
    # 设置缓存路径，如果不设置则不会缓存优化结果。
    optimize.root = root
    # 设置引擎参数
    optimize.engineSetting = {
        "timeRange":{
            "tradeStart":datetime(2014,1,1),
            "tradeEnd":datetime(2017,12,31),
            "historyStart":datetime(2013,7,1)
        },
        "dbURI":"localhost",
        "bardbName": "VnTrader_1Min_Db",
        "contracts":[{
            "symbol":symbolName,
            "slippage": 0.5,
            "rate": 0.0005}]   
    }

    # 设置策略固定参数 
    optimize.globalSetting = {
        "timeframeMap" :
        {"signalPeriod": "30m"},
        "symbolList": [symbolName],
        "barPeriod": 200,
        "atrPeriod": 30,
        "fastPeriod": 20,
        "stopAtrTimes": 100000,
        "stopRevTimes": 100000,
        "lot":2
    }

    # 设置策略优化参数
    optimize.paramsSetting = {
        "slowPeriod": range(30, 101,10),
        "slowPeriod2": range(30, 181, 10),
        "channelPeriod": range(10, 101, 10)
    }
 
    optimize.initOpt()
    
# 格式化输出
def fprint(text):
    print(f"{text:-<100}")

# 并行优化，有缓存
def runMemoryParallel():
    start = datetime.now()
    print("run memory | start: %s " % start)
    setConfig("OptMemo_{0}".format(symbolName[:symbolName.find(':')]))
    report = optimize.runParallel()

    print(report)

    end = datetime.now()
    print("run memory | end: %s | expire: %s " % (end, end-start))


def main():
    runMemoryParallel()
    

if __name__ == '__main__':
    main()