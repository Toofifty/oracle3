# -- coding: utf-8 --
"""
Oracle 3.0 IRC Bot

help.py
"""

import types, inspect
from format import BOLD, ITALICS, RESET
from errors import ArgumentError

###################################

def _init(b):
    print '^^^ %s loaded' % __name__

def _del(b):
    print 'vvv %s unloaded' % __name__

####################################

# All commands are called with the arguments
# <module>.<command>(bot.Oracle(), bot.Command())
# There are abbreviated to (bot, cmd)

def categories(bot, cmd):
    """
    !d List all categories
    !r user
    """
    restrict = [
        'mod.format',
        'mod.log'
    ]
    # Add mods to list
    message = []
    for mod in bot.plugins.mods:
        if not mod in restrict:
            # Remove 'mod.' from module name
            message.append(mod.__name__.replace('mod.', '').capitalize())
    # Concatenate mods into comma separated string, output to user
    cmd.output('Categories: %s' % (RESET + ', ' + BOLD).join(message))

def help(bot, cmd):
    """
    !d Print command usage and help guides
    !a [cmd|category] [page]
    !r user
    """

    B = BOLD
    I = ITALICS
    R = RESET

    def parse_mod(mod):
        # Get all the functions of the module, if they are
        # an instance of FunctionType
        cmds = [
            getattr(mod, func) for func in dir(mod)
            if isinstance(getattr(mod, func), types.FunctionType)
        ]
        # Collection of dicts for final output
        cmd_list = []

        for func in cmds:
            if not func.__name__.startswith('_'):
                # Ensure nothing is requested for hidden functions
                cmd_dict = parse_cmd(func.__name__, inspect.getdoc(func))
                if cmd_dict is not None:
                    # Add dict (list) to current list
                    cmd_list = cmd_list + cmd_dict

        return cmd_list

    def parse_cmd(func_name, doc):
        # Returns a list of dicts of the command:
        # {name, args, desc}
        # Returns multiple dicts if the cmd is a parent command
        if doc is None:
            print '!!! Doc not found for', func_name
            return None

        if '!parent-command' in doc and '!c' in doc:
            docs = doc.split('!c ')[1:]
            cmd_list = []
            for doc in docs:
                cmd_dict = parse_cmd(func_name + ' ' + doc.split('\n')[0], doc)
                if cmd_dict is not None:
                    cmd_list = cmd_list + cmd_dict

            return cmd_list

        desc = rank = args = ''
        if len(doc.split('\n')) == 1:
            # SHOULD be an emote, since every other command should
            # have a rank and description
            desc = doc
        else:
            # Only emotes are case sensitive
            func_name = func_name.upper()

            # Regular command
            for line in doc.split('\n'):
                line = line.strip()

                # Description
                if line.startswith('!d '):
                    desc = line.replace('!d ', '').capitalize()

                elif line.startswith('!a '):
                    args = line.replace('!a ', '').upper()

                elif line.startswith('!r '):
                    rank = bot.ranks[line.replace('!r ', '').lower()]
                    if cmd.user.rank < rank or rank < 0:
                        return None

        return [{'name': func_name, 'args': args, 'desc': desc}]

    def format_cmd_list(cmd_list):

        if cmd_list is None:
            # The cmd_list may be none if the command exists, but no doc
            # was returned (i.e. user doesn't have the rank)
            # We'll let an outside function handle this gracefully
            return None

        # The output list of commands, as formatted strings
        text_list = []
        # Align all commands to the longest (+2), to neaten it
        align = 2 + max(
            # Find longest command in the list
            [len(cmd['name'] + cmd['args']) for cmd in cmd_list]
        )

        for cmd in cmd_list:
            cmd_just = (cmd['name'] + ' ' + cmd['args']).ljust(align)


            text_list.append(cmd_just + ' ' + cmd['desc'])

        return text_list

    def output_paged_list(cmd_list):
        if len(cmd_list) > 10:
            # Use more than one page for the help, try to
            # parse the second arg as page number
            page = 1
            out = format_cmd_list(cmd_list)

            if len(cmd.args) > 1:
                try:
                    page = int(cmd.args[1])
                except ValueError:
                    cmd.output('Usage: .help %s [%d-%d]'
                        % (cmd.args[0].lower(), 1,
                        int(len(out) / 10) + 1))
                    return

            if page < 1:
                page = 1
            if page > len(out) / 10:
                page = int(len(out) / 10) + 1

            # Add page number message to outgoing message
            # Also get help results based on page number,
            # from 10*(p-1) to 10*p
            out = ['Page %d of %d' % (page, int(len(out) / 10) + 1)] \
                + out[10 * (page - 1):10 * page]
            cmd.output(*out)
        else:
            cmd.output(*format_cmd_list(cmd_list))

    if len(cmd.args) == 0:
        # Output regular help
        cmd.output(
            '< %s$nick$%s Help Guide >' % (B, R),
            'Check out the following commands to get started:',
            '\t%s.help $nick$' % B,
            '\t%s.help %s<%scategory%s> [%spage%s]' % (B, R, B, R, B, R),
            '\t%s.help %s<%scommand%s>' % (B, R, B, R),
            '\t%s.help search "%s<%sphrase...%s>%s" %s[%spage%s]'
                % (B, R, B, R, B, R, B, R),
            '\t%s.help all %s[%spage%s]' % (B, R, B, R),
            'Categories can be listed with %s.categories' % B
        )

    else:
        if cmd.args[0].lower() in [bot.nick.lower(), 'oracle']:
            # .help oracle
            cmd.output(
                '< $nick$ Usage Guide >',
                'Command notation:',
                '    <angle brackets>   Required arguments',
                '    [square brackets]  Optional arguments',
                '    option1|option2    Pick one option',
                '    ellipsis...        Allows multiple words, separated by '
                'spaces',
                '    "<arg...>"         Multiple words %scan%s be in one arg, '
                'surrounded by quotation marks' % (I, R),
                'Tips:',
                '    Crappy formatting? Download a proper IRC client (mIRC, '
                'HexChat)',
                '    Use %s/invite $nick$ <#channel>%s to bring $nick$ into '
                'your channel' % (B, R),
                '    Report and log errors with the %s.error <message...>%s '
                'command' % (B, R),
                '    Set custom command aliases with %s.alias%s' % (B, R),
                '    Perform multiple commands by separating them with %s;%s'
                ' E.g. .cmd1 ; .cmd2 (spaces required)' % (B, R)
            )

        elif cmd.args[0].lower() == 'search':
            # .help search
            pass

        elif cmd.args[0].lower() == 'all':
            # .help all

            # Collection of dicts for final output
            cmd_list = []

            for mod in bot.plugins.mods:
                cmd_list = cmd_list + parse_mod(mod)

            output_paged_list(cmd_list)
            return

        elif cmd.args[0].lower() == 'categories':
            # Just in case
            categories(bot, cmd)
            return

        elif bot.plugins.get_mod(cmd.args[0]) is not None:
            # .help <category>
            mod = bot.plugins.get_mod(cmd.args[0])
            cmd_list = parse_mod(mod)

            if len(cmd_list) > 0:
                output_paged_list(cmd_list)
                return
            # else
            # Exit to default fail message below
        else:
            # Check if it is a command
            for mod in bot.plugins.mods:
                # Get possible commands (functions) in mods
                cmds = [
                    # Get the attribute from the mod
                    getattr(mod, func) for func in dir(mod)
                    # But only if it is a function instance
                    if isinstance(getattr(mod, func), types.FunctionType)
                ]
                for func in cmds:
                    if func.__name__.startswith('_'):
                        # Ensure no help is requested for hidden functions
                        continue

                    if func.__name__.lower() == cmd.args[0].lower():
                        # We've found the command

                        # Parse the command and it's doc to a dict
                        cmd_dict_list = parse_cmd(func.__name__,
                            inspect.getdoc(func))

                        if cmd_dict_list is not None:
                            cmd.output(*format_cmd_list(cmd_dict_list))
                            return
                        else:
                            # Exit out for default fail message below
                            break
            cmd.output('No help found matching %s.' % cmd.args[0])
