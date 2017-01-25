#!/usr/bin/python
# -*- coding: utf-8 -*-

# Bot di Telegram per il Subotto

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, Job
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
		r = requests.post("https://uz.sns.it/24oretest/score",json={'action':'get'},headers={'Content-Type':'application/json'})       
		if r.status_code == 200:
			self.score = r.json()
			self.response['gol'] = self.score['teams']['1']['name']+": "+`self.score['teams']['1']['score']`+"\n"+self.score['teams']['2']['name']+": "+`self.score['teams']['2']['score']`+"\n\nDifferenza reti: "+`self.score['goal_difference']`+"\nIndice di rimonta: "+("{0:.2f}".format(self.score['remount_index']) if self.score['remount_index'] != "Infinity" else "Infinito")
			self.response['idx'] += 1
			self.response['time'] = "Tempo trascorso: "+hsec(self.score['elapsed_time'])+"\nTempo mancante: "+hsec(self.score['time_to_end'])
			self.response['players'] = self.score['teams']['1']['players'][0]['fname']+" "+self.score['teams']['1']['players'][0]['lname']+"\n"+self.score['teams']['1']['players'][1]['fname']+" "+self.score['teams']['1']['players'][1]['lname']+"\n\n"+self.score['teams']['2']['players'][0]['fname']+" "+self.score['teams']['2']['players'][0]['lname']+"\n"+self.score['teams']['2']['players'][1]['fname']+" "+self.score['teams']['2']['players'][1]['lname']+"\n\nIn corso da "+hsec(self.score['turn_duration']) if self.score['teams']['2']['players'] != None else "N/D"
		
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
	

def get_plot_data(year,last=0):
         r = requests.post("https://uz.sns.it/24oretest/score",json={'action':'getevents','year':`year`},headers={'Content-Type':'application/json'})
         if (r.status_code != 200):
                 return None
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
         if last != 0:
		time_max = last
         step = int(math.ceil(time_max/400))
         for time in range (0, time_max, step):
                 for team in data:
                         while (score[team] < len(data[team]) and data[team][score[team]] < time):
                                 score[team] += 1
                         points[team].append(score[team])
         points['time'] = time_max
         return points


def h24_plot(bot, update):
	logger.info(`update.message.from_user.id`+" requested: plot")

	new = get_plot_data(2017)
	old = get_plot_data(2016,new['time'])

	fig = plt.figure()
	ax = plt.subplot(111)
	plt.plot(new['Matematici'],label="Matematici",color="r",linestyle="-")
	plt.plot(new['Fisici'],label="Fisici",color="b",linestyle="-")
	plt.plot(old['Matematici'],label="Matematici (old)",color="r",linestyle="--")
	plt.plot(old['Fisici'],label="Fisici (old)",color="b",linestyle="--")
	plt.xticks([400/8*i for i in range(9)], [hsec(3*i*new['time']/(24),True) for i in range(9)])
	plt.title('Punteggio 24ore')
	ax.legend()
 
	fig.savefig('plot.png')

	bot.sendPhoto(chat_id=update.message.chat_id,photo=open('plot.png'))
	
	
def hsec(seconds,nosec=False):
	sec = seconds if (seconds != None) else 0
	m, s = divmod(sec, 60)
	h, m = divmod(m, 60)
	if nosec:
		return "%d:%02d" % (h, m)
	else:
		return "%d:%02d:%02d" % (h, m, s)

def send_updates(sh):
	def myjob(bot, job):	
		sh.update()
		for i in ['gol','players','time']:
			last = sh.lastmsg[i]
			resp = sh.response[i]
			for j in last:
				if (last[j].text != resp):
					try:
						last[j].edit_text(resp)
					except TelegramError as e:
						e = None #logger.warn(e)
	return myjob



def main():
    f = open("telegram_token","r")
    token = f.readline().strip()
	
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(token)
    j = updater.job_queue

    sh = Scores_handler()
    sh.update()

    job_minute = Job(send_updates(sh), 1.0)
    j.put(job_minute, next_t=0.0)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

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
    #dp.add_handler(MessageHandler(Filters.text, echo))	

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()



def update_stats():
	global stats
	r = requests.post("https://uz.sns.it/24ore/stats",json={'year':'all'},headers={'Content-Type':'application/json'})
	stats = r.json()


	

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print 'Interrupted'
        sys.exit(0)

