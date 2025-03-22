import os
import json
import logging
import datetime
import random
import telebot
from telebot.apihelper import ApiException

TOKEN = '8182642876:AAFzCS1k985u0KQ2V0gsM6z9jYH7TkpApvE'
CHANNEL_USERNAME = "@King_1_elehteraf"

bot = telebot.TeleBot(TOKEN)

USERS_FILE = 'users.json'
REWARD_CODES_FILE = 'reward_codes.json'
IMPORTED_CODES_FILE = 'imported_codes.json'
LOG_FILE = 'log.txt'
ADMINS = ['5869877607', '6978558238']

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=LOG_FILE, filemode='a')

def init_files():
    for file in [USERS_FILE, REWARD_CODES_FILE, IMPORTED_CODES_FILE]:
        if not os.path.exists(file):
            with open(file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
init_files()
