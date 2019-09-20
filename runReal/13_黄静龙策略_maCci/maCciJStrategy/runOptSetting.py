from stepwiseOptClass import stepwiseOpt
import numpy as np
import json
import os
from datetime import datetime
from cciStrategy import cciStrategy

STRATEGYCLASS = cciStrategy

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
                }


# 优化目标
OPT_TARGET = "sharpeRatio"
# np.arange(0.1,0.2,0.01)
# range(1,10,1)
# 指定优化任务
OPT_TASK = [
#             {"pick_freq_param": 
#                 {
#                 "cciPeriod": range(20, 301, 20),
#                 "sigPeriod": range(2, 6, 1)
#                 }
#             }, 
#             {"pick_freq_param": 
#                 {
#                 "maPeriod": [55, 120, 250],
#                 "modifyPct": [0.95, 0.75, 0.62, 0.5],
#                 "sigPeriod": [3, 5, 8]
#                 }
#             }, 
            # {"pick_freq_param": 
            #     {
            #     "observedCci": [95, 100, 105],
            #     "reversedCci": [80, 85, 90],
            #     "breakCci": [110, 115, 120],
            #     }
            # }, 
            {"pick_best_param": 
                {
                "volPeriod": range(20,91,20),
                "lowVolThreshold": np.arange(0.002, 0.011, 0.002)
                }
            }, 
]

multiSymbolList = [
                    # 'IF:CTP',
                    'RB:CTP',
                    'J:CTP',
                  ]


def main():
    path = os.path.split(os.path.realpath(__file__))[0]
    with open(path+"//CTA_setting.json") as f:
        globalSetting = json.load(f)[0]

    for s in multiSymbolList:
        ENGINESETTING["contracts"][0]['symbol'] = s
        globalSetting.update(ENGINESETTING)
        optimizer = stepwiseOpt(STRATEGYCLASS, ENGINESETTING, OPT_TARGET, OPT_TASK, globalSetting, '../optResult')
        optimizer.runMemoryParallel()

if __name__ == '__main__':
    main()