import requests
import time
import json
import threading
import os.path
import logging

log = logging.getLogger()

if os.path.isfile("mods/utils/CarbonConfig.json"):
	with open("mods/utils/CarbonConfig.json") as f:
		senddata = True
else:
	senddata = False

class Carbon(threading.Thread):
	def __init__(self, key, bot, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.key = key
		self.bot = bot

	def run(self):
		sent = 0
		url = 'https://www.carbonitex.net/discord/data/botdata.php'
		while senddata == True:
			with open("mods/utils/CarbonConfig.json") as f:
				carbonconfig = json.load(f)
			data = {
				'key': self.key,
				'servercount': len(self.bot.servers),
				"botname": self.bot.user.name,
				"botid": self.bot.user.id,
				"logoid": self.bot.user.avatar_url.strip("https://discordapp.com/api/users/133718676741292033/avatars/").replace(".jpg",""),
				"ownerid": carbonconfig["ownerid"],
				"ownername": carbonconfig["ownername"]
			}

			try:
				r = requests.post(url, json=data)
				sent += 1
				log.info('Carbon Payload #{1} returned {0.status_code} {0.reason} for {2}\n'.format(r, sent, data) + '-'*20)
			except Exception as e:
				log.error('An error occurred while fetching statistics: ' + str(e))
			finally:
				time.sleep(300)