# -- coding: utf-8 --
"""
Oracle 3.0 IRC Bot

mail.py
"""

import time, traceback
from errors import ArgumentError
from format import BOLD, RESET

###################################

def _init(b):
    print '^^^ %s loaded' % __name__

    # Create mail table in the database
    if not b.db.table_exists('mail'):
        print '... Creating mail table'
        b.db.execute('CREATE TABLE mail(sent INT, read BOOLEAN, sender TEXT, '
            'receiver TEXT, title TEXT, contents TEXT)', ())

def _del(b):
    print 'vvv %s unloaded' % __name__

####################################

def mail(bot, cmd):
    """!parent-command !r user
    !c inbox
        !d Get a list of mail sent to you
        !r user
        !a [filter...]
    !c read
        !d Read a single piece of mail
        !r user
        !a <mail names... or *>
    !c send
        !d Send mail to a user
        !r user
        !a <nick> <title> <message...>
    !c delete
        !d Delete a piece of mail from your inbox
        !r user
        !a <mail names... or *>
    """
    def inbox(bot, cmd):
        # Grab all mail for user
        inbox = bot.db.fetchall('SELECT * FROM mail WHERE receiver=?',
            (cmd.user.vhost,))
        if inbox is None or len(inbox) == 0:
            # 'inbox' is empty
            cmd.output('You have no mail :(')
        else:
            msg = []
            filt = ' '.join(cmd.args)
            for mail in inbox:
                # Make sure mail matches the filter
                if filt in mail['title']:
                    sent = time.asctime(time.gmtime(mail['sent']))
                    diff = time.time() - mail['sent']
                    # Find out difference in days, hours, mins, secs
                    dm, ds = divmod(diff, 60)
                    dh, dm = divmod(dm, 60)
                    dd, dh = divmod(dh, 24)
                    # Create a usable string to output
                    if dd > 0:
                        diff_str = '%d day%s ago' % (dd, 's' if dd > 1 else '')
                    elif dh > 0:
                        diff_str = '%d hour%s ago' % (dh, 's' if dh > 1 else '')
                    elif dm > 0:
                        diff_str = '%d minute%s ago' % (dm, 's' if dm > 1
                            else '')
                    else:
                        diff_str = 'less than a minute ago'
                    # Change the sender's vhost to their nick
                    sender = bot.get_user(mail['sender']).nick
                    msg.append('%s%s (%s) %s: %s' % (BOLD if not mail['read']
                        else '', sent, diff_str, sender, mail['title']))
            # Print to user
            cmd.output(*msg)

    def read(bot, cmd):
        # Grab all mail for user
        inbox = bot.db.fetchall('SELECT * FROM mail WHERE receiver=?',
            (cmd.user.vhost,))
        if inbox is None or len(inbox) == 0:
            cmd.output('You have no mail :(')
        elif len(cmd.args) == 0:
            cmd.output('Usage: .mail read <mail>')
        else:
            def matches(args, title):
                # Easy way to check if args match the title
                # of the mail, * glob will always return true
                if '*' in args:
                    return True
                for arg in args:
                    if '"' in arg:
                        if arg.lower().replace('"', '') == title.lower():
                            return True
                    elif arg.lower() in title.lower():
                        return True
                return False

            msg = []
            read = []
            for mail in inbox:
                if matches(cmd.args, mail['title']):
                    sent = time.asctime(time.gmtime(mail['sent']))
                    diff = time.time() - mail['sent']
                    dm, ds = divmod(diff, 60)
                    dh, dm = divmod(dm, 60)
                    dd, dh = divmod(dh, 24)
                    sender = bot.get_user(mail['sender']).nick
                    msg.append('%s on %s (%dd %dh %02dm ago): %s' % (sender,
                        sent, dd, dh, dm, mail['contents']))
                    read.append(mail)
            cmd.output(*msg)
            for mail in read:
                # Go through all mail records, set to read
                bot.db.execute('UPDATE mail SET read=? WHERE sent=? AND '
                    'title=?', (1, mail['sent'], mail['title']))

    def send(bot, cmd):
        if len(cmd.args) < 3:
            cmd.output('Usage: .mail send <nick> <title> <message...>')
        else:
            # Place a new record into the database
            recip = bot.get_user(cmd.args[0])
            if recip is None:
                cmd.output('User %s not found.' % cmd.args[0])
            else:
                bot.db.execute('INSERT INTO mail VALUES (?, ?, ?, ?, ?, ?)',
                    (time.time(), 0, cmd.user.vhost, recip.vhost,
                    cmd.args[1], ' '.join(cmd.args[2:])))
                cmd.output('Mail sent.')

    def delete(bot, cmd):
        if len(cmd.args) == 0:
            cmd.output('Usage: .mail delete <mail or *>')
        elif cmd.args[0] == '*':
            bot.db.execute('DELETE FROM mail WHERE receiver=?',
                (cmd.user.vhost,))
            cmd.output('Deleted all mail.')
            return
        else:
            matching = bot.db.fetchall('SELECT * FROM mail WHERE title = ? '
                'AND receiver = ?', (cmd.args[0], cmd.user.vhost))

            if len(matching) > 0:
                bot.db.execute('DELETE FROM mail WHERE title = ?  AND '
                    'receiver = ?', (cmd.args[0], cmd.user.vhost))
                cmd.output('Mail deleted.')
            else:
                cmd.output('No mail found for "%s".' % cmd.args[0])

    try:
        if len(cmd.args) == 0:
            raise ArgumentError()
        # Remove child command from args
        child_cmd = cmd.args[0]
        cmd.args = cmd.args[1:]
        locals()[child_cmd](bot, cmd)

    except ArgumentError:
        cmd.output('Usage: .mail <check|read|send|del>')

    except Exception:
        traceback.print_exc()
        cmd.output('Sorry, something went wrong. This error has been logged.')

def _join(bot, args):
    user, channel = args
    inbox = bot.db.fetchall('SELECT * FROM mail WHERE receiver=? AND read=0',
        (user.vhost,))
    if inbox is not None and len(inbox) > 0:
        user.message('You have mail! (.help mail)')
