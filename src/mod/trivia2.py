# -- coding: utf-8 --
"""
Oracle 3.0 IRC Bot

trivia2.py
"""

import random, os, time, traceback
from threading import Thread
from format import PURPLE, RESET, BOLD
from errors import ArgumentError
trivia_handler = None
FORMAT = '[%sTrivia%s]' % (PURPLE, RESET)

# Rewrite and improvement on the trivia game

###################################

def _init(b):
    print '^^^ %s loaded' % __name__
    global trivia_handler
    trivia_handler = TriviaHandler(120, b)
    trivia_handler.start()

def _del(b):
    print 'vvv %s unloaded' % __name__
    global trivia_handler
    trivia_handler.kill()

####################################

winning_alts = [
    'is a genius!',
    'is a trivia master!',
    'probably just Googled the answer.',
    'got the answer!',
    'knows their stuff!',
    'won\'t be beaten!'
]

incorrect_alts = [
    'Wrong!',
    'Nope.',
    'Nope!',
    'Hah! You\'re not very good at this.',
    'Incorrect!',
    'Not even close.',
    'Are you even trying?',
    'Seriously? You thought that was the answer?',
    'Oh no! That\'s not it! :(',
    'Better luck next time!',
    'I don\'t think that\'s right...',
    ''
]

def trivia(bot, cmd):
    """!parent-command !r user
    !c new
        !d Ask a new trivia question
        !r administrator
    !c time
        !d Check how long until the next trivia question
        !r user
    !c skip
        !d Start or speed up a skip timer to give a new trivia question
        !r user
    !c ks
        !d Kickstart the countdown to the next trivia question
        !r user
    """
    def new(bot, cmd):
        global trivia_handler
        trivia_handler.time_left = 2

    def time(bot, cmd):
        global trivia_handler
        m, s = divmod(trivia_handler.time_left, 60)
        cmd.output('%s Next question in %dm %ds.' % (FORMAT, m, s))

    def skip(bot, cmd):
        global trivia_handler
        skip_time = trivia_handler.skip(cmd.user)
        if not skip_time:
            cmd.output('%s You\'ve already tried to skip this question.' % FORMAT)
        else:
            m, s = divmod(skip_time, 60)
            cmd.set_loud(True)
            cmd.output('%s Skipping question in %dm %ds' % (FORMAT, m, s))

    def ks(bot, cmd):
        global trivia_handler
        time = trivia_handler.kick(cmd.user)
        if not time:
            cmd.output('%s You\'ve already kickstarted this round.' % FORMAT)
        else:
            m, s = divmod(trivia_handler.time_left, 60)
            cmd.set_loud(True)
            cmd.output('%s %s%s%s knocked %d seconds off the clock! %dm %ds '
                'until the next round.' % (FORMAT, BOLD, cmd.user.nick, RESET,
                time, m, s))

    try:
        if len(cmd.args) == 0:
            raise ArgumentError()
        # Remove child command from args
        child_cmd = cmd.args[0]
        cmd.args = cmd.args[1:]
        locals()[child_cmd](bot, cmd)

    except ArgumentError:
        if cmd.user.rank > 2:
            cmd.output('Usage: .trivia <new|time>')
        else:
            cmd.output('Usage: .trivia <time|stats|ks|skip>')

    except Exception:
        traceback.print_exc()
        cmd.output('Sorry, something went wrong. This error has been logged.')

def a(bot, cmd):
    """
    !d Answer a trivia question
    !a <answer...>
    !r user
    """
    global trivia_handler
    if len(cmd.args) > 0:
        trivia_handler.guess(cmd.user, ' '.join(cmd.args))

class TriviaHandler(Thread):
    # Trivia organizer class
    # Starts a new trivia (of one of the separate types)
    # every <interval> min, handles skipping, kickstarting
    # and questions

    def __init__(self, interval, bot):
        Thread.__init__(self)
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
        self.load_questions()
        for category, _ in self.questions.iteritems():
            table_name = self.cat_table(category)
            if not self.bot.db.table_exists(table_name):
                print '... Creating', table_name, 'table'
                self.bot.db.execute('CREATE TABLE %s(vhost TEXT, correct'
                    ' INT, incorrect INT)' % table_name, ())

    def cat_table(self, category):
        return 'trivia_' + category.replace(' ', '_').replace('\'', '')

    def load_questions(self):
        # Load questions into very deep set of dicts
        # with category keys and dict values
        # Files must be laid out as follows
        # NB: categories must be split between files.
        # <any_filename>.txt:
        # <category>
        # <question>: <answer>[, alternatives...]
        for file_name in os.listdir('../config/trivia'):
            if 'disabled' in file_name:
                continue
            else:
                with open('../config/trivia/' + file_name) as file:
                    lines = file.read().strip().split('\n')
                if ':' in lines[0]:
                    raise Exception('Bad trivia file format')
                else:
                    # Save category (key)
                    category = lines[0]
                # Questions for this single category
                questions = {}

                for line in lines[1:]:
                    qa = line.split(': ')
                    # The question is the first part of the line
                    qu = qa[0]
                    # Ans may contain multiple answers, separated by a comma
                    ans = qa[1]
                    questions[qu] = ans.lower().strip().split(', ')

                self.questions[category] = questions

    def get_question(self):
        # Get a random question from the dicts,
        # and remove it. Return a tuple of category, question, answers
        category = random.choice(self.questions.keys())
        question = random.choice(self.questions[category].keys())
        answers = self.questions[category][question]
        self.remove_question(category, question)
        return category, question, answers

    def remove_question(self, category, question):
        # Remove a question from the dict when it has been used
        # Avoids repeats until all questions have been asked.
        del self.questions[category][question]
        for c, q in self.questions.iteritems():
            if len(q) == 0 or q is None:
                # Remove category completely when all questions have
                # been asked.
                del self.questions[c]
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
            else:
                # Halve/remove 60 from skip time
                self.skip_time -= max(self.skip_time / len(self.skips), 60)
                self.skip_time = max(0, self.skip_time)
            return self.skip_time
        return False

    def kick(self, user):
        # Kickstart the trivia and remove time to the next round
        if user not in self.kicks:
            self.kicks.append(user)
            time = random.randint(60, 720)
            self.time_left -= time
            self.time_left = max(0, self.time_left)
            return time
        return False

    def kill(self):
        # Allows us to kill the thread when restarting/reloading Oracle
        self.dead = True

    def guess(self, user, guess):
        # Check if there is currently a trivia question, passes
        # guess to game object
        if self.game is None:
            user.message('%s There\'s no trivia question at the moment.')
            return False
        else:
            return self.game.guess(user, guess)

    def get_win_percent(self, user, category):
        table_name = self.cat_table(category)
        data = self.bot.db.fetchone('SELECT * FROM %s WHERE vhost=?'
            % table_name, (user.vhost,))
        print data
        if data['incorrect'] == 0:
            return data['correct'], 100
        return data['correct'], int(100 * data['correct'] /
            (data['incorrect'] + data['correct']))

    def end(self):
        self.game = None
        self.skip_time = 0
        self.kicks = []
        self.skips = []

    def run(self):
        while not self.dead:
            while self.time_left > 2:
                if self.dead:
                    return
                self.time_left -= 2
                if self.skip_time > 0:
                    # If the skip timer is running, dec 2
                    self.skip_time -= 2
                    if self.skip_time == 0:
                        # Create a new question. This is safe because
                        # when a question is answered, skip time will be
                        # set to 0 (stops skip timer completely)
                        self.time_left = 0
                time.sleep(2)
            rng = random.random()
            # if rng > 0.75:
            #     # Start a challenge trivia
            #     self.game = TriviaChallenge(self)
            # elif rng > 0.5:
            #     # Start a hard trivia
            #     self.game = TriviaHard(self)
            # elif rng > 0.25:
            #     # Start a risk trivia
            #     self.game = TriviaRisk(self)
            # else:
            #     # Start a regular trivia
            self.game = TriviaRegular(self, 100)
            self.time_left = self.interval
            self.game.start()
            time.sleep(2)

class TriviaBase(object):
    def __init__(self, handler, reward):
        self.handler = handler
        self.reward = reward
        self.category, self.question, self.answers = self.handler.get_question()
        self.table_name = self.handler.cat_table(self.category)
        self.mode = 'none'

    def guess(self, user, guess):
        # Check if the guess is in the answers list
        self.try_create_record(user)
        if guess.lower() in self.answers:
            self.end(user)
            return True
        self.add_incorrect(user)
        user.message('%s %s' % (FORMAT, random.choice(incorrect_alts)))
        return False

    def start(self):
        self.handler.bot.broadcast(
            '%s <%s: %s> %s (.help trivia)' % (FORMAT, self.category, self.mode,
            self.question)
        )

    def try_create_record(self, user):
        data = self.handler.bot.db.fetchone('SELECT * FROM %s WHERE '
            'vhost=?' % self.table_name, (user.vhost,))
        if data is None:
            self.handler.bot.db.execute('INSERT INTO %s VALUES(?, 0, 0)'
                % self.table_name, (user.vhost,))

    def add_correct(self, user):
        data = self.handler.bot.db.fetchone('SELECT * FROM %s WHERE '
            'vhost=?' % self.table_name, (user.vhost,))
        self.handler.bot.db.execute('UPDATE %s SET correct=? WHERE '
            'vhost=?' % self.table_name, (data['correct'] + 1, user.vhost))

    def add_incorrect(self, user):
        data = self.handler.bot.db.fetchone('SELECT * FROM %s WHERE '
            'vhost=?' % self.table_name, (user.vhost,))
        self.handler.bot.db.execute('UPDATE %s SET incorrect=? WHERE '
            'vhost=?' % self.table_name, (data['incorrect'] + 1, user.vhost))

    def end(self, winner):
        self.handler.bot.broadcast(
            '%s %s%s%s %s +%d $curr$' % (FORMAT, BOLD, winner.nick, RESET,
                random.choice(winning_alts), self.reward)
        )
        winner.add_points(self.reward)
        self.add_correct(winner)
        total_correct, percentage = self.handler.get_win_percent(winner,
            self.category)
        winner.message('You now have %d $curr$. You have correctly answered %d'
            ' %s questions (with %d%% success).' % (winner.points,
            total_correct, self.category, percentage))
        self.handler.end()

class TriviaRegular(TriviaBase):
    def __init__(self, handler, reward):
        TriviaBase.__init__(self, handler, reward)
        self.mode = 'regular'


def _message(bot, args):
    user, message = args

    global trivia_handler
    trivia_handler.guess(user, ' '.join(message))
