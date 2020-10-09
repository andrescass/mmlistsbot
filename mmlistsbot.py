#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
A bot that allow you to query Miralos Morir movie lists
"""

import logging
import os
import random
import sys
import json
import requests
from datetime import datetime, timedelta
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode

b_key = "1306345595:AAHyodPBoZVLU_pH-ZThoxu0-aTjZv5oFwM"
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Getting mode, so we could define run function for local and Heroku setup
mode = os.getenv("MODE")
#mode = "dev"
TOKEN = os.getenv("TOKEN")
if mode == "dev":
    TOKEN = b_key
    def run(updater):
        updater.start_polling()
elif mode == "prod":
    def run(updater):
        PORT =  int(os.environ.get("PORT", "8443"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
        # Code from https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks#heroku
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TOKEN)
        updater.bot.set_webhook("https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TOKEN))
else:
    logger.error("No MODE  specified!")
    sys.exit(1)

def start(update, context):
    """Send a message when the command /start is issued."""
    start_msg = "Hola, soy un bot calorista, al que podés consultarle por las películas nombradas en cada "
    start_msg += "edición de Míralos Morir \n"
    start_msg += "Para saber como interactuar conmigo, escribí /aiuuda y obtendrás una lista de comandos."
    update.message.reply_text(start_msg)

def show_help(update, context):
    """Send a message when the command /start is issued."""
    help_msg = "Usá los siguientes comandos para comunicarte conmigo:\n"
    help_msg += "/listar_todas para ver todas las listas disponibles \n"
    help_msg += "/MM 'nro' para ver una lista en particular con sus películas, por ejemplo: /MM 15 \n"
    help_msg += "/pelicula 'palabras' buscar las películas cuyo nombre contenga las palabras indicadas, por ejemplo /pelicula pussycat kill \n"
    help_msg += "/director 'palabras' buscar las películas cuyo director contenga en su nombre las palabras indicadas, por ejemplo "
    help_msg += "/director Russ Meyer"

    update.message.reply_text(help_msg)

def list_all(update, context):
    lists_url = "http://miralosmorserver.pythonanywhere.com/api/movielists-mm"
    lists_req = requests.get(lists_url)
    lists_dict = lists_req.json()
    lists_msg = ''
    list_count = 0
    for l in lists_dict:
        list_name = l['name'].split(' - ')[0]
        if len(l['ext_link']) > 2:
            list_name_url = "<a href=\""+ l['ext_link'] +" \">" + list_name + "</a>"
        else:
            list_name_url = list_name
        current_list = '<b>' + list_name_url + '</b>' + ' (' + l['name'].split(' - ')[1] + ')\n'
        current_list += l['description'] + '\n \n'
        if (len(current_list) + len(lists_msg)) < 4096:
            lists_msg += current_list
            list_count += 1
        else:
            update.message.reply_text(lists_msg,
                  parse_mode=ParseMode.HTML,
                  disable_web_page_preview=True) 
            lists_msg = ''
            lists_msg +=  current_list
            list_count = 0
    if list_count > 0:
        update.message.reply_text(lists_msg,
                  parse_mode=ParseMode.HTML,
                  disable_web_page_preview=True)

def get_mm(update, context):
    """ Get specific list """
    try:
        # args[0] should contain the time for the timer in seconds
        lists_url = "http://miralosmorserver.pythonanywhere.com/api/movielists-mm"
        lists_req = requests.get(lists_url)
        lists_dict = lists_req.json()
        list_n = int(context.args[0])
        if list_n < 0 or list_n > len(lists_dict):
            update.message.reply_text('Poné un número válido hermano. Entre 1 y ' + str(len(lists_dict)))
            return

        # Get the list
        mm_url = "http://miralosmorserver.pythonanywhere.com/api/movieliststag/"
        mm_url += "MiralosMorir" + str(list_n)
        mm_req = requests.get(mm_url)
        mm_dict = mm_req.json()[0]

        mm_msg = '<b>' + mm_dict['name'] + '</b>' + '  ' + mm_dict['description'] + '\n'
        mm_msg += mm_dict['link'] + '\n'
        if len(mm_dict['ext_link']) > 2:
            mm_msg += "Lo podés leer <a href=\""+ mm_dict['ext_link'] +" \">" + "acá</a> \n"
         

        update.message.reply_text(text=mm_msg, 
                  parse_mode=ParseMode.HTML)
        
        #Send movies
        movie_msg = ''
        movie_count = 0
        current_movie = ''
        for movie in mm_dict['movies']:
            current_movie = '<b>' + movie['name'] + '</b> (' + movie['year'] + ') - imdb: '+ movie['imdb_id'] +'\n'
            current_movie += 'Directed by ' + movie['director'] + '\n'
            if len(movie['details']) > 0:
                current_movie += movie['details'] + '\n' + '\n'
            else:
                current_movie += '\n'
            if (len(current_movie) + len(movie_msg)) < 4096:
                movie_msg += current_movie
                movie_count += 1
            else:
                update.message.reply_text(movie_msg,
                  parse_mode=ParseMode.HTML) 
                movie_msg = ''
                movie_msg +=  current_movie
                movie_count = 0
        if movie_count > 0:
            update.message.reply_text(movie_msg,
                    parse_mode=ParseMode.HTML)



    except (IndexError, ValueError):
        update.message.reply_text('Usage: /MM <numero>')

def get_name(update, context):
    """ Get specific list """
    try:
        # args[0] should contain the time for the timer in seconds
        key_w = ''
        movies_url = "http://miralosmorserver.pythonanywhere.com/api/movie/search_name/"
        if len(context.args) < 1:
            update.message.reply_text(text='poné una palabra al menos', 
                  parse_mode=ParseMode.HTML)
            return
        for i in range(0, len(context.args)):
            movies_url += context.args[i]
            key_w += context.args[i] + ' '
            if i < len(context.args)-1:
                movies_url += '-'
        
        movies_url += '_mm'

        movie_req = requests.get(movies_url)
        movie_dict = movie_req.json()

        if len(movie_dict) == 0:
            update.message.reply_text(text="no se encontraron películas con esas palabras", 
                  parse_mode=ParseMode.HTML)
            return

        mm_msg = 'Películas cuyo nombre contiene <b>' + key_w + '</b>: \n'
        update.message.reply_text(text=mm_msg, 
                  parse_mode=ParseMode.HTML)
        
        #Send movies
        movie_msg = ''
        movie_count = 0
        current_movie = ''
        for movie in movie_dict:
            current_movie = '<b>' + movie['movie_name'] + '</b> (' + movie['movie_year'] + ')\n'
            current_movie += 'Directed by ' + movie['movie_director'] + '\n'
            if len(movie['movie_detail']) > 0:
                current_movie += movie['movie_detail'] + '\n' 
            for l in movie['movie_lists'].split(','):
                current_movie += l + '\n'

            if (len(current_movie) + len(movie_msg)) < 4096:
                movie_msg += current_movie
                movie_count += 1
            else:
                update.message.reply_text(movie_msg,
                  parse_mode=ParseMode.HTML) 
                movie_msg = ''
                movie_msg +=  current_movie
                movie_count = 0
        if movie_count > 0:
            update.message.reply_text(movie_msg,
                    parse_mode=ParseMode.HTML)



    except (IndexError, ValueError):
        update.message.reply_text('Usage: /MM <numero>')

def get_director(update, context):
    """ Get specific list """
    try:
        # args[0] should contain the time for the timer in seconds
        key_w = ''
        movies_url = "http://miralosmorserver.pythonanywhere.com/api/movie/search_director/"
        if len(context.args) < 1:
            update.message.reply_text(text='poné una palabra al menos', 
                  parse_mode=ParseMode.HTML)
            return
        for i in range(0, len(context.args)):
            movies_url += context.args[i]
            key_w += context.args[i] + ' '
            if i < len(context.args)-1:
                movies_url += '-'
        
        movies_url += '_mm'

        movie_req = requests.get(movies_url)
        movie_dict = movie_req.json()

        if len(movie_dict) == 0:
            update.message.reply_text(text="no se encontraron directores con esas palabras", 
                  parse_mode=ParseMode.HTML)
            return
                
        mm_msg = 'Películas cuyo director contiene <b>' + key_w + '</b>: \n'
        update.message.reply_text(text=mm_msg, 
                  parse_mode=ParseMode.HTML)
        
        #Send movies
        movie_msg = ''
        movie_count = 0
        current_movie = ''
        for movie in movie_dict:
            current_movie = '<b>' + movie['movie_name'] + '</b> (' + movie['movie_year'] + ')\n'
            current_movie += 'Directed by ' + movie['movie_director'] + '\n'
            if len(movie['movie_detail']) > 0:
                current_movie += movie['movie_detail'] + '\n' 
            for l in movie['movie_lists'].split(','):
                current_movie += l + '\n'

            if (len(current_movie) + len(movie_msg)) < 4096:
                movie_msg += current_movie
                movie_count += 1
            else:
                update.message.reply_text(movie_msg,
                  parse_mode=ParseMode.HTML) 
                movie_msg = ''
                movie_msg +=  current_movie
                movie_count = 0
        if movie_count > 0:
            update.message.reply_text(movie_msg,
                    parse_mode=ParseMode.HTML)



    except (IndexError, ValueError):
        update.message.reply_text('Usage: /MM <numero>')

def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("aiuuda", show_help))
    dp.add_handler(CommandHandler("help", show_help))
    dp.add_handler(CommandHandler("listar_todas", list_all))
    dp.add_handler(CommandHandler("MM", get_mm,
                                  pass_args=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("pelicula", get_name,
                                  pass_args=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("director", get_director,
                                  pass_args=True,
                                  pass_chat_data=True))

    # Start the Bot
    run(updater)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()