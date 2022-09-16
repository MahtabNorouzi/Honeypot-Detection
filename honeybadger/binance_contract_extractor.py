#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import Queue
import threading
from binance_data_bscscan import BSCData
import requests
import time
import sys
import ast

NR_OF_THREADS   = 5
CONTRACT_FOLDER = "binance_contracts/"

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
                contract["init_bytecode"] = result["input"]
                remaining_time = 1 - (end_time - start_time)
                time.sleep(remaining_time)
            except BaseException:
                print(result)

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
    data_source = BSCData()
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
