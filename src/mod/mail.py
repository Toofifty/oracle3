# -- coding: utf-8 --
"""
Oracle 3.0 IRC Bot

mail.py
"""

import time
from errors import ArgumentError

###################################

def _init(b):
    print '^^^ %s loaded' % __name__

    # Create mail table in the database
    if not b.db.table_exists('mail'):
        print '... Creating mail table'
        self.bot.db.execute('CREATE TABLE mail(sent INT, read BOOLEAN, '
            'sender TEXT, receiver TEXT, title TEXT, contents TEXT)', ())

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
    !c del
        !d Delete a piece of mail from your inbox
        !r user
        !a <mail names... or *>
    """
    def inbox(bot, cmd):
        inbox = bot.db.fetchall('SELECT * FROM mail WHERE receiver=?',
            (cmd.user.vhost,))
        if inbox is None or len(inbox) == 0:
            cmd.output('You have no mail :(')
        else:
            msg = []
            filt = ' '.join(cmd.args)
            for mail in inbox:
                # Make sure mail matches the filter
                if filt in mail['title']:
                    sent = time.asctime(time.gmtime(mail['sent']))
                    diff = time.time() - mail['sent']
                    dh, dm = divmod(diff, 360)
                    dd, dh = divmod(dh, 24)
                    diff_str = ''
                    if dd > 0:
                        diff_str = '%d day%s ago' % (dd, 's' if dd > 1 else '')
                    elif dh > 0:
                        diff_str = '%d hour%s ago' % (dh, 's' if dd > 1 else '')
                    elif dm > 0:
                        diff_str = '%d minute%s ago' % (dm, 's' if dd > 1
                            else '')
                    # Change the sender's vhost to their nick
                    sender = bot.get_user(mail['sender']).nick
                    msg.append('%s (%s) %s: %s' % (sent, diff_str, sender,
                        mail['title']))
            cmd.output(*msg)

    def read(bot, cmd):
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
            for mail in inbox:
                if matches(cmd.args, mail['title']):
                    sent = time.asctime(time.gmtime(mail['sent']))
                    diff = time.time() - mail['sent']
                    dh, dm = divmod(diff, 360)
                    dd, dh = divmod(dh, 24)
                    sender = bot.get_user(mail['sender']).nick
                    msg.append('%s at %s (%dd %dh %02dm ago): %s' % (sender,
                        sent, dd, dh, dm, mail['content']))
            cmd.output(*msg)

    def send(bot, cmd):
        if len(cmd.args) < 3:
            cmd.output('Usage: .mail send <nick> <title> <message...>')
        else:
            recip = bot.get_user(cmd.args[0])
            if recip is None:
                cmd.output('User %s not found.' % cmd.args[0])
            else:
                bot.db.execute('INSERT INTO mail VALUES (?, ?, ?, ?, ?, ?)',
                    (time.time(), False, cmd.user.vhost, recip.vhost,
                    cmd.args[1], cmd.args[2:]))
                cmd.output('Mail sent.')

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
