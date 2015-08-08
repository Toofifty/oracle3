# -- coding: utf-8 --
"""
Oracle 3.0 IRC Bot

admin.py
"""

from errors import ArgumentError
import os, random, sys, traceback

###################################

def _init(b):
    print '^^^ %s loaded' % __name__

def _del(b):
    print 'vvv %s unloaded' % __name__

####################################

def error(bot, cmd):
    """
    !d Report an error
    !a <error report...>
    !r user
    """
    bot.plugin.event(bot,
        'error', 'User report by %s: %s' % (cmd.user.nick, ' '.join(cmd.args)))

def exe(bot, cmd):
    """
    !d VERY DANGEROUS - Execute Python code and print to IRC
    !a <code...>
    !r developer
    """
    try:
        exec ' '.join(cmd.args)
    except Exception, e:
        bot.output(e)

def fakejoin(bot, cmd):
    """
    !d Fake a user join event
    !a [nick]
    !r developer
    """
    if len(cmd.args) > 0:
        nick = cmd.args[0]
    else:
        nick = cmd.user.nick
    # Send _join event with args: user, channel
    bot.plugins.event(bot, 'join', (cmd.user, cmd.channel))
    cmd.output('Faked user join for %s.' % nick)

def fakepart(bot, cmd):
    """
    !d Fake a user part event
    !a [nick]
    !r developer
    """
    if len(cmd.args) > 0:
        nick = cmd.args[0]
    else:
        nick = cmd.user.nick
    # Send _part event with args: user, channel
    bot.plugins.event(bot, 'part', (cmd.user, cmd.channel))
    cmd.output('Faked user part for %s.' % nick)

def ignore(bot, cmd):
    """
    !d Set a user to rank 0
    !a <nick>
    !r moderator
    """
    if len(cmd.args) > 0:
        user = bot.get_user(cmd.args[0])
        if user is not None:
            user.set_rank(0)
            cmd.output('Ignored %s.' % user.nick)
        else:
            cmd.output('User %s not found.' % cmd.args[0])
    else:
        cmd.output('Usage: .ignore <user>')


def makeadmin(bot, cmd):
    """
    !d Fallback command to make Toofifty admin
    !r hidden
    """
    if cmd.user.vhost == 'user/Toofifty':
        cmd.user.set_rank(3)
        cmd.output('Toofifty set to administrator')

def rank(bot, cmd):
    """!parent-command !r administrator
    !c get
        !d Return a user's (or own) rank
        !a [nick]
        !r administrator
    !c set
        !d Set a user's rank
        !a <nick> <rank>
        !r administrator
    """
    def get(bot, cmd):
        if len(cmd.args) == 0:
            # No nick provided, default to the self
            cmd.output('%s: %s' % (cmd.user.nick, cmd.user.get_rank()))
        else:
            # Get user from nick
            user = bot.get_user(cmd.args[0])
            if user is not None:
                # Return rank if user exists
                cmd.output('%s: %s' % (user.nick, user.get_rank()))
            else:
                cmd.output('User %s not found.' % cmd.args[0])

    def set(bot, cmd):
        if len(cmd.args) is not 2:
            cmd.output('Usage: .rank set <nick> <rank>')
        else:
            # Get user from nick
            user = bot.get_user(cmd.args[0])
            if user is not None:
                # If use exists
                if user.set_rank(cmd.args[1]):
                    cmd.output('%s set to %s' % (user.nick, user.get_rank()))
                else:
                    # Rank was invalid and not found in bot.ranks
                    cmd.output('Invalid rank. Use 0-4 or banned|user|moderator'
                        '|administrator|developer')
            else:
                cmd.output('User: %s not found.' % cmd.args[0])

    # Child command processor
    try:
        if len(cmd.args) == 0:
            # No child command given
            raise ArgumentError()

        # Remove child command from args
        child_cmd = cmd.args[0]
        cmd.args = cmd.args[1:]
        # Run child command as a closure
        locals()[child_cmd](bot, cmd)

    except ArgumentError:
        # Default to .rank get [nick]
        # So .rank will return own rank
        locals()['get'](bot, cmd)

    except Exception, e:
        traceback.print_exc()
        cmd.output('Sorry, something went wrong. This error has been logged.')
        # Log error
        bot.plugin.event(bot, 'error', e)

def raw(bot, cmd):
    """
    !d Send a raw message to the IRC server
    !r developer
    """
    bot._send(' '.join(cmd.args))

def reload(bot, cmd):
    """
    !d Reload modules
    !a [modules...]
    !r developer
    """
    if len(cmd.args) == 0:
        for mod in bot.plugins.mods:
            bot.plugins.reload_mod(mod, bot, cmd)
    else:
        for mod_n in cmd.args:
            mod = bot.plugins.get_mod(mod_n)
            if mod is not None:
                bot.plugins.reload_mod(mod, bot, cmd)
            else:
                cmd.output('%s is not a valid module.' % mod_n)

def restart(bot, cmd):
    """
    !d Restart $nick$
    !r administrator
    """
    quotes = [
        '(Terminator) I\'ll be back.',
        'Back in a sec guys',
        'brb',
        'Be right back, homies'
    ]

    choice = random.randint(0, len(quotes) - 1)
    bot._broadcast(quotes[choice])
    bot.disconnect()

    # Reuse args and run Oracle again
    args = sys.argv
    args.insert(0, sys.executable)
    if sys.platform == 'win32':
        args = ['"%s"' % arg for arg in args]
    os.execv(sys.executable, args)

def stop(bot, cmd):
    """
    !d Disconnect and stop $nick$
    !r administrator
    """
    # Can't multi-thread here or the messages
    # won't be sent until after the bot disconnects
    bot._broadcast('Goodbye!')
    bot.stop()

def _chat(bot, args):
    user, _, message = args

    # Send a reply to a specific (connected) channel
    # Must be moderator+
    for channel in bot.channels:
        if message[0].startswith(channel):
            bot.chat_event(user, channel, message[1:])
