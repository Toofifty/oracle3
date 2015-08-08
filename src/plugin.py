# -- coding: utf-8 --
"""
Oracle 3.0 IRC Bot

plugin.py
"""

from errors import ArgumentError
import os, sys, traceback

class PluginLoader(object):
    # Plugin Loader class
    # Finds and imports all mods inside /mod/incl.txt
    # Also handles sending events through to mods

    def __init__(self, bot):
        # Iterates through incl.txt, loads mods

        self.mods = []
        print '... Loading mods'
        with open('../src/mod/incl.txt') as incl:
            mods_list = incl.read().strip().split('\n')

        for mod_name in mods_list:
            if mod_name.startswith('#'):
                continue

            self.load_mod(mod_name, bot)

        # Flag to set true if next command is a global alias
        # gives _any user_ access to a global alias.
        self.gl_alias = False

    def destroy_mods(self, bot):
        # Run _del on all mods before terminating the bot
        # VERY necessary to remove hanging threads
        for mod in self.mods:
            mod._del(bot)

    def get_mod(self, mod_name):
        # Loads the mod from string

        if 'mod.' in mod_name:
            mod_name = mod_name.replace('mod.', '')
        pack = 'mod.' + mod_name

        try:
            return getattr(__import__(pack), mod_name)

        except ImportError:
            print '-?- Tried and failed to get mod: %s' % (mod_name)
            traceback.print_exc()
            return None

    def load_mod(self, mod_name, bot):

        mod = self.get_mod(mod_name)

        self.mods.append(mod)

        try:
            self.event(self, 'mod_load', (mod_name, mod))
            mod._init(bot)

        except AttributeError:
            print '-?- Couldn\'t load mod:', mod_name
            traceback.print_exc()

    def reload_mod(self, mod, bot, cmd):
        # Tries to reload the mod passed in

        try:
            mod._del(bot)
            self.event(self, 'mod_reload', (mod,))
            reload(mod)
            bot.notice(cmd.nick, 'Reloaded ' + mod.__name__)
            mod._init(bot)

        except AttributeError:
            print 'X-X Could not reload %s, all mods must contain ' \
                '_init(bot) and _del(bot)' % mod.__name__
            bot.notice(cmd.nick, '%s was not reloaded.' % mod.__name__)

        except Exception, e:
            print 'X-X Failed to reload %s, error: %s' % (mod.__name__, e)
            bot.notice(cmd.nick, '%s was not reloaded.' % mod.__name__, e)


    def process_command(self, bot, cmd):
        # Finds the command in the loaded mods

        if str(cmd).startswith('_'):
            return

        cmd.user.add_command()

        for mod in self.mods:

            if hasattr(mod, str(cmd)):

                print '>>> Processing command...'

                try:
                    if cmd.user.rank >= self.get_command_rank(mod, cmd) \
                            or self.gl_alias:
                        getattr(mod, str(cmd))(bot, cmd)
                        print '>-> Finished command.'
                        self.gl_alias = False
                        return

                    else:
                        bot.notice(cmd.nick, 'Sorry, you do not have access to '
                        'that command.')
                        print '>!> User did not have access.'
                        return

                except ArgumentError, e:
                    bot.notice(cmd.nick, str(e))
                    print '>!> There was an argument error.'


    def get_command_rank(self, mod, cmd):
        # Get the rank from the doc bundled with
        # the command

        ranks = {
            'banned': 0,
            'user': 1,
            'moderator': 2,
            'administrator': 3,
            'developer': 4,
            'hidden': 5
        }

        doc = getattr(mod, str(cmd)).__doc__

        # Child command ranks
        if '!parent-command' in doc:

            if len(cmd.args) == 0:
                if not '!parent-command !r ' in doc:
                    raise Exception('No default command rank for %s' % str(cmd))
                # No child command, use default rank for parent command
                cmd_rank = doc.split('!r ', 1)[1]
                cmd_rank = cmd_rank.split(' ')[0].rstrip()
            else:
                if not cmd.args[0] in doc:
                    raise ArgumentError(
                        cmd.args[0], 'is not a child command of %s' % str(cmd)
                    )
                # Cut after !c <command>, so next !r will be the rank
                cmd_rank = doc.split('!c %s' % cmd.args[0], 1)[1]
                # Cut after next !r (cmd_rank now starts with rank)
                cmd_rank = cmd_rank.split('!r ', 1)[1]
                # Cut before next space, trim newline characters
                cmd_rank = cmd_rank.split(' ', 1)[0].rstrip()

            return ranks[cmd_rank]

        elif '!r' in doc:
            # Cut after next !r (cmd_rank now starts with rank)
            cmd_rank = doc.split('!r ', 1)[1]
            # Cut before next space, trim newline characters
            cmd_rank = cmd_rank.split(' ', 1)[0].rstrip()

            return ranks[cmd_rank]

        else:

            if mod.__name__ == 'mod.emotes':
                return 1

            print '-X- No command rank found for %s.%s, hiding.' % \
                (mod.__name__, str(cmd))
            return 5


    def event(self, bot, event_name, args):
        # Executes a global event which all
        # plugins have access to
        #   _chat (user, channel, message)
        #   _command (input)
        #   _message (user, message)
        #   _join (user, channel)
        #   _part (user, channel)
        #   _nick (user, nick)
        #   _bot_join (channel)
        #   _invite (user, channel)
        #   _whois_311 (user, realname, domain)
        #   _whois_319 (user, channels)
        #   _whois_317 (user, idle_seconds, signon_time)
        #   _whois_330 (user, ident)
        #   _error (error)
        # Example:
        #   def _message(bot, args):
        #       user, channel, message = args
        #       print '%s from %s said: %s' % (user.nick, channel, message)

        func = '_' + event_name

        for mod in self.mods:
            if hasattr(mod, func):
                try:
                    getattr(mod, func)(bot, args)
                except:
                    traceback.print_exc()
                    print 'Error encountered executing event', event_name,
                    print 'for module:', mod.__name__
