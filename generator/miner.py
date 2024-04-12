from time import sleep
from config import btc, miner_p2tr


while True:
    mem = btc.call("getmempoolinfo",)
    if mem.json()["result"]["size"] > 0:
        print("New tx in mempool")
        sleep(10)
        btc.call("generatetoaddress", 1, miner_p2tr.to_string())
    sleep(1)
