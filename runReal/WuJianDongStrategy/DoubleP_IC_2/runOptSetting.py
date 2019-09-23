from stepwiseOptClass import stepwiseOpt
import numpy as np
import json
import os
from datetime import datetime
from DoublePeriodStrategy_v5 import DoublePeriodStrategy

STRATEGYCLASS = DoublePeriodStrategy

# 指定引擎设置
ENGINESETTING = {
                "timeRange": {
                              # 样本内
                              "tradeStart":datetime(2014, 1, 1),
                              "tradeEnd":datetime(2017, 12, 31),
                              "historyStart":datetime(2013, 7, 1)
                              # 样本外
                              # "tradeStart":datetime(2018, 1, 1),
                              # "tradeEnd":datetime(2019, 7, 31),
                              # "historyStart":datetime(2017, 7, 1)
                              # 全样本
                              # "tradeStart":datetime(2014, 1, 1),
                              # "tradeEnd":datetime(2019, 7, 31),
                              # "historyStart":datetime(2013, 7, 1)
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
            #     "envPeriod":['60m','120m'], # 2
            #     "signalPeriod":['10m','15m'], # 2
            #     "erThreshold_low": np.arange(0.4,0.56,0.1), # 2
            #     "erThreshold_high": np.arange(0.7,0.96,0.1), # 3
            #     # "stdLongTimes":[0.5,1], # 2
            #     "stdHighTimes": np.arange(1.5,3.1,0.5), # 4
            #     "erMaPeriod":[3,6],
            #     # "fastPeriod": range(8,25,4), # 5
            #     # "fast_slow": np.arange(2, 4.1, 0.5), # 5
            #     # "EmaFastPeriod": range(6, 31, 6), # 5
            #     # "EmaFast_Slow": np.arange(2, 4.1, 0.5) # 5
            #     # "atrPeriod": [9,15,21], # 3
            #     }
            # }, 
            # {"pick_freq_param": 
            #     { # 63
            #     "signalPeriod":['10m'], # 2
            #     # "fastPeriod":[10,20,30],
            #     # "fast_slow":[2,3,4],
            #     "EmaFastPeriod":[8,16,24], #3
            #     "EmaFast_Slow":[2,3,4], #3
            #     "stdLongTimes": np.arange(0.4, 1.3, 0.4), # 3
            #     "stdHighTimes": np.arange(2.5,4.1,0.5), # 4
            #     "erThreshold_low": np.arange(0.4,0.66,0.05), # 6
            #     # "erThreshold_high": np.arange(0.75,1.01,0.1), # 3
            #     # "atrPeriod": range(9,25,3), # 6
            #     }
            # }, 
            # {"pick_freq_param": 
            #     { # 175
            #     "signalPeriod":['10m'], # 
            #     "atrPeriod": [5,9,13], # 3
            #     "erMaPeriod": [3,6], # 2
            #     # "close_atrPeriod": np.arange(0.2,1,0.2), # 4
                # "stdLongTimes": np.arange(0.4, 1.3, 0.4), # 3
                # "stdHighTimes": np.arange(1.5,4,0.6), # 5
            #     # "stdShortTimes": np.arange(0, 1.1, 0.5) # 3
            #     "erThreshold_low": np.arange(0.4,0.69,0.07), # 5
            #     "erThreshold_high": np.arange(0.7,0.96,0.08), # 4
            #     }
            # }, 
            # {"pick_freq_param": 
            #     { # 36
            #     "stopLossPct": np.arange(0.005, 0.026, 0.005), # 5
            #     "stoplossPeriod" : range(1, 20, 6), # 4
            #     "expectReturn": np.arange(0.003, 0.025, 0.003), # 8
            #     "takeProfitLotRatio":[0,0.5,1] # 3
            #     }
            # }, 
            {"pick_freq_param": 
                { # 60
                "addPct": np.arange(0.003, 0.025, 0.003), # 5
                "posTime": [0,1,2], # 3
                # "addLotTime": [0.5, 1, 1.5, 2] # 4
                # "expectReturn": np.arange(0.003, 0.025, 0.003), # 8
                # "takeProfitLotRatio": [0.5, 0.8, 1] # 3
                }
            }, 
]
multiSymbolList = [
                    # 'IF:CTP',
                    'IC:CTP',
                    # 'Y:CTP',
                    # 'J:CTP'
                  ]


def main():
    path = os.path.split(os.path.realpath(__file__))[0]
    startTime = datetime.now().strftime("%m%d%H%M")
    with open(path+"//CTA_setting-IC-v3.json") as f:
        globalSetting = json.load(f)[0]

    for s in multiSymbolList:
        if s in ['IC:CTP','IH:CTP']:
            ENGINESETTING['timeRange'] = {
                              "tradeStart":datetime(2015, 8, 1),
                              "tradeEnd":datetime(2018, 7, 31),
                              "historyStart":datetime(2015, 4, 20)
                              }
        else:
            ENGINESETTING['timeRange'] = {
                              "tradeStart":datetime(2014, 1, 1),
                              "tradeEnd":datetime(2017, 12, 31),
                              "historyStart":datetime(2013, 7, 1)
                              }
        ENGINESETTING["contracts"][0]['symbol'] = s
        globalSetting['symbolList'][0] = s
        globalSetting.update(ENGINESETTING)
        optimizer = stepwiseOpt(STRATEGYCLASS, ENGINESETTING, OPT_TARGET, OPT_TASK, globalSetting, 
                                path+'/optResult/'+STRATEGYCLASS.className+startTime)
        optimizer.runMemoryParallel(cpu_counts=None) # 设置使用的CPU核数量，可通过 os.cpu_count() 查看电脑核数量

if __name__ == '__main__':
    main()