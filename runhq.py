from vnpy.event import EventEngine2
from vnpy.trader.vtEvent import EVENT_LOG, EVENT_ERROR
from vnpy.trader.vtEngine import MainEngine, LogEngine
from vnpy.trader.gateway import simGateway as gateway
from vnpy.trader.app.ctaStrategy.ctaBase import EVENT_CTA_LOG
from vnpy.trader.app import ctaStrategy
from datetime import datetime
import sys
import os


os.environ["QRY_FREQ"] = "10"



def run_strategy():
    le = LogEngine()
    le.setLogLevel(le.LEVEL_INFO)
    ee = EventEngine2()
    me = MainEngine(ee)
    me.addGateway(gateway)
    me.addApp(ctaStrategy)
    # ee.register(EVENT_LOG, le.processLogEvent)
    # ee.register(EVENT_CTA_LOG, le.processLogEvent)
    me.connect(gateway.gatewayName)
    gw = me.getGateway(gateway.gatewayName)
    gw.start_date = datetime(2019, 9, 19, 9)
    # gw.end_date = datetime(2019, 9, 19, 12)
    # gw.start_date = datetime(2019, 9, 19, 12, 30)
    gw.end_date = datetime.now()
    cta = me.getApp(ctaStrategy.appName)
    cta.settingfilePath = "CTA_setting.json"
    
    cta.loadSetting()
    cta.initAll()    
    cta.startAll()


def test(path, sid):
    import os
    import importlib
    os.environ["STRATEGY_ID"]
    path = os.path.abspath(path)
    os.chdir(path)
    sys.path.append(path)
    run_strategy()


if __name__ == "__main__":
    import sys
    path = sys.argv[1]
    sid = sys.argv[2]
    test(path, sid)