#!/usr/bin/python
# -*- coding: utf-8 -*-

# Bot di Telegram per il Subotto

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import TelegramError
import logging
import requests
import sys
import time
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import math

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

class Scores_handler:	
	def __init__(self):
		self.score = {}
		self.lastmsg = {'gol': {}, 'time': {}, 'players': {}, 'idx': {}}
		self.response = {'idx':0}
	
	def update(self):
		r = requests.post("https://uz.sns.it/24ore/score",json={'action':'get'},headers={'Content-Type':'application/json'})       
		self.score = r.json()
		self.response['gol'] = self.score['teams']['1']['name']+": "+`self.score['teams']['1']['score']`+"\n"+self.score['teams']['2']['name']+": "+`self.score['teams']['2']['score']`+"\n\nDifferenza reti: "+`self.score['goal_difference']`+"\nIndice di rimonta: "+`self.score['remount_index']`
		self.response['idx'] += 1
		self.response['time'] = "Tempo trascorso: "+hsec(self.score['elapsed_time'])+"\nTempo mancante: "+hsec(self.score['time_to_end'])
		self.response['players'] = self.score['teams']['1']['players']['1']['fname']+" "+self.score['teams']['1']['players']['1']['lname']+"\n"+self.score['teams']['1']['players']['2']['fname']+" "+self.score['teams']['1']['players']['2']['lname']+"\n\n"+self.score['teams']['2']['players']['1']['fname']+" "+self.score['teams']['2']['players']['1']['lname']+"\n"+self.score['teams']['2']['players']['2']['fname']+" "+self.score['teams']['2']['players']['2']['lname']+"\n\nIn corso da"+`self.score['turn_duration']` if self.score['teams']['2']['players'] != None else "N/D"
		
	def resp(self, cosa):
		def fun(bot, update):
			logger.info(`update.message.from_user.id`+" requested: "+cosa)
			self.lastmsg[cosa][update.message.from_user.id] = update.message.reply_text(self.response[cosa])
		return fun


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    update.message.reply_text('Salve!\nSono un Bot per la visualizzazione delle statistiche del Subotto.\nScrivi /help per l\'elenco dei comandi.')


def help(bot, update, args):
    update.message.reply_text('/all Tutte le statistiche\n/plot Il grafico dei punteggi')


def echo(bot, update):
    logger.warn(update.message.from_user.id)
    update.message.reply_text(update.message.text)


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))
    
           
def h24_all(sh):
	def sall(bot, update):
		sh.resp('time')(bot, update)
		sh.resp('gol')(bot, update)
		sh.resp('players')(bot, update)
		#sh.resp('idx')(bot, update)
	return sall
	

def h24_plot(bot, update):
	logger.info(`update.message.from_user.id`+" requested: plot")
	
	r = requests.post("https://uz.sns.it/24ore/score",json={'action':'getevents','year':'2016'},headers={'Content-Type':'application/json'})
	data = r.json()

	score = {}
	points = {}
	points['Matematici']=[]
	points['Fisici']=[]
	time_max = 0
	for team in data: 
		score[team] = 0;
		for i in range(len(data[team])):
			data[team][i] += data[team][i-1]
			time_max = time_max if (time_max > data[team][i]) else data[team][i]
	step = int(math.ceil(time_max/400))
	for time in range (0, time_max, step):
		for team in data:
			while (score[team] < len(data[team]) and data[team][score[team]] < time):
				score[team] += 1
			points[team].append(score[team])

	fig = plt.figure()
	ax = plt.subplot(111)
	plt.plot(points['Matematici'],label="Matematici")
	plt.plot(points['Fisici'],label="Fisici")
	plt.xticks([400/8*i for i in range(9)], [3*i for i in range(9)])
	plt.title('Punteggio 24ore')
	ax.legend()
 
	fig.savefig('plot.png')

	bot.sendPhoto(chat_id=update.message.chat_id,photo=open('plot.png'))
	
	
def hsec(seconds):
	sec = seconds if (seconds != None) else 0
	m, s = divmod(sec, 60)
	h, m = divmod(m, 60)
	return "%d:%02d:%02d" % (h, m, s)


def main():
    f = open("telegram_token","r")
    token = f.readline().strip()
	
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(token)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    
    sh = Scores_handler()
    sh.update()

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help,pass_args=True))
    dp.add_handler(CommandHandler("all", h24_all(sh)))
    dp.add_handler(CommandHandler("gol", sh.resp('gol')))
    dp.add_handler(CommandHandler("players", sh.resp('players')))
    dp.add_handler(CommandHandler("time", sh.resp('time')))
    dp.add_handler(CommandHandler("plot", h24_plot))
    
    dp.add_handler(CommandHandler("idx", sh.resp('idx')))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))	

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()
    
    while True:
		sh.update()
		for i in ['gol','players','time']:
			last = sh.lastmsg[i]
			for j in last:
				if (last[j].text != sh.response[i]):
					try:
						last[j].edit_text(sh.response[i])
					except TelegramError:
						logger.warn("Update text error: "+last[j].text+" --> "+sh.response[i])
		
		time.sleep(1)
    

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
    
    
def update_stats():
	global stats	
	r = requests.post("https://uz.sns.it/24ore/stats",json={'year':'all'},headers={'Content-Type':'application/json'})
	stats = r.json()


	

if __name__ == '__main__':
    main()
