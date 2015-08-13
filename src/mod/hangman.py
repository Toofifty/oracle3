# -- coding: utf-8 --
"""
Oracle 3.0 IRC Bot

trivia2.py
"""

import urllib2, traceback, random
from math import sqrt
from format import CYAN, RESET, BOLD
from errors import ArgumentError
FORMAT = '[%sHangman%s]' % (CYAN, RESET)
COST = 50

game = None

###################################

def _init(b):
    print '^^^ %s loaded' % __name__

def _del(b):
    print 'vvv %s unloaded' % __name__
    global game
    game = None

####################################

def _delete_game():
    global game
    game = None

class Hangman(object):
    def __init__(self, bot, difficulty, randword):
        lives = {
            'easy': 15,
            'medium': 10,
            'hard': 5,
            'boss': 1
        }

        self.bot = bot
        self.diff = difficulty
        self.lives = lives[self.diff]
        if randword:
            self.complete_phrase = urllib2.urlopen(
                'http://randomword.setgetgo.com/get.php'
            ).read().rstrip()
        else:
            self.complete_phrase = random.choice(self.load_phrases())
        self.reward = (1500 / self.lives) / sqrt(len(self.complete_phrase))
        if randword:
            self.reward *= 3
        self.phrase = ''
        self.guessed_letters = ''

        for word in self.complete_phrase.split(' '):
            self.phrase = self.phrase + '_' * len(word) + ' '
        self.phrase = list(self.phrase)

        if self.diff == 'easy':
            self.guess_letter(random.choice('aei'))
            self.guess_letter(random.choice('ours'))

    def remove_life(self, user):
        self.lives -= 1
        self.reward *= 0.75
        if self.lives == 0:
            self.bot.broadcast('%s Game over! %s lost the last life.' % (FORMAT,
                user.nick))
            _delete_game()
        else:
            self.bot.broadcast('%s %s guessed wrong! %d lives left.' % (FORMAT,
                user.nick, self.lives))

    def guess_letter(self, letter):
        letter = letter.lower()
        self.guessed_letters = self.guessed_letters + letter
        if not letter in self.complete_phrase:
            return False
        position = -1
        while True:
            position = self.complete_phrase.find(letter, position + 1)
            if position == -1:
                break
            self.phrase[position] = letter
        if not '_' in self.phrase:
            return 'winner'
        return True

    def guess_phrase(self, guess):
        if guess.lower() == self.complete_phrase.lower():
            self.phrase = list(self.complete_phrase)
            return True
        return False

    def load_phrases(self):
        with open('../config/hangman.txt') as f:
            phrases = f.read().strip().split('\n')
        return phrases

    def phrase_spaced(self):
        return ''.join([l + ' ' for l in self.phrase])

    def phrase_text(self):
        return ''.join(self.phrase)

    def print_phrase(self):
        self.bot.broadcast(
            '%s %s | Guessed: %s | %d lives left | Prize: %d $curr$' % (
                FORMAT, self.phrase_spaced(), self.guessed_letters, self.lives,
                self.reward
            )
        )

    def end(self, winner):
        self.print_phrase()
        self.bot.broadcast('%s %s wins! +%d $curr$.' % (FORMAT, winner.nick,
            self.reward))
        winner.add_points(self.reward)
        winner.message('You now have %d $curr$.' % (winner.points))
        _delete_game()

def hangman(bot, cmd):
    """!parent-command !r user
    !c new
        !d Create a new game of hangman. Costs 50 $curr$.
        !a [easy|medium|hard|boss] [random]
        !r user
    !c answer
        !d Get the current hangman phrase
        !r administrator
    !c guess
        !d Guess a letter or the entire phrase
        !a [letter/phrase]
        !r user
    !c info
        !d Get the current phrase as well as guess tally and used letters
        !r user
    """
    def new(bot, cmd):
        global game
        if game is not None:
            cmd.output('There is already a hangman game running.')
        else:
            diff = 'medium'
            random = False
            if len(cmd.args) > 0:
                if len(cmd.args) > 1:
                    random = cmd.args[1].lower() == 'random' or \
                        cmd.args[1].lower() == 'r'
                if not cmd.args[0] in ['easy', 'medium', 'hard', 'boss']:
                    cmd.output('Please choose easy, medium or hard difficulty.')
                    return
                else:
                    diff = cmd.args[0]
            if cmd.user.rank < 3:
                if cmd.user.points > COST:
                    cmd.user.add_points(-COST)
                    cmd.output('You pay %d $curr$ to start a new game.' % COST)
                else:
                    cmd.output('You don\'t have enough points to start a game.')
                    return
            game = Hangman(bot, diff, random)
            game.print_phrase()

    def guess(bot, cmd):
        global game
        if game is None:
            cmd.output('There is no hangman game at the moment.')
        else:
            if len(cmd.args) > 1 or len(cmd.args[0]) > 1:
                # User has guessed the entire phrase
                if game.guess_phrase(' '.join(cmd.args)):
                    game.end(cmd.user)
                else:
                    game.remove_life(cmd.user)
            else:
                result = game.guess_letter(cmd.args[0])
                if result == 'winner':
                    game.end(cmd.user)
                elif result:
                    game.print_phrase()
                else:
                    game.remove_life(cmd.user)

    def answer(bot, cmd):
        global game
        if game is None:
            cmd.output('There is no hangman game at the moment.')
        else:
            cmd.output(game.complete_phrase)

    def info(bot, cmd):
        global game
        if game is None:
            cmd.output('There is no hangman game at the moment.')
        else:
            game.print_phrase()

    try:
        if len(cmd.args) == 0:
            info(bot, cmd)
            return
        # Remove child command from args
        child_cmd = cmd.args[0]
        cmd.args = cmd.args[1:]
        locals()[child_cmd](bot, cmd)

    except Exception:
        traceback.print_exc()
        cmd.output('Sorry, something went wrong. This error has been logged.')


def randomword(bot, cmd):
    """
    !d Get a random word using the same API as used in hangman.
    !r user
    """
    content = urllib2.urlopen('http://randomword.setgetgo.com/get.php').read()
    cmd.output(content)
