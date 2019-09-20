from vnpy.trader.utils import optimize
from MYStrategy import myStrategy
from datetime import datetime
import numpy as np


def setConfig(root=None):
    # 设置策略类
    optimize.strategyClass = myStrategy
    # 设置缓存路径，如果不设置则不会缓存优化结果。
    optimize.root = root
    # 设置引擎参数
    optimize.engineSetting = {
        "timeRange": {
            "tradeStart": datetime(2014, 2, 2),
            "tradeEnd":datetime(2019, 7, 20),
            "historyStart":datetime(2013, 1, 1)
        },
        "dbURI": "localhost",
        "bardbName": "vnTrader_1Min_Db",
        "contracts":[
            {
                "symbol":"IF:CTP",
                "rate" : 5/10000, # 单边手续费
                "slippage" : 0.002 # 滑价
            }
        ]
    }
    # 设置策略固定参数
    optimize.globalSetting = {
    "symbolList": ["IF:CTP"],
    "barPeriod": 300,
    "timeframeMap" :
    {"signalPeriod": "15m"},
    "macdPeriod" : 12,
    "macdsignalPeriod" : 26,
    "macdhistPeriod" : 9,
    "stopwinPeriod" : 12,
    "posTime" : 4,
    "addPct" : 0.02,
    "lot" : 10,
    "atrPeriod": 24,
    "maPeriod" : 40
    }
    # 设置策略优化参数
    optimize.paramsSetting = {
        "stopAtrTime" : np.arange(0.5,3,0.5)
    }
    optimize.initOpt()


# 格式化输出
def fprint(text):
    print(f"{text:-<100}")


# 简单优化，无并行，无缓存
def runSimple():
    start = datetime.now()
    fprint("run simple | start: %s " % start)

    setConfig()

    # optimize.run() 在设置好的参数下优化，返回回测结果
    report = optimize.run()

    # Optimization.report 返回优化结果
    print(report)
    
    end = datetime.now()
    fprint("run simple | end: %s | expire: %s " % (end, end-start))


# 并行优化 无缓存
def runSimpleParallel():
    start = datetime.now()
    fprint("run simple | start: %s " % start)

    setConfig()
    report = optimize.runParallel()
    print(report)

    end = datetime.now()
    fprint("run simple | end: %s | expire: %s " % (end, end-start))


# 简单优化，无并行，有缓存
def runMemory():

    start = datetime.now()
    fprint("run memory | start: %s " % start)

    setConfig("test-memory")
    # 开始优化，优化返回此次回测结果
    report = optimize.run()
    print(report)
    
    end = datetime.now()
    fprint("run memory | end: %s | expire: %s " % (end, end-start))


# 并行优化，有缓存
def runMemoryParallel():
    start = datetime.now()
    fprint("run memory | start: %s " % start)

    setConfig("test-memory-parallel")
    report = optimize.runParallel()

    print(report)

    end = datetime.now()
    fprint("run memory | end: %s | expire: %s " % (end, end-start))


def main():
    # runSimple()
    # runSimpleParallel()
    # runMemory()
    runMemoryParallel()


if __name__ == '__main__':
    main()