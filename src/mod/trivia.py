# -- coding: utf-8 --
"""
Oracle 3.0 IRC Bot

trivia2.py
"""

import random, os, time, traceback, operator
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
    trivia_handler = TriviaHandler(600, b)
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
    'won\'t be beaten!',
    'thinks they\'re the smartest person here.'
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
    'Man, you\'re terrible at this.',
    'That was so wrong that it hurt.',
    'Negatory brochacho.'
]

def trivia(bot, cmd):
    """!parent-command !r user
    !c new
        !d Ask a new trivia question
        !a <mode>
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
    !c repeat
        !d Repeat the last trivia question
        !r user
    !c enter
        !d Enter into the trivia challenge (if it is running)
        !r user
    !c stats
        !d Get personal trivia stats
        !a [category...]
        !r user
    """
    def new(bot, cmd):
        global trivia_handler
        trivia_handler.time_left = 2
        trivia_handler.end()

    def time(bot, cmd):
        global trivia_handler
        if trivia_handler.game is not None:
            if trivia_handler.game.mode in ['risky', 'hard']:
                m, s = divmod(trivia_handler.game.time, 60)
                cmd.output('%s %dm %ds left in the current round.' % (FORMAT, m,
                    s))
            elif trivia_handler.game.mode == 'challenge' \
                    and trivia_handler.game.stage == 'enter':
                m, s = divmod(trivia_handler.game.time, 60)
                cmd.output('%s %dm %ds left to enter the challange.' % (FORMAT,
                    m, s))
        m, s = divmod(trivia_handler.time_left, 60)
        cmd.output('%s Next round in %dm %ds.' % (FORMAT, m, s))

    def skip(bot, cmd):
        global trivia_handler

        if trivia_handler.game is None:
            cmd.output('%s There is no round to skip.' % FORMAT)
            return

        if trivia_handler.game.mode == 'challenge' \
                and not trivia_handler.game.stage == 'enter':
            cmd.output('%s You can\'t skip during an in-progress challenge '
                'round.' % FORMAT)
            return

        skip_time = trivia_handler.skip(cmd.user)
        if not skip_time:
            cmd.output('%s You\'ve already tried to skip this question.' %
                FORMAT)
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

    def stats(bot, cmd):
        global trivia_handler
        stats = trivia_handler.get_stats(cmd.user)
        msg = ['%s %s%s %s %s' % (FORMAT, BOLD, 'Category'.ljust(13),
            'Correct'.ljust(11), '%')]

        # User may want a specific category
        if not len(cmd.args) == 0:
            user_category = ' '.join(cmd.args).lower()
        else:
            user_category = ''

        # Save total for later, we want to output it last
        total = stats.pop('Total')

        for category, stat in stats.iteritems():
            if user_category in category.lower():
                msg.append('%s %s %s %s' % (FORMAT, category.ljust(16),
                    str(stat[0]).rjust(4), (str(stat[1]) + '%').rjust(5)))

        if len(msg) == 1:
            cmd.output('%s No category found for "%s"' % (FORMAT, user_category))
            return

        if not user_category in 'total':
            cmd.output(*msg)
            return

        # Ensure total is last
        msg.append('%s %s%s %s %s' % (FORMAT, BOLD, 'Total'.ljust(16),
            str(total[0]).rjust(4),
            (str(total[1]) + '%').rjust(5)))

        # Output lines to the user
        cmd.output(*msg)

    def enter(bot, cmd):
        global trivia_handler
        if trivia_handler.game is not None:
            if trivia_handler.game.mode == 'challenge':
                trivia_handler.game.enter(cmd.user)
            else:
                cmd.output('%s Current game is not a challenge.' % FORMAT)
        else:
            cmd.output('%s There is no game at the moment.' % FORMAT)

    def repeat(bot, cmd):
        global trivia_handler
        game = trivia_handler.game
        if game is not None:
            if game.mode == 'challenge' and not game.state == 'enter':
                cmd.output('%s A trivia challenge round is in progress.' %
                    FORMAT)
            else:
                game.broadcast()
        else:
            cmd.output('%s There is no game at the moment.' % FORMAT)

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
    !d Answer a trivia question. Can also use /msg $nick$ <answer...>
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
        # Need a separate list for categories as they are removed from
        # the questions dict when empty. This list will not change.
        self.categories = []
        self.load_questions()
        for category, _ in self.questions.iteritems():
            self.categories.append(category)
            table_name = self.cat_table(category)
            if not self.bot.db.table_exists(table_name):
                print '... Creating', table_name, 'table'
                self.bot.db.execute('CREATE TABLE %s(vhost TEXT, correct'
                    ' INT, incorrect INT)' % table_name, ())

    def cat_table(self, category):
        # Creates a database table name for the category, removing spaces
        # and quotation marks
        return 'trivia_' + category.replace(' ', '_').replace('\'', '')

    def get_stats(self, user):
        # Return trivia stats for the user
        # Returns dict, category: (num, percent) for all categories
        # and "total_correct": (num, percent)
        stats = {}
        total_correct = total_percentage = 0
        for category in self.categories:
            # Set an entry in the dict to the win percent tuple (num, percent)
            stats[category] = self.get_win_percent(user, category)
            # Add tuple to running sums of total_correct (num, percent_sum)
            total_correct += stats[category][0]
            total_percentage += stats[category][1]
        # Divide total_correct percent_sum by num of categories,
        # so it is now a total percent of questions correct
        stats['Total'] = (total_correct, int(total_percentage /
            len(self.categories)))
        return stats

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
        # List of all categories that need to be removed
        remove_categories = []
        for c, q in self.questions.iteritems():
            if len(q) == 0 or q is None:
                # Remove category completely when all questions have
                # been asked.
                remove_categories.append(c)
        for c in remove_categories:
            del self.questions[c]
        if len(self.questions) == 0:
            # Reload all questions when all categories have been used
            # i.e. all questions have been asked.
            self.load_questions()

    def skip(self, user):
        # Allow users to skip the current question.
        # First skip starts skip timer, further skips reduce by 1/2 or 60s
        if user.vhost not in self.skips:
            self.skips.append(user.vhost)
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
        if user.vhost not in self.kicks:
            self.kicks.append(user.vhost)
            time = random.randint(60, 720)
            self.time_left -= time
            self.time_left = max(0, self.time_left)
            return time
        return False

    def kill(self):
        # Allows us to kill the thread when restarting/reloading Oracle
        self.dead = True
        self.end()

    def guess(self, user, guess):
        # Check if there is currently a trivia question, passes
        # guess to game object
        if self.game is None:
            user.message('%s There\'s no trivia question at the moment.')
            return False
        else:
            return self.game.guess(user, guess.lower())

    def try_create_record(self, user, category):
        # Try to create a record for a user if it doesn't
        # already exist.
        table_name = self.cat_table(category)
        data = self.bot.db.fetchone('SELECT * FROM %s WHERE '
            'vhost=?' % table_name, (user.vhost,))
        if data is None:
            self.bot.db.execute('INSERT INTO %s VALUES(?, 0, 0)'
            % table_name, (user.vhost,))

    def add_points(self, user, points):
        user.add_points(points)

    def add_correct(self, user, category):
        table_name = self.cat_table(category)
        data = self.bot.db.fetchone('SELECT * FROM %s WHERE vhost=?'
            % table_name, (user.vhost,))
        self.bot.db.execute('UPDATE %s SET correct=? WHERE vhost=?'
            % table_name, (data['correct'] + 1, user.vhost))

    def add_incorrect(self, user, category):
        table_name = self.cat_table(category)
        data = self.bot.db.fetchone('SELECT * FROM %s WHERE vhost=?'
            % table_name, (user.vhost,))
        self.bot.db.execute('UPDATE %s SET incorrect=? WHERE vhost=?'
            % table_name, (data['incorrect'] + 1, user.vhost))

    def get_win_percent(self, user, category):
        try:
            table_name = self.cat_table(category)
            data = self.bot.db.fetchone('SELECT * FROM %s WHERE vhost=?'
                % table_name, (user.vhost,))
        except: # TODO: Find exception name
            # User not found in database, create and retry method
            traceback.print_exc()
            self.try_create_record(user, category)
            return self.get_win_percent(user, category)

        if data is None:
            return 0, 0
        if data['correct'] == 0:
            return 0, 0
        if data['incorrect'] == 0:
            return data['correct'], 100

        return data['correct'], int(100 * data['correct'] /
            (data['incorrect'] + data['correct']))

    def end(self):
        # Signify the end of a round
        # Delete trivia game object, reset skip
        # and user lists
        self.skip_time = 0
        self.kicks = []
        self.skips = []
        # Ensure sub threads are killed by setting time to 0
        if self.game is not None:
            self.game.time = 0
            self.game.dead = True
            self.game = None

    def run(self):
        # Threaded loop
        while not self.dead:
            while self.time_left > 0:
                if self.dead:
                    # Allows us to kill the thread during the countdown
                    return
                # Decrement time left, allows us to change/read time left
                # rather than just let the thread sleep the entire duration
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
            if rng > 0.75:
                # Start a challenge trivia
                self.game = TriviaChallenge(self, 500)
            elif rng > 0.5:
                # Start a hard trivia
                self.game = TriviaHard(self, 200)
            elif rng > 0.25:
                # Start a risk trivia
                self.game = TriviaRisk(self, 250)
            else:
                # Start a regular trivia
                self.game = Trivia(self, 100)
            self.game.broadcast()
            # self.game will run in it's own object until it calls
            # end() on both itself and this handler.
            self.time_left = self.interval
            time.sleep(2)


class Trivia(object):
    def __init__(self, handler, reward):
        self.handler = handler
        self.reward = reward
        self.category, self.question, self.answers = self.handler.get_question()
        self.table_name = self.handler.cat_table(self.category)
        self.mode = 'regular'
        self.time = 0
        self.dead = False

    def broadcast(self):
        self.handler.bot.broadcast('%s <%s: %s> %s (.help trivia)' % (FORMAT,
            self.category, self.mode, self.question))

    def guess(self, user, guess):
        # Make sure the user record for this category exists
        # first, otherwise there will be lots of errors down the line.
        self.handler.try_create_record(user, self.category)
            # Check if the guess is in the answers list
        if guess.lower() in self.answers:
            self.end(user)
            return True
        self.handler.add_incorrect(user, self.category)
        user.message('%s %s' % (FORMAT, random.choice(incorrect_alts)))
        return False

    def end(self, winner):
        self.handler.bot.broadcast(
            '%s %s%s%s %s +%d $curr$' % (FORMAT, BOLD, winner.nick, RESET,
                random.choice(winning_alts), self.reward)
        )
        self.handler.add_points(winner, self.reward)
        self.handler.add_correct(winner, self.category)
        total_correct, percentage = self.handler.get_win_percent(winner,
            self.category)
        winner.message('You now have %d $curr$. You have correctly answered %d'
            ' %s questions (with %d%% success).' % (winner.points,
            total_correct, self.category, percentage))
        self.handler.end()


class TriviaRisk(Trivia, Thread):
    def __init__(self, handler, reward):
        Thread.__init__(self)
        Trivia.__init__(self, handler, reward)
        self.mode = 'risky'
        self.cost = 50
        self.time = 120
        self.start()

    def broadcast(self):
        super(TriviaRisk, self).broadcast()
        # Broadcast a second message to tell cost and time remaining
        # Sleep to help allieviate incorrect orderings from threading
        time.sleep(0.5)
        m, s = divmod(self.time, 60)
        self.handler.bot.broadcast('%s %dm %ds remain. Costs %d $curr$ per '
            'guess.' % (FORMAT, m, s, self.cost))

    def guess(self, user, guess):
        if user.points < self.cost:
            user.message('%s You don\'t have enough points to guess for this '
                'question.' % FORMAT)
            return False
            self.handler.add_points(user, -self.reward)
        return super(TriviaRisk, self).guess(user, guess)

    def end(self, winner):
        if self.time > 0:
            super(TriviaRisk, self).end(winner)
        else:
            self.handler.bot.broadcast('%s Time\'s up! No winner this round.' %
                FORMAT)

    def run(self):
        while self.time > 0:
            self.time -= 2
            time.sleep(2)
        if not self.dead:
            self.end(None)


class TriviaHard(Trivia, Thread):
    def __init__(self, handler, reward):
        Thread.__init__(self)
        Trivia.__init__(self, handler, reward)
        self.mode = 'hard'
        self.time = 120
        self.guessers = []
        self.start()

    def broadcast(self):
        super(TriviaHard, self).broadcast()
        # Broadcast a second message to tell cost and time remaining
        # Sleep to help allieviate incorrect orderings from threading
        time.sleep(0.5)
        m, s = divmod(self.time, 60)
        self.handler.bot.broadcast('%s %dm %ds remain. One guess per player.'
            % (FORMAT, m, s))

    def guess(self, user, guess):
        if not user.vhost in self.guessers:
            self.guessers.append(user.vhost)
            return super(TriviaHard, self).guess(user, guess)
        else:
            user.message('%s You can only guess once in hard mode.' % FORMAT)
            return False

    def end(self, winner):
        if self.time > 0:
            super(TriviaHard, self).end(winner)
        else:
            self.handler.bot.broadcast('%s Time\'s up! No winner this round.' %
                FORMAT)

    def run(self):
        while self.time > 0:
            self.time -= 2
            time.sleep(2)
        if not self.dead:
            self.end(None)


class TriviaChallenge(Thread):
    # Not a child class of Trivia, as it works very differently
    # to any other mode of trivia.
    # It can still be called by the TriviaHandler (via commands),
    # so it is important it has the attribues 'time', 'guess()'
    def __init__(self, handler, reward):
        Thread.__init__(self)
        self.handler = handler
        self.reward = reward
        self.stage = 'enter'
        # Time is set to the initial time of the enter stage (2 mins)
        # it is used afterwards to time each question, so it can return
        # a value to .trivia time
        self.time = 120
        self.ans_time = 15
        self.num_qs = 5
        self.min_players = 2
        # Dict of user objects: amount correct
        # Using user objects so they can be messaged without
        # recreating them
        self.players = {}
        # Users are added to the winners list to prevent correctly
        # answering multiple times.
        # Reset after each question
        self.winners = []
        self.questions = []
        # Place 5 questions into list of tuples - (category, question, answers)
        for i in range(self.num_qs):
            self.questions.append(self.handler.get_question())

        self.mode = 'challenge'
        self.start()

    def broadcast(self):
        self.handler.bot.broadcast(
            '%s <%s> A trivia challenge round is about to start. Use %s.trivia '
            'enter%s to take part. (.help trivia)' % (FORMAT, self.mode, BOLD,
            RESET)
        )

    def enter(self, user):
        if self.stage == 'enter' and self.saved_user(user) is None:
            # Add player to dict
            self.players[user] = 0
            self.handler.bot.broadcast(
                '%s %s entered the Trivia Challenge. (.trivia help)' % (FORMAT,
                user.nick)
            )
            # Send challenge info to player
            m, s = divmod(self.time, 60)
            players_left = max(0, self.min_players - len(self.players))
            user.message(
                '%s The challenge will begin in %dm %ds%s' % (FORMAT, m, s,
                '.' if players_left == 0 else ' if %d more players enter.'
                % players_left),
                '%s When the challenge starts you will be sent questions via '
                'private message, and you are encouraged to reply privately '
                'too. You don\'t require .a in private messages.' % FORMAT,
                '%s You will have %d seconds after each question to answer '
                'before the next question is sent.' % (FORMAT, self.ans_time),
                '%s Whoever gets the most correct out of the %s questions wins.'
                ' Winnings will be split in the case of a tie.' % (FORMAT,
                self.num_qs),
                '%s First place: %s%d%s $curr$, second place: %s%d%s $curr$' %
                (FORMAT, BOLD, self.reward, RESET, BOLD, self.reward / 4, RESET)
            )
        else:
            user.message('%s Too late! Game already in progress.' % FORMAT)

    def ask_question(self):
        # Private message the question to all players.
        for player in self.players.keys():
            q = self.questions[self.stage]
            player.message('%s <%s: %s> %s You have %ds.' % (FORMAT, q[0],
                self.mode, q[1], self.ans_time))

    def saved_user(self, user):
        # Return true if user is in the players list
        for player in self.players.keys():
            if player.vhost == user.vhost:
                return player
        return None

    def guess(self, user, guess):
        # Make sure user is actually in the game
        if self.stage == 'enter':
            user.message('%s You can\'t answer yet.' % FORMAT)
            return
        if user.vhost in self.winners:
            # Make sure players can't answer more than once
            user.message('%s You already got it right, calm down.' % FORMAT)
            return

        player = self.saved_user(user)
        if player is not None:
            q = self.questions[self.stage]
            self.handler.try_create_record(user, q[0])
            # Check if phrase in q[3] -> answers list
            if guess in q[2]:
                # Guess is correct
                self.players[player] += 1
                # Append to winners, so they can't guess again
                self.winners.append(player.vhost)
                self.handler.add_correct(player, q[0])
                user.message('%s Correct!' % FORMAT)
            else:
                # Guess is incorrect
                self.handler.add_incorrect(player, q[0])
                user.message('%s %s' % (FORMAT, random.choice(incorrect_alts)))
        else:
            user.message('%s You aren\'t in the current trivia challenge.' %
                FORMAT)

    def end(self):
        # Winner is usually passed in, it is not necessary here

        out = []
        for player, score in self.players.iteritems():
            out.append(FORMAT + ' ' + player.nick + ': ' + str(score))

        # Sort the dict by values, place into list of tuples
        players = sorted(self.players.items(), key=operator.itemgetter(1))

        print players

        first_reward = self.reward
        second_reward = self.reward / 4

        first_ties = 0
        second_ties = 0

        # Check for ties
        for player in players[1:]:
            if players[0][1] == player[1]:
                first_ties += 1
        if first_ties == 0:
            for player in players[2:]:
                if players[1][1] == player[1]:
                    second_ties += 1

        if first_ties == 0:
            out.append('%s <challenge> First place: %s %d/%d correct. +%d '
                '$curr$' % (FORMAT, players[0][0].nick, players[0][1],
                self.num_qs, first_reward))
            self.handler.add_points(player[0][0], first_reward)
            players[0][0].message('You now have %d $curr$' %
                players[0][0].points)
            if second_ties == 0:
                out.append('%s <challenge> Second place: %s %d/%d correct. +%d '
                    '$curr$' % (FORMAT, players[1][0].nick, players[1][1],
                    self.num_qs, second_reward))
                self.handler.add_points(player[1][0], second_reward)
                players[1][0].message('You now have %d $curr$' %
                    players[1][0].points)
            else:
                second_reward = second_reward / (second_ties + 1)
                nicks = ''
                for player in players[1:second_ties]:
                    self.handler.add_points(player[0], second_reward)
                    player[0].message('You now have %d $curr$' %
                        player[0].points)
                    nicks = nicks + '%s, ' % player[0].nick
                out.append('%s <challenge> Second place was a tie between: %s'
                    'with %d/%d correct. +%d $curr$ each' % (FORMAT, nicks,
                    players[0][1], self.num_qs, first_reward))
        else:
            first_reward = (first_reward + second_reward) / (first_ties + 1)
            nicks = ''
            for player in players[:first_ties]:
                self.handler.add_points(player[0], first_reward)
                player[0].message('You now have %d $curr$' % player[0].points)
                nicks = nicks + '%s, ' % player[0].nick
            out.append('%s <challenge> First place was a tie between: %swith '
                '%d/%d correct. +%d $curr$ each' % (FORMAT, nicks,
                players[0][1], self.num_qs, first_reward))
        self.handler.bot.broadcast(*out)
        self.handler.end()

    def run(self):
        # Threaded loop
        # STAGE: enter
        while self.time > 0:
            self.time -= 2
            time.sleep(2)
        # After enter stage, check if there is enough players
        if len(self.players) < self.min_players:
            # Break out if not enough players, and use the handler
            # to start the next question
            self.handler.bot.broadcast('%s Not enough players to start the '
                'challenge.' % FORMAT)
            self.handler.end()
            self.handler.time_left = 2
            return
        # Run each question
        for i in range(self.num_qs):
            if self.handler.dead:
                return
            # Reset winners list, otherwise you could only
            # get one point
            self.winners = []
            self.stage = i
            self.ask_question()
            self.time = self.ans_time
            # Run timer
            while self.time > 0:
                self.time -= 1
                time.sleep(1)
        self.end()


def _message(bot, args):
    user, message = args

    # Process private messages to the bot as trivia
    # guesses.
    global trivia_handler
    trivia_handler.guess(user, ' '.join(message))
