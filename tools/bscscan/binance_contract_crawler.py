from unittest import result
import Queue
import threading
import datetime
import json
import ast
import requests
import logging
from hashlib import sha256
# import time
from time import sleep, perf_counter



exitFlag = 0
THREAD_NUM = 5


formatter = logging.Formatter('%(message)s')

def setup_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


bscscan_logger = setup_logger('bscscan_logger', 'bscscan_dataset.log')

unsuccessful_calls = setup_logger('unsuccessful_calls', 'unsuccessful_calls.log', logging.ERROR)

# def init():
#     if web3.eth.syncing == False:
#         print('Ethereum blockchain is up-to-date.')
#         print('Latest block: '+str(latestBlock.number)+' ('+datetime.datetime.fromtimestamp(int(latestBlock.timestamp)).strftime('%d-%m-%Y %H:%M:%S')+')\n')
#     else:
#         print('Ethereum blockchain is currently syncing...')
#         print('Latest block: '+str(latestBlock.number)+' ('+datetime.datetime.fromtimestamp(int(latestBlock.timestamp)).strftime('%d-%m-%Y %H:%M:%S')+')\n')

class searchThread(threading.Thread):
    def __init__(self, threadID, queue):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.queue = queue
    def run(self):
        searchContracts(self.queue)

def searchContracts(queue):
    global data_source
    global list_of_contracts

    while not exitFlag:
        queueLock.acquire()
        if not queue.empty():
            blockNumber = queue.get()
            queueLock.release()
            try:
                start_time = perf_counter()
                print('Searching block '+str(blockNumber)+' for contracts...')


                url = data_source.apiDomain + '?module=proxy&action=eth_getBlockByNumber&tag=' + str(hex(blockNumber)) + '&boolean=true&apikey=' + data_source.apikey
                info = requests.get(url)
                block = info.json()

                transactions = block["result"]["transactions"]
                end_time = perf_counter()
                remaining_time = 1 - (end_time - start_time)
                sleep(remaining_time)
                if block and transactions:
                    for transaction in transactions:
                        if transaction and not transaction["to"]:
                            print("contract found")
                            tx_hash = transaction['hash']
                            # contract_adr = data_source.getContractAddress(tx_hash)
                            init_bytecode = transaction["input"]
                            contract_hash = sha256(bytearray.fromhex(init_bytecode[2:]))

                            contract = {}
                            # contract['address'] = contract_adr.lower()
                            contract['transactionHash'] = tx_hash
                            contract['blockNumber'] = blockNumber
                            contract['hash'] = contract_hash.hexdigest()

                            if not contract in list_of_contracts:
                                list_of_contracts.append(contract)
                                bscscan_logger.info(contract)
                                # with open("dataset.txt", 'a') as r_report:
                                #     r_report.write('\n'+contract)
            except BaseException:
                unsuccessful_calls.error(blockNumber)
                # print(blockNumber, block["result"], e)

        else:
            queueLock.release()


if __name__ == "__main__":
    # init()
    queueLock = threading.Lock()
    blockQueue = Queue.Queue()

    # global data_source
    # data_source = EthereumData()

    global list_of_contracts
    list_of_contracts = []

    # Create new threads
    threads = []
    threadID = 1
    for _ in range(THREAD_NUM):
        thread = searchThread(threadID, blockQueue)
        thread.start()
        threads.append(thread)
        threadID += 1

    startBlockNumber = 45425
    endBlockNumber = max(startBlockNumber, 100976)

    # The 5 calls per sec/IP rate limit: fills the queue with 5 blocks everytime
    # Fill the queue with block numbers

    # 45425 (First block of Aug-7-2015)
	# end: 6567980
    queueLock.acquire()
    for i in range(startBlockNumber, endBlockNumber+1):
        blockQueue.put(i)
    queueLock.release()

    print('Searching for contracts within blocks '+str(startBlockNumber)+' and '+str(endBlockNumber)+'\n')

    try:
    # Wait for queue to empty
        while not blockQueue.empty():
            pass

        # Notify threads it's time to exit
        exitFlag = 1

        # for thread in threading.enumerate(): 
        #     print(thread.name)
        # Wait for all threads to complete
        for t in threads:
            t.join()

        print('\nDone')

        print("contracts found", list_of_contracts)
    except KeyboardInterrupt:
        exitFlag = 1
        raise
