from unittest import result
import Queue
import threading
import requests
import logging
from hashlib import sha256
import time
from binance_data_bscscan import BSCData


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


bscscan_logger = setup_logger('bscscan_logger', 'binance_dataset.log')

unsuccessful_bsc_calls = setup_logger('unsuccessful_bsc_calls', 'unsuccessful_bsc_calls.log', logging.ERROR)

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
                print('Searching block '+str(blockNumber)+' for contracts...')
                start_time = time.time()
                url = data_source.apiDomain + '?module=proxy&action=eth_getBlockByNumber&tag=' + str(hex(blockNumber)) + '&boolean=true&apikey=' + data_source.apikey
                end_time = time.time()
                info = requests.get(url)
                block = info.json()
                transactions = block["result"]["transactions"]
                if block and transactions:
                    for transaction in transactions:
                        if transaction and not transaction["to"]:
                            print("contract found")
                            tx_hash = transaction['hash']
                            init_bytecode = transaction["input"]
                            contract_hash = sha256(bytearray.fromhex(init_bytecode[2:]))

                            contract = {}
                            contract['transactionHash'] = tx_hash
                            contract['blockNumber'] = blockNumber
                            contract['hash'] = contract_hash.hexdigest()

                            if not contract in list_of_contracts:
                                list_of_contracts.append(contract)
                                bscscan_logger.info(contract)
                                # with open("dataset.txt", 'a') as r_report:
                                #     r_report.write('\n'+contract)
                remaining_time = 1 - (end_time - start_time)
                time.sleep(remaining_time)
            except BaseException:
                unsuccessful_bsc_calls.error(blockNumber)
                # print(blockNumber, block["result"], e)

        else:
            queueLock.release()


if __name__ == "__main__":
    # init()
    queueLock = threading.Lock()
    blockQueue = Queue.Queue()

    global list_of_contracts
    list_of_contracts = []

    global data_source
    data_source = BSCData()

    # Create new threads
    threads = []
    threadID = 1
    for _ in range(THREAD_NUM):
        thread = searchThread(threadID, blockQueue)
        thread.start()
        threads.append(thread)
        threadID += 1

    startBlockNumber = 21384380
    endBlockNumber = max(startBlockNumber, 21384390)

    # Fill the queue with block numbers

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

    except KeyboardInterrupt:
        exitFlag = 1
        raise
