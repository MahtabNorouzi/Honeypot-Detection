#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import Queue
import threading
# from etherscan_contract_crawler import list_of_contracts
from ethereum_data_etherscan import EthereumData
import requests
import time
import sys
import ast

NR_OF_THREADS   = 5
# MONGO_HOST      = "127.0.0.1"
# MONGO_PORT      = 27017
# DATABASE        = "honeybadger"
# COLLECTION      = "contracts"
CONTRACT_FOLDER = "ethereum_contracts/"
# CONTRACT_FOLDER = "C:\Users\AR01530\Desktop\Tools\test2\HoneyBadger\honeybadger\contracts\\"

exitFlag = 0

class searchThread(threading.Thread):
    def __init__(self, threadID, queue):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.queue = queue
    def run(self):
        searchContract(self.queue)

def searchContract(queue):
    global data_source

    while not exitFlag:
        queueLock.acquire()
        if not queue.empty():
            contract = queue.get()
            queueLock.release()
            try:
                # get the bytecode of the contract by the transaction hash
                start_time = time.time()
                url = data_source.apiDomain + '?module=proxy&action=eth_getTransactionByHash&txhash=' + contract["transactionHash"] + '&apikey=VT4IW6VK7VES1Q9NYFI74YKH8U7QW9XRHN'
                end_time = time.time()
                info = requests.get(url)
                contract_info = info.json()
                result = contract_info["result"]
                if not result:
                    print("couldn't find the contract bytecode for %" % contract["transactionHash"])
                    return None
                # contract_address = result["contractAddress"]
                contract["init_bytecode"] = result["input"]
                remaining_time = 1 - (end_time - start_time)
                time.sleep(remaining_time)
            except BaseException:
                print(result)

            # file_path = CONTRACT_FOLDER+"\\"+str(contract["transactionHash"])+".bin"
            bin_file = str(contract["transactionHash"])+".bin"
            file_path = os.path.join(CONTRACT_FOLDER,bin_file)
            # Write bytecode to file
            dirname = os.path.dirname(file_path)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            # if not os.path.isfile(file_path):
            writeLock.acquire()
            file = open(file_path, "w")
            file.write(contract["init_bytecode"])
            file.close()
            writeLock.release()
        else:
            queueLock.release()

if __name__ == "__main__":

    queueLock = threading.Lock()
    writeLock = threading.Lock()

    global data_source
    data_source = EthereumData()
    contractQueue = Queue.Queue()

    # Create new threads
    threads = []
    threadID = 0
    for i in range(NR_OF_THREADS):
        thread = searchThread(threadID, contractQueue)
        thread.start()
        threads.append(thread)
        threadID += 1

    # print("Total number of smart contracts: "+str(len(list_of_contracts)))

    uniques = set()
    contracts = []
    distinct_bytecode = {}
    # distinct_deployer = {}

    with open('etherscan_dataset.log') as f:           
        for line in f:
            contract = line
            contract = ast.literal_eval(contract)
            if not contract["hash"] in uniques:
                uniques.add(contract["hash"])
                contracts.append(contract)
                distinct_bytecode[contract["hash"]] = 1
            else:
                distinct_bytecode[contract["hash"]] += 1

    print("Total number of smart contracts that are distinct: "+str(len(uniques))+" ("+str(len(contracts))+")")
    # print(str(len(distinct_bytecode)))
    # sorted_by_value = sorted(distinct_bytecode.items(), key=lambda kv: kv[1])
    # print(sorted_by_value[-1])
    # print(str(len(distinct_deployer)))
    # sorted_by_value = sorted(distinct_deployer.items(), key=lambda kv: kv[1])
    # print(sorted_by_value[-1])

    # Fill the queue with contracts
    queueLock.acquire()
    print("Filling queue with contracts...")
    for i in range(len(contracts)):
        contractQueue.put(contracts[i])
    queueLock.release()

    print("Queue contains "+str(contractQueue.qsize())+" contracts...")

    try:
    # Wait for queue to empty
        while not contractQueue.empty():
            pass

        # Notify threads it's time to exit
        exitFlag = 1

        # Wait for all threads to complete
        for t in threads:
            t.join()

        print('\nDone')
    except KeyboardInterrupt:
        exitFlag = 1
        raise
