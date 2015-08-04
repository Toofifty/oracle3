# -- coding: utf-8 --
"""
Oracle 3.0 IRC Bot

trivia2.py
"""

from threading import Thread
from format import PURPLE, RESET, BOLD
trivia_handler = None

# Rewrite and improvement on the trivia game

###################################

def _init(b):
    print '^^^ %s loaded' % __name__
    global trivia_handler
    trivia_handler = TriviaHandler(1200, b)
    trivia_handler.start()

def _del(b):
    print 'vvv %s unloaded' % __name__
    global trivia_handler
    trivia_handler.kill()

####################################

class TriviaHandler(Thread):
    # Trivia organizer class
    # Starts a new trivia (of one of the separate types)
    # every <interval> min, handles skipping, kickstarting
    # and questions

    def __init__(self, interval, bot):
        self.dead = False
        self.game = None
        self.bot = bot
        self.time_left = interval
        self.interval = interval
        self.skip_time = 0
        self.skips = []
        self.kicks = []
        # Questions is a dict of categories (strings) and dicts of
        # "question" : [answers]
        # Loaded from plaintext using the load_questions method.
        self.questions = {
            # "general": {
            #     "some question": ["a1", "a2"],
            #     "another": ["a"]
            # }
        }

    def load_questions(self):
        # Load questions into very deep set of dicts
        # with category keys and dict values
        # Files must be laid out as follows
        # NB: categories must be split between files.
        # <any_filename>.txt:
        # <category>
        # <question>: <answer>[, alternatives...]
        for file_name in listdir('../config/trivia'):
            if 'disabled' in file_name:
                continue
            else:
                with open('../config/trivia/' + file_name) as file:
                    lines = file.read().strip().split('\n')
                if lines[0].contains(':'):
                    raise Exception('Bad trivia file format')
                else:
                    # Save category (key)
                    category = lines[0]
                # Questions for this single category
                questions = {}

                for line in lines[1:]:
                    qa = line.split(': ')
                    # The question is the first part of the line
                    qu = qa[1]
                    # Ans may contain multiple answers, separated by a comma
                    ans = qa[2]
                    questions[qu] = ans.lower().strip().split(', ')

                self.questions[category] = questions

    def remove_question(self, category, question):
        # Remove a question from the dict when it has been used
        # Avoids repeats until all questions have been asked.
        self.questions[category] #del(question) ?
        for c, q in iteritems(self.questions):
            if len(q) == 0 or q == None:
                # Remove category completely when all questions have
                # been asked.
                self.questions #.del(category)
        if len(self.questions) == 0:
            # Reload all questions when all categories have been used
            # i.e. all questions have been asked.
            self.load_questions()

    def skip(self, user):
        # Allow users to skip the current question.
        # First skip starts skip timer, further skips reduce by 1/2 or 60s
        if user not in self.skips:
            self.skips.append(user)
            if len(self.skips) == 1:
                # Set skip time to 4 mins
                self.skip_time = 240
                self.start_skip_clock()
            else:
                # Halve/remove 60 from skip time
                self.skip_time -= max(self.skip_time / len(self.skips), 60)
            return self.skip_time
        return False

    def kick(self, user):
        # Kickstart the trivia and remove time to the next round
        if user not in self.kick:
            self.kicks.append(user)
            time = random(60, 720) # ?
            self.time_left -= time
            return time
        return False

    def kill(self):
        # Allows us to kill the thread when restarting/reloading Oracle
        self.dead = True

    def run(self):
        while not self.dead:
            while self.time_left > 2:
                self.time_left -= 2
                if self.skip_time != 0:
                    # If the skip timer is running, dec 2
                    self.skip_time -= 2
                    if self.skip_time == 0:
                        # Create a new question. This is safe because
                        # when a question is answered, skip time will be
                        # set to 0 (stops skip timer completely)
                        self.time_left = 0
                time.sleep(2)
            rng = random(1)
            if rng > 0.75:
                # Start a challenge trivia
                self.game = TriviaChallenge(self)
            elif rng > 0.5:
                # Start a hard trivia
                self.game = TriviaHard(self)
            elif rng > 0.25:
                # Start a risk trivia
                self.game = TriviaRisk(self)
            else:
                # Start a regular trivia
                self.game = TriviaRegular(self)
            self.kicks = []
            self.skips = []
            self.time_left = self.interval
            time.sleep(2)

def __chat(bot, args):
    user, channel, message = args

    global trivia_handler
    trivia_handler.guess(user, ' '.join(message))
