from stepwiseOptClass import stepwiseOpt
import numpy as np
import json
import os
from datetime import datetime
from hlBreakStrategyCtp import hlBreakStrategy

STRATEGYCLASS = hlBreakStrategy

# 指定引擎设置
ENGINESETTING = {
                "timeRange": {
                              "tradeStart":datetime(2014, 6, 1),
                              "tradeEnd":datetime(2019, 7, 31),
                              "historyStart":datetime(2014, 1, 1)
                             },
                "contracts":[{
                              "symbol":"IF:CTP",
                              "slippage": 0.1,
                              "rate": 0.0008,
                           }],
                'dbURI': "mongodb://localhost:27017",
                "bardbName": "VnTrader_0Min_Db",
                "symbolList":["IF:CTP"]
                }


# 优化目标
OPT_TARGET = "sharpeRatio"
# np.arange(0.1,0.2,0.01)
# range(1,10,1)
# 指定优化任务
OPT_TASK = [
            #{"pick_freq_param": 
            #     {
            #     "hlEntryPeriod": range(200,401,50),
            #     "hlExitPeriod": range(60, 180, 20)
            #     }
            # }, 
            # {"pick_freq_param": 
            #     {
                  #"dsPeriod": range(50,201,20),
                  #"dsSmaPeriod": range(20,61,20),
                # "bandTime": np.arange(1, 2, 0.2)
            #     }
            # }, 
            {"pick_freq_param": 
                {
                # "hlExitPeriod": range(10,200,10),
                # "dsLmaPeriod": range(100, 301, 50),
                #"dsThreshold": np.arange(0.12, 0.21, 0.02),
                #"bandTime": np.arange(1,2,0.1)
                # "cmiPeriod":range(330,350,1),
                # "cmiThreshold":range(10,20,1)
                # "atrLevel":range(20,40,2),
                # "atrPeriod":range(40,100,20)
                # "keltnerentrywindow": range(200,401,10), 
                # "keltnerexitwindow": range(10,201,10),
                # "keltnerentrydev": np.arange(1,3.1,0.1),
                # "keltnerexitdev": np.arange(1,3,0.1),
                "fastPeriod":range(100,300,20),
                # "slowPeriod":range(100,700,50)
                
                #"holdDay":range(5,25,1)
                #"lot":range(10,30,1)
                #"expectReturn":np.arange(0.001,0.050,0.001)
                # "addPct":np.arange(0.001,0.050,0.001)
                # "posTime":[1,2,3,4,5,6,7,8,9,10]
                #"addLotTime":np.arange(0.1,3,0.1)
                #"dsPeriod": range(50,201,20),
                #"dsSmaPeriod": range(20,61,20),
                }
            }, 
            # {"pick_freq_param": 
            #     {
            #     "addPct": np.arange(0.01, 0.04, 0.01),
            #     "posTime": [1,2,3],
            #     "addLotTime": [0.5, 1, 2]
            #     }
            # }, 


            ]
# multiSymbolList = [
# #                     ['btc.usd.q:okef'],
# #                     ['eos.usd.q:okef'],
# #                     ['eth.usd.q:okef'],
# #                     ['ltc.usd.q:okef']
#                       ['AG:CTP'],
#                       ['M:CTP'],
#                       ['FU:CTP'],
#                       ['I:CTP'],
#                       ['MA:CTP'],
#                    ]


def main():
    path = os.path.split(os.path.realpath(__file__))[0]
    with open(path+"//CTA_setting.json") as f:
        globalSetting = json.load(f)[0]

    # for s in multiSymbolList:
    #     ENGINESETTING["symbolList"] = s
    globalSetting.update(ENGINESETTING)
    optimizer = stepwiseOpt(STRATEGYCLASS, ENGINESETTING, OPT_TARGET, OPT_TASK, globalSetting, '../optResult')
    optimizer.runMemoryParallel()

if __name__ == '__main__':
    main()