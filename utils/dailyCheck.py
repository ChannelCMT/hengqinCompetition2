from datetime import datetime, time as dtime, timedelta
from pymongo import MongoClient, collection
import os
import pandas as pd
import numpy as np


MONGODB_HOST = os.environ.get("MONGODB_HOST", "172.16.11.81")
STRATEGY = os.environ.get("STRATEGY_COL", "HENGQIN.strategy")

def readCalendar():
    with open("calendar.csv") as f:
        return f.read().split("\n")

OPEN_TIME = dtime(9)
CLOSE_TIME = dtime(15)


def expectedTime():
    calendar = np.array(readCalendar()[:-1])
    now = datetime.now()
    i = calendar.searchsorted(now.strftime("%Y-%m-%d"), side="right") - 1
    date = calendar[i]
    endDt = datetime.strptime(date, "%Y-%m-%d").replace(hour=16)
    return min([now, endDt])


def isTradeTime():
    calendar = readCalendar()
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    if date in calendar:
        time = now.time()    
        if (OPEN_TIME <= time) and (time <= CLOSE_TIME):
            return True 
        
    return False    


def loadStrategy(col: collection.Collection):
    records = list(col.find({"strategyId": {"$exists": 1}}, projection={"strategyId": 1, "_id": 0}))
    return [record["strategyId"] for record in records]



def findLatestRecords(col: collection.Collection, *strategyIds):
    records = []
    for sid in strategyIds:
        doc = col.find_one({"strategyId": sid}, sort=[("datetime", -1)])
        doc.pop('_id')
        if doc:
            records.append(doc)

    return pd.DataFrame(records).set_index("strategyId")


def test():
    client = MongoClient(MONGODB_HOST)
    col = client["HENGQIN"]["strategy"]
    names = loadStrategy(col)
    result = findLatestRecords(client["HENGQIN"]["account"], *names)
    
    print("all", "-"* 100)
    print(result.sort_values("datetime", ascending=False))
    print("timeout", "-"* 100)
    timeouts = result[datetime.now() - result["datetime"] > timedelta(minutes=5)]
    if len(timeouts):
        print(timeouts)
    else:
        print("No timeout strategy")


if __name__ == "__main__":
    test()