# -- coding: utf-8 --
"""
Oracle 3.0 IRC Bot

irc.py
"""

import socket, sys, traceback, time, thread

class IRC(socket.socket):
    # Outgoing actions class
    # Main interface to server from bot

    def __init__(self, ident, channels, host, port, nick, password=None):
        # Initialize the socket, set initial variables

        socket.socket.__init__(self)

        self.ident = ident
        self.channels = channels
        self.host = host
        self.port = port
        self.nick = nick
        self.password = password
        self.verbose = False
        self.connected = False

    def set_verbose(self, verbose):
        # Set verbose to true or false.

        if isinstance(verbose, bool):
            self.verbose = verbose
        else:
            raise TypeError('Tried to set verbose to non-bool')

    def set_nick(self, nick):
        # Set the nick of the bot

        self.nick = nick
        return self._send('NICK %s' % nick) > 0

    def connect(self):
        # Initial connection process with the IRC server

        try:
            # Connect with the super socket class
            super(IRC, self).connect((self.host, self.port))

            # Send initial bot info
            self.set_nick(self.nick)
            self._send('USER %s %s %s :Toofifty\'s Oracle bot' % (self.ident,
                self.host, self.nick))
            self.connected = True

        except Exception:
            # TODO: Catch more specific exceptions when they happen
            traceback.print_exc()
            print '-X- There was an error connecting to the server.'
            print '-X- Trying again in 30 seconds...'
            time.sleep(30)
            self.connect()

    ## Single threaded methods - do not call ##
    ## These are all called by their multi-threaded
    ## counterparts.

    def _send(self, message):
        # Send the text required through the super class
        # after logging and applying \r\n characters.
        # Should not be called. Instead, use notice, privmsg, etc

        if self.verbose:
            print '<--', message.rstrip()

        return self.send(message + '\r\n')

    def _join_channel(self, channel):
        # Join a channel, and add it to current channels

        if not '#' in channel:
            channel = '#' + channel

        self._send('JOIN %s' % channel)
        if not channel in self.channels:
            self.channels.append(channel)

    def _join_channels(self, channels):
        # Join a list of channels at once

        return not any(
            [self._join_channel(channel) for channel in channels]
        )

    def _notice(self, nick, message):
        # Send a private message to a user without getting their
        # client to open a new window.

        return self._send('NOTICE %s :%s' % (nick, message)) > 0

    def _notice_many(self, nick, *messages):
        # Send many private messages, passed in as a list
        # Used to aid in threading

        return not any(
            [not self._notice(nick, message) for message in messages]
        )

    def _privmsg(self, receiver, message):
        # Send a message to a user or channel

        return self._send('PRIVMSG %s :%s' % (receiver, message)) > 0

    def _privmsg_many(self, receiver, *messages):
        # Send many regular messages, passed in as a list
        # Used to aid in threading

        return not any(
            [not self._privmsg(receiver, message) for message in messages]
        )

    def _broadcast(self, message):
        # Broadcasts the message to all connected channels.
        # Return true if all messages were sent

        return not any(
            [not self._privmsg(channel, message) for channel in self.channels]
        )

    def _broadcast_many(self, *messages):
        # Send many regular messages, passed in as a list
        # Used to aid in threading

        return not any(
            [not self._broadcast(message) for message in messages]
        )

    def _ping(self, ping_id):
        # Replies to a ping event.
        return self._send('PONG %s' % str(ping_id)) > 0

    def _whois(self, nick):
        # Send a WHOIS request to the server
        # Returns true if sent

        return self._send('WHOIS %s' % nick) > 0

    def _kick(self, nick, channel):
        # Tries to kick a user from the channel
        # Will try all channels if no channel is given
        # Returns true if sent

        if channel is None:
            return not any(
                [self._send('KICK %s %s' % (channel, nick)) <= 0
                    for channel in self.channels]
            )
        else:
            return self._send('KICK %s %s' % (channel, nick)) > 0

    ## Multi-threaded methods - call these ##
    ## These ensure all slow outgoing messages are in
    ## their own temporary thread, to prevent lag when
    ## sending 10+ messages at once

    def join_channel(self, channel):
        thread.start_new_thread(self._join_channel, (channel,))

    def join_channels(self, channels):
        thread.start_new_thread(self._join_channels, (channels,))

    def notice(self, nick, *message):
        if len(message) > 1:
            thread.start_new_thread(self._notice_many, (nick,) + message)
        elif len(message) > 0:
            thread.start_new_thread(self._notice, (nick, message[0]))

    def privmsg(self, receiver, *message):
        if len(message) > 1:
            thread.start_new_thread(self._privmsg_many, (receiver,) + message)
        elif len(message) > 0:
            thread.start_new_thread(self._privmsg, (receiver, message[0]))

    def broadcast(self, *message):
        if len(message) > 1:
            thread.start_new_thread(self._broadcast_many, message)
        elif len(message) > 0:
            thread.start_new_thread(self._broadcast, (message[0],))

    def ping(self, ping_id):
        thread.start_new_thread(self._ping, (ping_id,))

    def whois(self, nick):
        thread.start_new_thread(self._whois, (nick,))

    def kick(self, nick, channel=None):
        thread.start_new_thread(self._kick, (nick, channel))

    ## End multi-threaded methods ##

    def disconnect(self):
        # Disconnect from the IRC server

        self.connected = False
        return self._send('QUIT') > 0

    def stop(self):
        # This kills the bot

        self.disconnect()
        sys.exit()

    def process(self, raw_message):
        # ~abstract~ method :-)
        return True

    def run(self):
        # Main IRC interaction loop
        # Get incoming data, saves to the buffer,
        # then splits and processes each line

        readbuffer = ''

        while self.connected:
            try:
                # Read 2048 bytes into the buffer
                readbuffer += self.recv(2048)
                # Split newlines
                temp = readbuffer.split('\n')
                # Place last bits back into readbuffer
                readbuffer = temp.pop()

                for line in temp:
                    # Process each raw message
                    raw_message = line.rstrip().split()
                    self.process(raw_message)

                time.sleep(0.5)

            except KeyboardInterrupt:
                self.plugins.destroy_mods(self)
                raise

            except SystemExit:
                self.plugins.destroy_mods(self)
                raise

            except Exception:
                print '-X- Fatal exception was caught:'
                traceback.print_exc()
