import requests
import time
import logging
import json
import threading
import os.path

log = logging.getLogger()

if os.path.isfile("mods/utils/CarbonConfig.json"):
	with open("mods/utils/CarbonConfig.json") as f:
		carbonconfig = json.load(f)
		senddata = True
else:
	senddata = False

class Carbon(threading.Thread):
	def __init__(self, key, bot, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.key = key
		self.bot = bot

	def run(self):
		url = 'https://www.carbonitex.net/discord/data/botdata.php'
		while senddata == True:
			data = {
				'key': self.key,
				'servercount': len(self.bot.servers),
				"botname": self.bot.user.name,
				"botid": self.bot.user.id,
				"logoid": self.bot.user.avatar_url.strip("https://discordapp.com/api/users/{}/avatars/").format(self.bot.user.id).replace(".jpg",""),
				"ownerid": carbonconfig["ownerid"],
				"ownername": carbonconfig["ownername"]
			}

			try:
				resp = requests.post(url, json=data)
				log.info('Carbon statistics returned {0.status_code} for {1}'.format(resp, data))
			except Exception as e:
				log.error('An error occurred while fetching statistics: ' + str(e))
			finally:
				time.sleep(300)