# -- coding: utf-8 --
"""
Oracle 3.0 IRC Bot

format.py
"""

from colorama import init, Fore, Back, Style
init(autoreset=True)

###################################

def _init(b):
    print '^^^ %s loaded' % __name__

def _del(b):
    print 'vvv %s unloaded' % __name__

####################################

RESET       = '\x0F'
BOLD        = '\x02'
ITALICS     = '\x1D'
UNDERLINE   = '\x1F'

WHITE       = '\x0300'
BLACK       = '\x0301'
DARKBLUE    = '\x0302'
DARKGREEN   = '\x0303'
RED         = '\x0304'
DARKRED     = '\x0305'
PURPLE      = '\x0306'
ORANGE      = '\x0307'
YELLOW      = '\x0308'
GREEN       = '\x0309'
CYAN        = '\x0310'
LIGHTBLUE   = '\x0311'
BLUE        = '\x0312'
PINK        = '\x0313'
DARKGREY    = '\x0314'
GREY        = '\x0315'

console = {
    BOLD:       '',
    ITALICS:    '',
    UNDERLINE:  '',

    WHITE:      Style.BRIGHT + Fore.WHITE,
    BLACK:      Style.NORMAL + Fore.BLACK,
    DARKBLUE:   Style.NORMAL + Fore.BLUE,
    DARKGREEN:  Style.NORMAL + Fore.GREEN,
    RED:        Style.BRIGHT + Fore.RED,
    DARKRED:    Style.NORMAL + Fore.RED,
    PURPLE:     Style.NORMAL + Fore.MAGENTA,
    ORANGE:     Style.NORMAL + Fore.YELLOW,
    YELLOW:     Style.BRIGHT + Fore.YELLOW,
    GREEN:      Style.BRIGHT + Fore.GREEN,
    CYAN:       Style.NORMAL + Fore.CYAN,
    LIGHTBLUE:  Style.BRIGHT + Fore.CYAN,
    BLUE:       Style.BRIGHT + Fore.BLUE,
    PINK:       Style.BRIGHT + Fore.MAGENTA,
    DARKGREY:   Style.BRIGHT + Fore.BLACK,
    GREY:       Style.NORMAL + Fore.WHITE,
}
