# -- coding: utf-8 --
"""
Oracle 3.0 IRC Bot

stats.py
"""

import time
from errors import ArgumentError

###################################

def _init(b):
    print '^^^ %s loaded' % __name__

def _del(b):
    print 'vvv %s unloaded' % __name__

####################################

def commandcount(bot, cmd):
    """
    !d Get the amount of commands issued by a user (or self)
    !a [user]
    !r user
    """
    user = cmd.user
    if len(cmd.args) > 0:
        user = bot.get_user(cmd.args[0])
    cmd.output('%s: %d commands' % (user.nick, user.cmd_count))

def listusers(bot, cmd):
    """
    !d List all users who have records (warning: spam)
    !r user
    """
    pass

def score(bot, cmd):
    """!parent-command !r user
    !c top
        !d List top players
        !a [amount]
        !r user
    !c check
        !d Check a user's score (or your own)
        !a [user]
        !r user
    !c set
        !d Set a user's score
        !a <user> <points>
        !r administrator
    !c add
        !d Add to user's score
        !a <user> <points>
        !r administrator
    !c rem
        !d Remove from user's score
        !a <user> <points>
        !r administrator
    """
    def top(bot, cmd):
        # Set amount to first arg, or 5 if no args
        am = int(cmd.args[0]) if len(cmd.args) > 0 else 5
        am = max(am, 20)
        # Get the first _am_ of users
        users = bot.db.fetchall('SELECT * FROM users ORDER BY points DESC',
            ())[:am-1]
        msg = []
        n = 1
        for user in users:
            if user['points'] < 1:
                break
            msg.append('%d. %s %s' % (n, user['nick'].ljust(20),
                str(user['points']).rjust(6)))
            n += 1
        cmd.output(*msg)

    def check(bot, cmd):
        user = cmd.user
        if len(cmd.args) > 0:
            user = bot.get_user(cmd.args[0])
            if user is None:
                cmd.output('User "%s" not found.' % cmd.args[0])
                return
        cmd.output('%s: %d $curr$' % (user.nick, user.points))

    def set(bot, cmd):
        if len(cmd.args) < 2:
            cmd.output('Usage: .score set <user> <points>')
        else:
            user = bot.get_user(cmd.args[0])
            user.set_points(int(cmd.args[1]))
            cmd.output('%s now has %d $curr$.' % (user.nick, user.points))

    def add(bot, cmd):
        if len(cmd.args) < 2:
            cmd.output('Usage: .score add <user> <points>')
        else:
            user = bot.get_user(cmd.args[0])
            user.add_points(int(cmd.args[1]))
            cmd.output('%s now has %d $curr$.' % (user.nick, user.points))

    def rem(bot, cmd):
        if len(cmd.args) < 2:
            cmd.output('Usage: .score rem <user> <points>')
        else:
            user = bot.get_user(cmd.args[0])
            user.add_points(-int(cmd.args[1]))
            cmd.output('%s now has %d $curr$.' % (user.nick, user.points))

    try:
        if len(cmd.args) == 0:
            raise ArgumentError()
        # Remove child command from args
        child_cmd = cmd.args[0]
        cmd.args = cmd.args[1:]
        locals()[child_cmd](bot, cmd)

    except ArgumentError:
        if cmd.user.rank > 2:
            cmd.output('Usage: .score <top|check|set|add|rem>')
        else:
            cmd.output('Usage: .score <top|check>')

    except Exception:
        traceback.print_exc()
        cmd.output('Sorry, something went wrong. This error has been logged.')


def seen(bot, cmd):
    """
    !d Get the last time the user was seen by $nick$
    !a <user>
    !r user
    """
    if len(cmd.args) == 0:
        cmd.output('Usage: %s.seen <user>')
    else:
        user = bot.get_user(cmd.args[0])
        if user is None:
            cmd.output('User %s not found' % cmd.args[0])
            return
        seen = time.asctime(time.gmtime(user.seen))
        diff = time.time() - user.seen
        dm, ds = divmod(diff, 60)
        dh, dm = divmod(dm, 60)
        dd, dh = divmod(dh, 24)
        cmd.output('%s was last seen on %s (%d days, %d hours ago)' %
            (user.nick, seen, dd, dh))
