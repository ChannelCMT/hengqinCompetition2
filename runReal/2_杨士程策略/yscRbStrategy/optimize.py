from vnpy.trader.utils import optimize
from strategy import SimpleStrategy
from datetime import datetime
import os
import json

def setConfig(root=None):
    # 设置策略类
    optimize.strategyClass = SimpleStrategy
    # 设置缓存路径，如果不设置则不会缓存优化结果。
    optimize.root = root
    # 设置引擎参数
    optimize.engineSetting = {
        "timeRange": {
            "tradeStart": datetime(2014,1,1),
            "tradeEnd": datetime(2017,12,31),
            "historyStart": datetime(2013,12,1)
        },
        "dbURI": "localhost",
        "bardbName": "vnTrader_1Min_Db",
        "contracts":[
            {
                "symbol":"IF:CTP",
                "rate" : 5/10000, # 单边手续费 IF RB  2019,8,1  2017,12,31
                "slippage" : 0.5 # 滑价
            }
        ]
    }

    # 设置策略固定参数
    optimize.globalSetting = {
        "symbolList": ["IF:CTP"],
        "barPeriod": 150,
    }
    # 设置策略优化参数
    optimize.paramsSetting = {
            "Env_trend_period": 30, #range(20,61,5),
            "Env_trend_value": 0.5,

            "trend_condition_period": 25, #range(20,61,5),
            "EfficiencyRation_threshold": 0.5,

            "BOLL_MID_MA_strend": 50, #range(35,51,5),
            "BOLL_SD_strend": 27, #range(20,31,1),
            
            "BOLL_MID_MA_wtrend": 40, #range(20,61,5),
            "BOLL_SD_wtrend": 22, #range(20,31,1),
            "ATR_period": range(10,31,1),
            "ATR_threshold": range(2,5,1),
            "ROC_Period": 65, #range(20,81,5),
            "ROC_MA_Period": 70, #range(20,81,5),

            "BOLL_MID_MA_ntrend": 30, #range(20,51,5),
            "BOLL_SD_ntrend": 24, #range(20,31,1),
            "MA_Short_period": 50, #range(20,121,5),
            "MA_Long_period": 60, #range(80,121,5),
            "ntrend_Stop_Time": 6,

            "Capital": 500000,
            "lot" : 0.4,
            "wlot" : 0.3,
            "addTime": 1,
            "addlot": 0.1,
            "addPre": 0.03
    }
    path = os.path.split(os.path.realpath(__file__))[0]
    with open(path+"//setting.json") as f:
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
    report.to_csv('opt_IF88.csv')    
    end = datetime.now()
    print("run simple | end: %s | expire: %s -----------------------------" % (end, end-start))

def main():
    runSimpleParallel()

if __name__ == '__main__':
    main()