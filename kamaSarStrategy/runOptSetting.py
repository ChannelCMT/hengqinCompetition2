from stepwiseOptClass import stepwiseOpt
import numpy as np
import json
import os
from datetime import datetime
from kamaSarStrategy import kamaSarStrategy

STRATEGYCLASS = kamaSarStrategy

# 指定引擎设置
ENGINESETTING = {
                "timeRange": {
                    "tradeStart":datetime(2014, 3, 1),
                    "tradeEnd":datetime(2017, 12, 30),
                    "historyStart":datetime(2014, 1, 1)
                    },
                "contracts":[{
                            "slippage": 0,
                            "rate": 0.0008,
                            "symbol": "IF:CTP"
                           }],
                'dbURI': "mongodb://172.16.11.81:27017",
                "bardbName": "VnTrader_1Min_Db_contest",
                "symbolList": ["IF:CTP"]
                }


# 优化目标
OPT_TARGET = "sharpeRatio"
# np.arange(0.1,0.2,0.01)
# range(1,10,1)
# 指定优化任务
OPT_TASK = [
            {"pick_freq_param": 
                {
                "kamaPeriod": range(50, 161, 20),
                "smaPeriod": range(10, 41, 10)
                }
            }, 
            {"pick_freq_param": 
                {
                "kamaFastest": range(4,25,4),
                "kamaSlowest": range(30, 101, 10)
                }
            }, 
            {"pick_best_param": 
                {
                "sarAcceleration": np.arange(0.0002,0.008,0.0002),
                }
            }, 
            {"pick_best_param": 
                {
                "dsPeriod": range(10,61,10),
                "dsThreshold": np.arange(0.1, 0.2, 0.02)
                }
            }, 
            {"pick_best_param": 
                {
                "dsSmaPeriod": np.arange(5,31,5),
                "dsLmaPeriod": np.arange(35,81,5)
                }
            }, 


]


def main():
    path = os.path.split(os.path.realpath(__file__))[0]
    with open(path+"//CTA_setting.json") as f:
        globalSetting = json.load(f)[0]

    globalSetting.update(ENGINESETTING)
    optimizer = stepwiseOpt(STRATEGYCLASS, ENGINESETTING, OPT_TARGET, OPT_TASK, globalSetting, '../optResult')
    optimizer.runMemoryParallel()

if __name__ == '__main__':
    main()