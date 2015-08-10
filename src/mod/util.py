# -- coding: utf-8 --
"""
Oracle 3.0 IRC Bot

util.py
"""

import re, traceback, time, random, socket
from errors import ArgumentError

try:
    from sympy import *
    from sympy.parsing.sympy_parser import parse_expr, eval_expr
    sympy_active = True
except:
    print '... SymPy not found; ignoring'
    sympy_active = False

###################################

def _init(b):
    print '^^^ %s loaded' % __name__
    if not b.db.table_exists('alias'):
        print '... Creating alias table'
        b.db.execute('CREATE TABLE alias(alias TEXT, command TEXT, '
            'user TEXT)', ())

def _del(b):
    print 'vvv %s unloaded' % __name__

####################################

def alias(bot, cmd):
    """!parent-command !r user
    !c add
        !d Add a personal alias command
        !a "<alias>" "<command>"
        !r user
    !c gadd
        !d Add a global alias command
        !a "<alias>" "<command>"
        !r administrator
    !c rem
        !d Remove a personal alias command
        !a "<alias>"
        !r user
    !c grem
        !d Remove a global alias command
        !a "<alias>""
        !r administrator
    !c list
        !d View all personal aliases
        !r user
    !c glist
        !d View all global aliases
        !r user
    """
    def add(bot, cmd, *args):
        message = ' '.join(cmd.args)
        if len(args) == 0:
            user = cmd.user.nick
        else:
            user = args[0]

        if not '"' in cmd.args[0] and len(cmd.args) > 1:
            alias = cmd.args[0]
            command = ' '.join(cmd.args[1:])
            if alias == command:
                cmd.output('The alias can\'t be the same as the command.')
                return
            if command[0] in (bot.config.char, bot.config.loud_char):
                # Make sure second arg is actually a command
                bot.db.execute('INSERT INTO alias VALUES(?, ?, ?)',
                                (alias, command, user))
                cmd.output('Alias "%s" : "%s" saved.' % (alias, command))
            else:
                cmd.output('Command must start with %s or %s.' % \
                    (bot.config.char, bot.config.loud_char))
        elif '"' in message:
            split = re.compile(r'"(.*?)" "(.*?)"')
            match = split.match(message)
            if match is not None:
                if match.group(2)[0] in (bot.config.char, bot.config.loud_char):
                    # Make sure second arg is actually a command
                    alias = match.group(1)
                    command = match.group(2)
                    if alias == command:
                        cmd.output('The alias can\'t be the same as the command.')
                        return
                    bot.db.execute('INSERT INTO alias VALUES(?, ?, ?)',
                                    (alias, command, user))
                    cmd.output('Alias "%s" : "%s" saved.' % (alias, command))
                else:
                    cmd.output('Command must start with %s or %s.' % \
                        (bot.config.char, bot.config.loud_char))
            else:
                cmd.output('Usage: .alias add "<alias>" "<command...>"',
                    'Or: .alias add <alias> <command...>')
        else:
            cmd.output('Usage: .alias add "<alias>" "<command...>"',
                'Or: .alias add <alias> <command...>')

    def gadd(bot, cmd):
        add(bot, cmd, 'global')

    def rem(bot, cmd, *args):
        message = ' '.join(cmd.args)
        if len(args) == 0:
            user = cmd.user.nick
        else:
            user = args[0]

        alias = ' '.join(cmd.args[0:]).replace('"', '')

        matching = bot.db.fetchall('SELECT * FROM alias WHERE alias = ? '
            'AND user = ?', (alias, user))

        if len(matching) > 0:
            bot.db.execute('DELETE FROM alias WHERE alias = ? AND user = ?',
                (alias, user))
            cmd.output('Alias removed.')
        else:
            cmd.output('No alias found.')

    def grem(bot, cmd):
        rem(bot, cmd, 'global')

    def list(bot, cmd, *args):
        if len(args) == 0:
            user = cmd.user.nick
        else:
            user = args[0]

        aliases = bot.db.fetchall('SELECT * FROM alias WHERE user = ?', (user,))
        out = []
        for alias in aliases:
            out.append('%s : %s' % (alias['alias'], alias['command']))
        if len(out) == 0:
            cmd.output('No aliases found.')
        else:
            cmd.output(*out)

    def glist(bot, cmd):
        list(bot, cmd, 'global')

    try:
        if len(cmd.args) == 0:
            raise ArgumentError()
        # Remove child command from args
        child_cmd = cmd.args[0]
        cmd.args = cmd.args[1:]
        locals()[child_cmd](bot, cmd)

    except ArgumentError:
        if cmd.user.rank > 2:
            cmd.output('Usage: .alias <add|rem|gadd|grem|list|glist>')
        else:
            cmd.output('Usage: .alias <add|rem|list|glist>')

    except Exception:
        traceback.print_exc()
        cmd.output('Sorry, something went wrong. This error has been logged.')

def calc(bot, cmd):
    """
    !d Calculate high-level maths
    !a <equation...>
    !r user
    """
    if not sympy_active:
        cmd.output('Sorry, this command is disabled.')
        return
    if len(cmd.args) > 0:
        try:
            exp = parse_expr(' '.join(cmd.args))
            try:
                cmd.output('%s: %d' % (cmd.nick, exp.evalf()))
            except:
                cmd.output('%s: %d' % (cmd.nick, exp))
        except Exception, e:
            cmd.output('Syntax error: %s' % (str(e)))
    else:
        cmd.output('Usage: .calc <equation...>')

def pick(bot, cmd):
    """
    !d Pick an option from a list (space separated)
    !a <options...>
    !r user
    """
    if len(cmd.args) < 2:
        cmd.output('Usage: .pick <options...>')
    else:
        cmd.output('%s: %s' % (cmd.nick, random.choice(cmd.args)))

def resolve(bot, cmd):
    """
    !d Resolve domain names/addresses to an IP
    !a <addresses...>
    !r user
    """
    if len(cmd.args) > 0:
        msg = []
        for addr in cmd.args:
            data = socket.gethostbyname_ex(addr)
            msg.append('%s: %s' % (addr, data[2]))
        cmd.output(*msg)
    else:
        cmd.output('Usage: .resolve <address>')

def say(bot, cmd):
    """
    !d Repeat a phrase
    !a <message...>
    !r moderator
    """
    msg = ' '.join(cmd.args)
    for match in re.findall(bot.token_pattern, msg):
        # Haha, no
        if not 'pass' in match and not 'conf' in match:
            try:
                msg = msg.replace('$%s$' % match, str(eval(match)))
            except:
                msg = 'Bad token: $%s$' % match
                break
            # Replace the string with the attribute value
    cmd.set_loud(True)
    cmd.output(msg)

def utc(bot, cmd):
    """
    !d Get the current time, utc
    !r user
    """
    cmd.output('UTC Time: %s' % str(time.asctime(time.gmtime())))

def _chat(bot, args):
    user, channel, message = args

    # Alias handling, personal and global
    p_aliases = bot.db.fetchall('SELECT * FROM alias WHERE user = ?',
        (user.nick,))
    g_aliases = bot.db.fetchall('SELECT * FROM alias WHERE user = ?',
        ('global',))

    str_msg = ' '.join(message)

    for alias in p_aliases:
        if message[0] == alias['alias']:
            str_msg = str_msg.replace(alias['alias'], alias['command'], 1)
            message = str_msg.split(' ')
            print '->> Processing command', alias['command']
            bot.chat_event(user, channel, message)
            return

    for alias in g_aliases:
        if message[0] == alias['alias']:
            str_msg = str_msg.replace(alias['alias'], alias['command'], 1)
            if '&b' in str_msg:
                index = str_msg.find('&b')
                str_msg = str_msg[:index] + str_msg[index+3:]
            message = str_msg.split(' ')
            print '->> Processing command', str_msg
            # Change flag in the plugins object to allow the next
            # command to go through no matter the user's rank
            bot.plugins.gl_alias = True
            bot.chat_event(user, channel, message)
            return

def _invite(bot, args):
    user, channel = args

    print '>>* %s has invited me to %s' % (user.nick, channel)
    bot.join_channel(channel)
