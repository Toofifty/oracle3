# -- coding: utf-8 --
"""
Oracle 3.0 IRC Bot

user.py
"""

import time

class User(object):
    # User class handles all current information
    # about a user, and a few helper methods

    def __init__(self, bot, vhost, nick, rank, points, cmd_count, seen=0):
        self.bot = bot

        self.vhost = vhost
        self.nick = nick

        self.rank = rank
        self.points = points
        self.cmd_count = cmd_count
        self.seen = seen
        if self.seen == 0:
            self.was_seen()

    def was_seen(self):
        self.seen = time.time()
        self.save()

    def part(self):
        self.was_seen()
        self.save()

    def get_rank(self):
        # Get rank as a string representation
        # For an int rank, use user.rank
        for rank, num in self.bot.ranks.iteritems():
            if num == self.rank:
                return rank

    def set_nick(self, nick):
        self.nick = nick
        self.save()

    def add_points(self, points):
        self.points += int(points)
        self.save()

    def set_points(self, points):
        self.points = int(points)
        self.save()

    def add_command(self):
        # Increment command count
        self.cmd_count += 1
        self.save()

    def set_rank(self, rank):
        # Set rank to an int or string found in bot.ranks
        try:
            # Use int rank
            rank = int(rank)
            if rank >= -1 and rank < len(self.bot.ranks) - 1:
                self.rank = rank
                self.save()
                return True

        except ValueError:
            # Accept string ranks
            if rank in self.bot.ranks:
                self.rank = self.bot.ranks[rank]
                self.save()
                return True

        print 'X-X Rank: %s was not recognised.' % rank
        return False

    def save(self):
        # Should be able to safely use UPDATE since
        # the bot will try to make a record for the user
        # when this object is created (and not already in the db)

        self.bot.db.execute('UPDATE users SET nick=?, seen=?, rank=?, points=?,'
            ' cmd_count=? WHERE vhost=?', (self.nick, self.seen, self.rank,
            self.points, self.cmd_count, self.vhost))
