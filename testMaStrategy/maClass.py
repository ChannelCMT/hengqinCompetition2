import talib as ta
import numpy as np
import pandas as pd

"""
将kdj策略需要用到的信号生成器抽离出来
"""

class maSignal():

    def __init__(self):
        self.author = 'channel'

    def maSignal(self, am, paraDict):
        maPeriod = paraDict['maPeriod']

        ma = ta.MA(am.close, maPeriod)
        return ma
        