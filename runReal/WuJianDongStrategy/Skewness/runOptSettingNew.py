from stepwiseOptClassNew import stepwiseOpt
import numpy as np
import json
import os
from datetime import datetime
from SkewBaseStrategy_V3 import SkewBaseStrategy

STRATEGYCLASS = SkewBaseStrategy

# 指定引擎设置
ENGINESETTING = {
                "timeRange": {
                              # 样本内
                              # "tradeStart":datetime(2014, 1, 1),
                              # "tradeEnd":datetime(2017, 12, 31),
                              # "historyStart":datetime(2013, 7, 1)
                              # 样本外
                            #   "tradeStart":datetime(2018, 1, 1),
                            #   "tradeEnd":datetime(2019, 7, 31),
                            #   "historyStart":datetime(2017, 7, 1)
                              # 全样本
                              "tradeStart":datetime(2014, 1, 1),
                              "tradeEnd":datetime(2019, 7, 31),
                              "historyStart":datetime(2013, 7, 1)
                    },
                "contracts":[{
                            "slippage": 0,
                            "rate": 0.0005,
                            "symbol": None
                           }],
                'dbURI': "mongodb://localhost:27017",
                "bardbName": "VnTrader_1Min_Db",
                }


# 优化目标
OPT_TARGET = "sharpeRatio"
# np.arange(0.1,0.2,0.01)
# range(1,10,1)
# 指定优化任务
OPT_TASK = [
            # {"pick_best_param": 
            #     { # 48
            #     "signalPeriod": ['20m','30m'], # 4
            #     "fastPeriod": range(4,30,4), # 7
            #     }
            # }, 
            # {"pick_freq_param": 
            #     { # 63
            #     # "skewShortPeriod": np.arange(30,70,8), # 6
            #     # "skewLongPeriod": np.arange(32,73,8), #6
            #     "skewLongThreshold_left": np.arange(0.55,0.86,0.05), # 4
            #     # "skewShortThreshold": np.arange(-0.3,0.2,0.1), # 5
            #     }
            # }, 
            # {"pick_freq_param": 
            #     { # 175
            #     # "skewShortThreshold": [-0.2, 0],
            #     # "skewShortThreshold": np.arange(-0.4,0.3,0.1), # 7
            #     "volumeMaPeriod": np.arange(25,66,10), #5
            #     "volumeStdMultiple": np.arange(1, 2.6, 0.5), # 4
            #     }
            # }, 
            {"pick_freq_param": 
                { # 36
                "stopLossPct": np.arange(0.005, 0.025, 0.005), # 4
                "stoplossPeriod" : range(1, 6, 1), # 5
                "expectReturn": np.arange(0.005, 0.025, 0.005), # 4
                # "takeProfitLotRatio": [0.5, 0.8, 1] # 3
                }
            }, 
            # {"pick_freq_param": 
            #     { # 60
            #     # "addPct": np.arange(0.005, 0.026, 0.005), # 5
            #     # "posTime": [1,2,3], # 3
            #     # "addLotTime": [0.5, 1, 1.5, 2] # 4
            #     "expectReturn": np.arange(0.003, 0.025, 0.003), # 8
            #     "takeProfitLotRatio": [0.5, 0.8, 1] # 3
            #     }
            # }, 
]
multiSymbolList = [
                    'M:CTP',
                    'IF:CTP',
                    'J:CTP',
                  ]


def main():
    path = os.path.split(os.path.realpath(__file__))[0]
    startTime = datetime.now().strftime("%m%d%H%M")
    with open(path+"//CTA_setting.json") as f:
        globalSetting = json.load(f)[0]

    for s in multiSymbolList:
        ENGINESETTING["contracts"][0]['symbol'] = s
        globalSetting['symbolList'][0] = s
        globalSetting.update(ENGINESETTING)
        optimizer = stepwiseOpt(STRATEGYCLASS, ENGINESETTING, OPT_TARGET, OPT_TASK, globalSetting, 
                                path+'/optResult/'+STRATEGYCLASS.className+startTime)
        optimizer.runMemoryParallel(cpu_counts=7) # 设置使用的CPU核数量，可通过 os.cpu_count() 查看电脑核数量

if __name__ == '__main__':
    main()