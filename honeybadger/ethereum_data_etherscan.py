# this the interface to create your own data source 
# this class pings etherscan to get the latest code and balance information

import json
import re
import requests

class EthereumData:
	def __init__(self):
		self.apiDomain = "https://api.etherscan.io/api"
		self.apikey = "VT4IW6VK7VES1Q9NYFI74YKH8U7QW9XRHN"

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
		url = 'https://api.etherscan.io/api?module=account&action=txlist&address=' + address + '&tag=first&apikey=' + self.apikey
		first_tx = requests.get(url)
		if first_tx:
			results = first_tx.json()
			init_bytecode = results["result"]
		# print(init_bytecode)
		return init_bytecode[0]