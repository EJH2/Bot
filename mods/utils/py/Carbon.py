import requests
import time
import json
import threading
import os.path
import logging

log = logging.getLogger()

if os.path.isfile("mods/utils/json/configs/CarbonConfig.json"):
	with open("mods/utils/json/configs/CarbonConfig.json") as f:
		senddata = True
else:
	senddata = False

class Carbon(threading.Thread):
	def __init__(self, key, bot, timestamp, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.key = key
		self.bot = bot
		self.timestamp = timestamp

	def run(self):
		sent = 0
		url = 'https://www.carbonitex.net/discord/data/botdata.php'
		while senddata == True:
			with open("mods/utils/json/configs/CarbonConfig.json") as f:
				carbonconfig = json.load(f)
			data = {
				'key': self.key,
				'servercount': len(self.bot.servers),
				"botname": self.bot.user.name,
				"botid": self.bot.user.id,
				"logoid": self.bot.user.avatar_url[60:].replace(".jpg",""),
				"ownerid": carbonconfig["ownerid"],
				"ownername": carbonconfig["ownername"]
			}

			try:
				self.timestamp = time.strftime('%H:%M:%S')
				r = requests.post(url, json=data)
				sent += 1
				print('{3}: Carbon Payload #{1} returned {0.status_code} {0.reason} for {2}\n '.format(r, sent, data, self.timestamp))
			except Exception as e:
				print('/!\\=================/!\\==/!\\=================/!\\\nERROR: An error occurred while fetching statistics: ' + str(e) + "\n/!\\=================/!\\==/!\\=================/!\\")
			finally:
				time.sleep(300)