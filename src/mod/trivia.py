# -- coding: utf-8 --
"""
Oracle 3.0 IRC Bot

trivia.py
"""

from threading import Thread
from format import PURPLE, RESET
trivia = None

###################################

def _init(b):
    print '^^^ %s loaded' % __name__
    global trivia
    trivia = Trivia(1200, 100, b)
    trivia.start()

def _del(b):
    print 'vvv %s unloaded' % __name__
    global trivia
    trivia.kill()

####################################

winning_alts = [
    'is a genius!',
    'is a trivia master!',
    'probably just Googled the answer.',
    'got the answer!',
    'knows their stuff!',
    'won\'t be beaten!'
]

class Trivia(Thread):
    def __init__(self, interval, reward, bot):
        Thread.__init__(self)
        self.questions = self.load_questions()
        self.reward = reward
        self.interval = interval
        self.time_left = interval
        self.bot = bot
        self.current = ''
        self.format = '[%sTrivia%s]' % (PURPLE, RESET)
        self.kickstarters = []
        self.skippers = []
        self.dead = False
        print '!!! Trivia thread started'

    def load_questions(self):
        questions = {}
        for file_name in listdir('../config/trivia'):
            if 'disabled' in file_name:
                continue
            else:
                with open('../config/trivia/' + file_name) as file:
                    list = file.read().strip().split('\n')
                for line in list:
                    qa = line.split(': ')
                    # The question is the first part of the line
                    qu = qa[1]
                    # Ans may contain multiple answers, separated by a comma
                    ans = qa[2]
                    questions[qu] = ans.lower().strip().split(', ')
        return questions

    def kickstart(self, user):
        if user in self.kickstarters:
            return 0
        self.kickstarters.append(nick)
        diff = random.randint(self.interval * 0.1, self.interval * 0.6)
        self.time_left -= diff
        return diff

    def new_question(self):
        return random.choice(self.questions.keys())

    def get_answers(self, question=None):
        if question is not '' and question is not None:
            return self.questions[question]
        else:
            for k, v in self.questions.iteritems():
                if k == self.current:
                    return v
        return 'No answer found.'

    def guess(self, guess):
        guess = ' '.join(guess)
        if guess.lower() in self.get_answers():
            self.current = ''
            return True, self.reward
        else:
            return False, None

    
