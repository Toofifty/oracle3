# -- coding: utf-8 --
"""
Oracle 3.0 IRC Bot

log.py
"""

import os
from datetime import datetime

###################################

def _init(b):
    print '^^^ %s loaded' % __name__

def _del(b):
    print 'vvv %s unloaded' % __name__

####################################

def _log(channel, line):
    time = '[%s] ' % str(datetime.now().strftime('%d/%m %H:%M:%S'))
    with open('../data/log/%s.txt' % channel, 'a') as out:
        out.write(time + line + '\n')

def _chat(bot, args):
    user, channel, message = args
    _log(channel, '<%s> %s' % (user.nick, ' '.join(message)))

def _message(bot, args):
    user, message = args
    _log(user.nick, '<%s> %s' % (user.nick, ' '.join(message)))

def _join(bot, args):
    user, channel = args
    _log(channel, '%s joined %s' % (user.nick, channel))

def _part(bot, args):
    user, channel = args
    _log(channel, '%s parted %s' % (user.nick, channel))

def _nick(bot, args):
    user, nick = args
    _log(user.nick, '%s set nick to %s' % (user.nick, nick))

def _bot_join(bot, args):
    channel = args
    _log(channel, '%s joined %s' % (bot.config.nick, ' '.join(channel)))

def _invite(bot, args):
    user, channel = args
    _log(channel, '%s was invited to %s by %s' \
        % (bot.config.nick, channel, user.nick))

def _error(bot, args):
    error = args
    _log('_error', error)
