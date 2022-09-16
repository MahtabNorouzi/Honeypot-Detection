# this the interface to create your own data source 
# this class pings etherscan to get the latest code and balance information

import json
import re
import requests
import logging
from hashlib import sha256

formatter = logging.Formatter('%(message)s')


def setup_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


logger = setup_logger('first_logger', 'dataset.log')

class EthereumData:
	def __init__(self):
		self.apiDomain = "https://api.etherscan.io/api"
		# self.apikey = "VT4IW6VK7VES1Q9NYFI74YKH8U7QW9XRHN"
		# self.apikey = "YQJDMZ7TZXTYPD6NCWUH6R2AEQBEXEETQA"
		# self.apikey = "R4MGAUJP2YXZUJHKFUSHBYY499KWXINXCT"
		self.apikey = "I23V6H6P492B593X3PXAHW2IM7MRRSKPZV"

	def getBalance(self, address):
		apiEndPoint = self.apiDomain + "?module=account&action=balance&address=" + address + "&tag=latest&apikey=" + self.apikey
		r = requests.get(apiEndPoint)
		result = json.loads(r.text)
		status = result['message']
		if status == "OK":
			return result['result'] 
		return -1

	def getCode(self, address):
		# apiEndPoint = self.apiDomain + "" + address + "&tag=latest&apikey=" + apikey
		# no direct endpoint for this
		r = requests.get("https://etherscan.io/address/" + address + "#code")
		html = r.text
		code = re.findall("<div id='verifiedbytecode2'>(\w*)<\/div>", html)[0]
		return code

	def get_the_first_transaction_data(self, address):
		url = self.apiDomain + '?module=account&action=txlist&address=' + address + '&tag=first&apikey=' + self.apikey
		first_tx = requests.get(url)
		if first_tx:
			results = first_tx.json()
			init_bytecode = results["result"]
		return init_bytecode[0]


	# TODO: Move this to a class and change self.getAllContracts() to sth better :D
	def getAllContracts(self, start_block, end_block):
		# 45425 (First block of Aug-7-2015)

		# end: 6567980
		for r in range(start_block, end_block):
			url = self.apiDomain + '?module=proxy&action=eth_getBlockByNumber&tag=' + str(hex(r)) + '&boolean=true&apikey=' + self.apikey
			info = requests.get(url)
			if info.status_code != 200:
				print("again")
				self.getAllContracts(r, end_block)
				return True
			print(info, r)
			block_info = info.json()
			if block_info["result"] is None:
				print("Couldn't find the block")
				continue
			if block_info["result"]["transactions"]:
				block_transactions = block_info["result"]["transactions"]
				for i in range(0, len(block_transactions)):
					if not block_transactions[i]["to"]:
						print("contract found")
						tx_hash = block_transactions[i]["hash"]
						contract_adr = self.getContractAddress(tx_hash)
						init_bytecode = block_transactions[i]["input"]
						contract_hash = sha256(bytearray.fromhex(init_bytecode[2:]))
						# contract = Contract(contract_hash, contract_adr)
						# contracts.append(contract)
						logger.info("Block Number:" + str(r))
						logger.info("Contract Address:" + contract_adr)
						logger.info("Contract Hash:" + contract_hash.hexdigest())
						logger.info("---------------------------------------------------------------")

						# contract_bytecode.append(block_transactions[i]["input"])
		# return contract_bytecode


	def getContractAddress(self, transaction_hash):
		try:
			url = self.apiDomain + '?module=proxy&action=eth_getTransactionReceipt&txhash=' + transaction_hash + '&apikey=' + self.apikey
			info = requests.get(url)
			contract_info = info.json()
			result = contract_info["result"]
			if not result:
				print("couldn't find the contract information for %" % transaction_hash)
				return None
			contract_address = result["contractAddress"]
			return contract_address
		except BaseException:
			print(result)