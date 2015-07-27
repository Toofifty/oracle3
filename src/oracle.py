# -- coding: utf-8 --
"""
Oracle 3.0 IRC Bot

oracle.py
"""

from bot import Oracle
from optparse import OptionParser, OptionGroup

VERSION = 'v3.0'

def main():
    # Bot initialiser

    config, args = parse_options()
    bot = Oracle(config)
    bot.run()

def parse_options():
    # Parse console options using
    # OptionParser

    # Set groups
    parse = OptionParser(version='Version: %s' % VERSION)
    debug = OptionGroup(parse, 'Debug Options')
    irc = OptionGroup(parse, 'IRC Options')
    bot = OptionGroup(parse, 'Bot Options')

    debug.add_option(
        '-v', '--verbose',
        action='store_true',
        dest='verbose',
        default=False,
        help='output raw messages and debug text               '
        'default: %default'
    )

    debug.add_option(
        '-q', '--quiet',
        action='store_false',
        dest='verbose',
        help='output only the important things'
    )

    irc.add_option(
        '-c', '--channel',
        action='append',
        type='string',
        dest='channels', default=['#toofifty'],
        help='add a channel for the bot to connect to on join\n'
        'default: %default'
    )

    irc.add_option(
        '--port',
        action='store',
        type='int',
        dest='port',
        default=6667,
        help='change the port to connect to the server on      '
        'default: %default'
    )

    irc.add_option(
        '-s', '--server', '--host',
        action='store',
        type='string',
        dest='host',
        default='irc.esper.net',
        help='change the host/server to connect to             '
        'default: %default'
    )

    irc.add_option(
        '-d', '--database',
        action='store',
        type='string',
        dest='db',
        default='../data/db.db',
        help='path and filename of database                    '
        'default: %default'
    )

    bot.add_option(
        '--char',
        action='store',
        type='string',
        dest='char',
        default='.',
        help='change the character used to access bot commands\n'
        'default: %default'
    )

    bot.add_option(
        '--currency-name',
        action='store',
        type='string',
        dest='curr',
        default='points',
        help='the currency used as the point system            '
        'default: %default'
    )

    bot.add_option(
        '-l', '--loud-char',
        action='store',
        type='string',
        dest='loud_char',
        default='$',
        help='change the character used to access bot commands and'
             ' receive public responses (admin only)              '
        'default: %default'
    )

    irc.add_option(
        '-n', '--nick',
        action='store',
        type='string',
        dest='nick', default='Oracle',
        help='change the nick the bot uses                     '
        'default: %default'
    )

    irc.add_option(
        '-p', '--password',
        action='store',
        type='string',
        dest='password',
        help='change the password the bot uses to identify to '
             'nickserv with'
    )

    irc.add_option(
        '-i', '--ident',
        action='store',
        type='string',
        dest='ident',
        default='Oracle',
        help='change the ident the bot uses to connect         '
        'default: %default'
    )

    parse.add_option_group(debug)
    parse.add_option_group(irc)
    parse.add_option_group(bot)
    return parse.parse_args()

if __name__ == '__main__':
    main()
