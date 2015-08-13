# -- coding: utf-8 --
"""
Oracle 3.0 IRC Bot

bot.py
"""

import sqlite3, re
from irc import IRC
from user import User
from plugin import PluginLoader

class Oracle(IRC):
    # Main bot class
    # Decode messages and throw events

    def __init__(self, config):
        IRC.__init__(self, config.ident, config.channels, config.host,
            config.port, config.nick, config.password or None)

        self.set_verbose(config.verbose)

        self.token_pattern = re.compile(r'\$([\w\.]*)\$')

        self.config = config
        self.db = Database(config.db)

        if not self.db.table_exists('users'):
            print '... Creating users table'
            self.db.execute('CREATE TABLE users(vhost TEXT, nick TEXT, '
                'rank INT, points INT, cmd_count INT, seen INT)', ())

        self.auth = False

        # Ranks are accessible anytime using the bot
        # instance object
        self.ranks = {
            'hidden': -1,
            'banned': 0,
            'user': 1,
            'moderator': 2,
            'administrator': 3,
            'developer': 4
        }

        # Load plugins last so they have access to the
        # above attributes
        self.plugins = PluginLoader(self)

        # List of users to avoid re-instantiation for every message
        self.users = []

        # Connect last, plugins may need to do something
        # before connecting to the IRC server
        self.connect()


    def _send(self, message):
        # Replace tokens with specific bot/config variables
        # before sending the message to the server

        for match in re.findall(self.token_pattern, message):
            # Haha, no
            if not 'pass' in match and not 'conf' in match:

                # Check if the bot or config has the attribute found
                # Coninue if not found
                if hasattr(self, match):
                    obj = self

                elif hasattr(self.config, match):
                    obj = self.config

                else:
                    continue

                # Replace the string with the attribute value
                message = message.replace('$%s$' % match,
                    str(getattr(obj, match)))

        return super(Oracle, self)._send(message)


    def process(self, raw):
        # Process a raw message from the server
        #   PRIVMSG
        #   PING
        #   JOIN
        #   MODE
        #   PART
        #   NICK
        #   End of MOTD
        #   NickServ auth
        #   NAMES response
        #   WHOIS repsonse
        #   JOIN (bot)
        # Message comes in as a list of strings

        if self.verbose:
            print '--> %s' % ' '.join(raw)

        # Reply to ping event from server
        if 'PING' in raw[0]:
            self.ping(''.join(raw[1:]))
            return

        # End of MOTD
        # Join channels here
        if '376' in raw[1] and self.nick in raw[2]:
            if self.verbose:
                print '... Joining channels'
                self.join_channels(self.channels)

        # NickServ asking for auth
        # Don't need to auth if we have already, or there is no password
        if 'NickServ!' in raw[0] and 'NOTICE' in raw[1] and not self.auth \
                and self.password is not None:
            self.privmsg('NickServ', 'identify %s %s' \
                % (self.nick, self.password))
            self.auth = True
            return

        # NAMES response
        if '353' in raw[1]:
            return

        # End of NAMES
        if '366' in raw[1]:
            return

        # Bot join
        if ':%s!' % self.nick in raw[0] and 'JOIN' in raw[1]:
            # Send a _bot_join event with args: channel
            self.plugins.event(self, 'bot_join', (raw[2][1:],))
            return

        # MODE changes
        if 'MODE' in raw[1]:
            return

        # MOTD messages
        if '372' in raw[1]:
            return

        # WHOIS response
        # %ident% %vhost% * :%desc%
        if '311' in raw[1]:
            # Send a _whois_311 event with args: nick, ident, vhost
            self.plugins.event(self, 'whois_311', (raw[3], raw[4], raw[5]))
            return

        # WHOIS response
        # :%channels[...]%
        if '319' in raw[1]:
            raw[4] = raw[4].replace(':', '', 1)
            # Send a _whois_319 event with args: nick, channels
            self.plugins.event(self, 'whois_319', (raw[3], raw[4:]))
            return

        # WHOIS response
        # %user% :is logged in as
        if '330' in raw[1]:
            # Send a _whois_330 event with args: nick, nick (logged in as)
            self.plugins.event(self, 'whois_330', (raw[3], raw[4]))
            return

        # WHOIS response
        # :is a registered nick
        if '307' in raw[1]:
            # Send a _whois_307 event with args: nick
            self.plugins.event(self, 'whois_307', (raw[3],))
            return

        # '!' is the split character between a nick and vhost
        # if there is no '!' then there must be no user
        # Also, we should ignore service bots
        if not '!' in raw[0] or 'services' in raw[0]:
            return

        # User messages #

        # Create a new user object from vhost string
        user = self.create_user(raw[0])
        user.was_seen()

        if 'INVITE' in raw[1]:
            # Send an _invite event with args: user, channel
            self.plugins.event(self, 'invite', (user, raw[3][1:]))
            return

        if 'PART' in raw[1]:
            # Send a _part event with args: user, channel
            self.plugins.event(self, 'part', (user, raw[2][1:]))
            return

        if 'JOIN' in raw[1]:
            # Send a _join event with args: user, channel
            self.plugins.event(self, 'join', (user, raw[2][1:]))
            return

        if 'NICK' in raw[1]:
            # Send a _nick event with args: old_nick, new_nick
            self.plugins.event(self, 'nick', (user, raw[2]))
            user.set_nick(raw[2])
            return

        if 'PRIVMSG' in raw[1]:
            raw[3] = raw[3][1:]
            # Pass message to chat processor
            self.chat_event(user, raw[2], raw[3:])
            return

        # Message hasn't been caught anywhere else
        print '-X> Unhandled server message: %s' % raw[1]
        return


    def chat_event(self, user, channel, message):
        # Chat event called by PRIVMSG
        # Check to see whether the message was a command
        # and sends it to the command processor

        # Call this to parse commands

        # Process multi commands
        if ' ; ' in ' '.join(message):
            print '!!! Found multi-command'
            sep_messages = ' '.join(message).split(' ; ')
            for message in sep_messages:
                self.chat_event(user, channel, message.split(' '))
            return

        if '#' in channel:
            # Was an actual IRC channel
            # Send a _chat event with args: user, channel, message
            self.plugins.event(self, 'chat', (user, channel, message))
        else:
            # Was a PRIVMSG from a user
            # Send a _privmsg event with args: user, message
            self.plugins.event(self, 'privmsg', (user, message))

        for char in (self.config.char, self.config.loud_char):
            if message[0].startswith(char):
                # Create new command object
                cmd = Command(self, user, channel, message)
                cmd.set_command(message[0].replace(char, ''))
                if char == self.config.loud_char and user.rank > 1:
                    cmd.set_loud(True)

                # Send a _command event with args: cmd (object)
                self.plugins.event(self, 'command', (cmd,))
                # Pass new command to plugins.py
                self.plugins.process_command(self, cmd)
                return


    def create_user(self, vhost):
        # Gets a user from their vhost address, will
        # make a new user if no record is found
        nick = vhost.split('!', 1)[0].replace(':', '', 1)
        vhost = vhost.split('@', 1)[1]

        user = self.get_user(vhost)

        if user is None:
            # Add user to database, and create a new user object
            self.db.execute('INSERT INTO users VALUES(?, ?, ?, ?, ?, ?)',
                            (vhost, nick, 1, 0, 0, 0))
            user = self.get_user(vhost)

        # The nick might've changed, so we'll make sure it's
        # updated on each chat message
        user.set_nick(nick)

        return user


    def get_user(self, nick_vhost):
        # Gets a user from their nick OR vhost, returns None
        # if no user found in the database

        # Try the list of users first, avoid unneccessary instantiation
        for user in self.users:
            if user.nick == nick_vhost or user.vhost == nick_vhost:
                return user

        # Try to find with nick, not case dependent
        rec = self.db.fetchone('SELECT * FROM users WHERE nick = ? '
            'COLLATE NOCASE', (nick_vhost,))

        if rec is None:
            # Try to find with vhost, not case dependent
            rec = self.db.fetchone('SELECT * FROM users WHERE vhost = ? '
                'COLLATE NOCASE', (nick_vhost,))

            if rec is None:
                # Failed to find either the vhost or nick
                return None

        # Construct a user object from the record and return it
        return User(self, rec['vhost'], rec['nick'], rec['rank'], rec['points'],
                    rec['cmd_count'], rec['seen'])


    def stop(self):
        # Sends a _stop event with no args, before calling
        # stop() on the super class
        self.plugins.event(self, 'stop', ())
        super(Oracle, self).stop()


class Command(object):
    # Input command class
    # Bundles input command info, for quick use
    # in other places

    def __init__(self, bot, user, channel, message):
        self.bot = bot
        self.nick = user.nick
        self.user = user
        self.channel = channel
        self.command = message[0]
        self.args = message[1:]
        self.loud = False

    def __str__(self):
        # Easy and sensical way to get the command from
        # a command object, str(cmd) rather than cmd.command
        return self.command

    def output(self, *message):
        # Will work with multiple messages
        # Users can no longer directly broadcast replies
        if self.loud:
            self.bot.privmsg(self.channel, *message)
        else:
            self.bot.notice(self.nick, *message)

    def set_loud(self, loud):
        self.loud = loud

    def set_command(self, command):
        self.command = command

    def set_user(self, user):
        self.user = user

class Database(object):
    # Convenience class for database interaction
    # Provides some helpful methods so direct use of
    # the connection or cursor isn't necessary

    def __init__(self, database):
        # Connect to the specified database, set the row_factory
        # and get the cursor
        self.con = sqlite3.connect(database)
        self.con.row_factory = sqlite3.Row
        self.cur = self.con.cursor()

    def table_exists(self, table):
        # Check if a table exists in the database
        with self.con:
            self.cur.execute('SELECT name FROM sqlite_master WHERE '
                'type=\'table\' AND name = ?', (table,))
            return len(self.cur.fetchall()) > 0

    def execute(self, sql_txt, sql_tuple):
        # Execute a single action
        # Should be used for updating records
        with self.con:
            self.cur.execute(sql_txt, sql_tuple)

    def fetchall(self, sql_txt, sql_tuple):
        # Fetch all results from a query
        with self.con:
            self.cur.execute(sql_txt, sql_tuple)
            return self.cur.fetchall()

    def fetchone(self, sql_txt, sql_tuple):
        # Fetch one result from a query
        with self.con:
            self.cur.execute(sql_txt, sql_tuple)
            return self.cur.fetchone()
