from pymongo import MongoClient
import time
import requests
import os
from datetime import datetime, time as dtime
import logging
import traceback
import pandas as pd


logging.basicConfig(
    format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s",
    level=os.environ.get("LOGGING_LEVEL", "WARNING")
)


def getIDs(filename):
    data = pd.read_excel(
        filename,
    )
    return data.set_index("Name")["StrategyId"].apply(str).to_dict()

STRATEGYID_FILE = "strategyID.xlsx"
strategy_ids = getIDs(STRATEGYID_FILE)


HEADERS = {
    "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36",
    "Content-Type": "application/json"
}

GATEWAY = os.environ.get("GATEWAY_HOST", "http://40.73.99.45:18057/api")
TOKEN = os.environ.get("TOKEN", "")
MONGODB_HOST = os.environ.get("MONGODB_HOST", "172.16.11.81")
STRATEGY = os.environ.get("STRATEGY_COL", "HENGQIN.strategy")
DOMINANTS = os.environ.get("DOMINANT_COL", "VnTrader_1Min_Db_contest.dominants")

OPEN_TIME = dtime(9)
CLOSE_TIME = dtime(15)

SYMBOL_EX = {'SR': 'CZCE', 'A': 'DCE', 'CF': 'CZCE', 'TA': 'CZCE', 'FU': 'SHFE', 'SC': 'INE', 'BU': 'SHFE', 'AG': 'SHFE', 'AL': 'SHFE', 'CU': 'SHFE', 'HC': 'SHFE', 'NI': 'SHFE', 'PB': 'SHFE', 'RB': 'SHFE', 'RU': 'SHFE', 'SN': 'SHFE', 'WR': 'SHFE', 'ZN': 'SHFE', 'T': 'CFFEX', 'TF': 'CFFEX', 'TS': 'CFFEX', 'AP': 'CZCE', 'CY': 'CZCE', 'FG': 'CZCE', 'JR': 'CZCE', 'LR': 'CZCE', 'MA': 'CZCE', 'OI': 'CZCE', 'PM': 'CZCE', 'RI': 'CZCE', 'RM': 'CZCE', 'RS': 'CZCE', 'SF': 'CZCE', 'SM': 'CZCE', 'WH': 'CZCE', 'B': 'DCE', 'BB': 'DCE', 'C': 'DCE', 'CS': 'DCE', 'FB': 'DCE', 'I': 'DCE', 'J': 'DCE', 'JM': 'DCE', 'L': 'DCE', 'ZC': 'CZCE', 'AU': 'SHFE', 'SP': 'SHFE', 'M': 'DCE', 'P': 'DCE', 'PP': 'DCE', 'V': 'DCE', 'Y': 'DCE', 'EG': 'DCE', 'JD': 'DCE', 'IC': 'CFFEX', 'IF': 'CFFEX', 'IH': 'CFFEX'}
DOMINANTS_MAP = {}


def read_table(client, name):
    db, col = name.split(".", 1)
    return list(client[db][col].find())


def read_strategy(client):
    return read_table(client, STRATEGY)


def read_dominants(client):
    return read_table(client, DOMINANTS)


def load_dominants(client):
    for doc in read_dominants(client):
        DOMINANTS_MAP[doc["symbol"]] = doc["contract"]


def makePlaceTargetRequestData(strategyID, targetPositionList, orderID):
    return {
        "msgType": "PlaceTargetPosition",
        "msgBody" : {
            "strategyId": strategyID,
            "token": TOKEN,
            "targetPositionList" : targetPositionList,
            "orderId": str(orderID),
            "orderTag": str(orderID)
            }
    }


def makeTargetPosition(doc):
    tp = []
    for symbol, hold in doc.items():
        t = {
            "volume": hold.get("long_vol", 0) - hold.get("short_vol", 0),
            "market": SYMBOL_EX[symbol],
            "symbol": DOMINANTS_MAP[symbol]
        }
        tp.append(t)
    return tp


import json


def sendRequest(payload):
    data = json.dumps(payload)
    logging.warning(f"Send payload: {data}")
    r = requests.post(
        GATEWAY,
        headers=HEADERS,
        data=data
    )
    logging.warning(f"Post response: [{r.status_code}] {r.text}")


def readCalendar():
    with open("calendar.csv") as f:
        return f.read().split("\n")


def isTradeTime():
    calendar = readCalendar()
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    if date in calendar:
        time = now.time()    
        if (OPEN_TIME <= time) and (time <= CLOSE_TIME):
            return True 
        
    return False    


def get_hq_id(name):
    author, strategy = name.split("_", 1)
    return strategy_ids.get(author, None)

    
def routing():
    client = MongoClient(MONGODB_HOST)
    load_dominants(client)
    oid = int(time.time())
    records = {}
    for strategy in read_strategy(client):
        hqid = get_hq_id(strategy["strategyId"])
        if not hqid:
            print(f"StrategyId: {strategy['strategyId']} not found.")
            continue 
        positions = records.setdefault(hqid, {})
        for symbol, pos in strategy["positions"].items():
            position = positions.setdefault(symbol, {})
            for key, value in pos.items():
                position[key] = position.get(key, 0) + value
    
    oid = int(time.time())
    for hqid, positions in records.items():
        tp = makeTargetPosition(positions)
        reqdata = makePlaceTargetRequestData(hqid, tp, oid)
        print(reqdata)
        try:
            sendRequest(reqdata)
        except:
            logging.error(f"Failed sending req: {reqdata}")
            logging.error(f"{traceback.print_exc()}")
        
        oid += 1


def main():
    if isTradeTime():
        logging.warning("isTradeTime")
        routing()
    else:
        logging.warning('NotTradeTime')


if __name__ == "__main__":
    main()