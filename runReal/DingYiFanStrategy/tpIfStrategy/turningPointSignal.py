import talib as ta
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import SGDClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier


"""
将策略需要用到的信号生成器抽离出来
"""

class tpSignal():

    def __init__(self):
        self.author = 'Right.Ding'

    def trendDirection(self,am,paraDict):
        out_pos = [0,None]
        profit_r = paraDict["profit_r"]
        loss_r = paraDict["loss_r"]
        ma_period = paraDict["ma_period"]
        dif_r1 = paraDict["dif_r1"]
        dif_r2 = paraDict["dif_r2"]
        envMa = ta.MA(am.close, ma_period)
        spread = am.close - envMa
        # spread = am.close / envMa - 1
        # spMa = ta.MA(spread, sp_period)
        
        # longMa = ta.MA(am.close, 10)

        sp_length = paraDict["sp_length"]
        if spread[-1] < 0 and spread[-2] > 0:
            # spMax为前一个价均差
            spMax = spread[-2]
            # clMax为前一个收盘价
            clMax = am.close[-2]
            upflag = True
            # 遍历搜前面的价均差是否有负的，有就把upflag设成False
            for i in range(3, sp_length+2):
                if spread[-i] < 0:
                    upflag = False
                    break
                # 如果-i的价均差大与前一个Bar的价均差，就替换价均差
                if spread[-i] > spMax:
                    spMax = spread[-i]
                # 如果-i的收盘价大与前一个Bar的收盘价，就替换收盘价                
                if am.close[-i] > clMax:
                    clMax = am.close[-i]

            if upflag:
            # if upflag and longMa[-1] > envMa[-1]:
                count = sp_length
                while spread[-count-2] > 0:
                    if am.close[-count-2] > clMax:
                        clMax = am.close[-count-2]
                    count += 1
                tpos = count + 2
                while not(am.close[-tpos] < am.close[-tpos-1] and am.close[-tpos] < am.close[-tpos+1]):
                    tpos += 1
                clMin = am.close[-tpos]

                if spread[-1] + dif_r1 * spMax > 0:
                    clMin = am.close[-1] - loss_r * (am.close[-1] - clMin)
                    out_pos = [1, clMin, am.close[-1], profit_r * (clMax - clMin), True, count]
                elif spread[-1] + dif_r2 * spMax < 0:
                    clMax = am.close[-1] + loss_r * (clMax - am.close[-1])
                    out_pos = [-1, clMax, am.close[-1], profit_r * (clMax - clMin), True, count]
        
        elif spread[-1] > 0 and spread[-2] < 0:
            spMax = spread[-2]
            clMin = am.close[-2]
            downflag = True
            for i in range(3, sp_length+2):
                if spread[-i] > 0:
                    downflag = False
                    break

                if spread[-i] < spMax:
                    spMax = spread[-i]
                if am.close[-i] < clMin:
                    clMin = am.close[-i]
            
            if downflag:
            # if downflag and envMa[-1] < longMa[-1]:
                count = sp_length
                while spread[-count-2] < 0:
                    if am.close[-count-2] < clMin:
                        clMin = am.close[-count-2]
                    count += 1
                tpos = count + 2
                while not(am.close[-tpos] > am.close[-tpos-1] and am.close[-tpos] > am.close[-tpos+1]):
                    tpos += 1
                clMax = am.close[-tpos]

                if spread[-1] + dif_r1 * spMax < 0:
                    clMax = am.close[-1] + loss_r * (clMax - am.close[-1])
                    out_pos = [-1, clMax, am.close[-1], profit_r * (clMax - clMin), True, count]
                elif spread[-1] + dif_r2 * spMax > 0:
                    clMin = am.close[-1] - loss_r * (am.close[-1] - clMin)
                    out_pos = [1, clMin, am.close[-1], profit_r * (clMax - clMin), True, count]

        return out_pos, envMa
    