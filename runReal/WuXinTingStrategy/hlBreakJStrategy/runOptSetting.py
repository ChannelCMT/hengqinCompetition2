from stepwiseOptClass import stepwiseOpt
import numpy as np
import json
import os
from datetime import datetime
from hlBreakVfDsStrategyV9 import hlBreakVfDsStrategy

STRATEGYCLASS = hlBreakVfDsStrategy

# 指定引擎设置
# 指定引擎设置
ENGINESETTING = {
                "timeRange": {
                    "tradeStart":datetime(2014, 6, 1),
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
                }


# 优化目标
OPT_TARGET = "sharpeRatio"
# np.arange(0.1,0.2,0.01)
# range(1,10,1)
# 指定优化任务
OPT_TASK = [
            {"pick_freq_param": 
                {
                "adxPeriod": range(10,51,5),
                "adxLowthreshold": range(8,23,2)
                }
            }, 
            {"pick_best_param": 
                {
                "adxHighthreshold": range(30,56,5),
                "adxMaxPeriod": range(10,51,10)
                }
            }, 
            {"pick_freq_param": 
                {
                "hlEntryPeriod": range(300,501,10),
                "hlExitPeriod": range(10,61,5)
                }
            }, 

]

multiSymbolList = [
                    'IF:CTP',
                    'RB:CTP',
                    'J:CTP',
                  ]


def main():
    path = os.path.split(os.path.realpath(__file__))[0]
    with open(path+"//CTA_setting.json") as f:
        globalSetting = json.load(f)[0]

    for s in multiSymbolList:
        ENGINESETTING["contract"][0]['symbol'] = s
        globalSetting.update(ENGINESETTING)
        optimizer = stepwiseOpt(STRATEGYCLASS, ENGINESETTING, OPT_TARGET, OPT_TASK, globalSetting, '../optResult')
        optimizer.runMemoryParallel()

if __name__ == '__main__':
    main()