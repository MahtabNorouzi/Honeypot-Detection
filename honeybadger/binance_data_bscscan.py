# this the interface to create your own data source 
# this class pings etherscan to get the latest code and balance information

import json
import re
import requests
import logging
from hashlib import sha256

logging.basicConfig(filename="dataset.log",level=logging.INFO,format='%(message)s')
log = logging.getLogger(__name__)

class BSCData:
	def __init__(self):
		self.apiDomain = "https://api.bscscan.com/api"
		self.apikey = "WKR2TT211YBPU6NN1G8419R964C23F7HEK"

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


	def getContractAddress(self, transaction_hash):
		url = self.apiDomain +'?module=proxy&action=eth_getTransactionReceipt&txhash=' + transaction_hash + '&apikey=' + self.apikey
		info = requests.get(url)
		contract_info = info.json()
		result = contract_info["result"]
		if not result:
			print("couldn't find the contract information for %" % transaction_hash)
			return None
		contract_address = result["contractAddress"]
		return contract_address