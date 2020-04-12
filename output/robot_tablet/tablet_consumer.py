"""
Redis consumer, runs on the robot.
"""
import signal
import time
from json import dumps
from urllib import quote as urlquote

import redis

from tablet import Tablet

class TabletConsumer(object):
    """Receives commands from Redis and executes them on the tablet"""
    def __init__(self, server, redis_port, server_port):
        print 'Redis: {}:{}'.format(server, redis_port)
        print 'Web: {}:{}'.format(server, server_port)
        self.tablet = Tablet(server, server_port)

        # Catch SIGINT/SIGTERM for cleanup purposes to stop threads
        signal.signal(signal.SIGINT, self._exit_gracefully)
        signal.signal(signal.SIGTERM, self._exit_gracefully)

        # The Redis channels on which the tablet can receive commands
        channels = [
            'tablet_control',
            'tablet_audio',
            'tablet_image',
            'tablet_video',
            'tablet_web',
        ]
        print channels

        # Create the consumer on those channels
        self.redis = redis.Redis(host=server, port=redis_port)
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(*channels)

        # Set the base URI for web pages
        self.webcontent_uri = 'http://' + server + ':' + str(server_port) + '/index.html'

    # Handler should technically also have signum and frame as parameters, but we don't use that
    def _exit_gracefully(self, *_):
        print 'Exiting gracefully (ignore the runtime error from pubsub)'
        self.tablet.stop_audio()
        self.pubsub.close()

    def update(self):
        """Get a message and execute it"""
        msg = self.pubsub.get_message()
        if msg is not None:
            self.execute(msg['channel'], msg['data'])
        else:
            time.sleep(0)

    def tablet_control(self, command):
        """Misc commands to control the tablet"""
        if command == 'hide':
            self.tablet.hide()
        elif command == 'show':
            self.tablet.open_url(self.webcontent_uri)
        elif command == 'reload':
            self.tablet.reload()
        elif command == 'settings':
            self.tablet.settings()
        elif command.startswith('volume'):
            # Convert the percentage to a float between 0 and 1
            # The command sent to the channel is e.g. "volume 50"
            value = float(command.split(' ')[1]) / 100
            print 'setting volume to {}'.format(value)
            try:
                self.tablet.set_volume(value)
            except ValueError, exception:
                print 'error: ', exception.message
        else:
            print '!! Command not found.'

    # pylint: disable=too-many-branches, too-many-statements
    # We need this many if statements to handle the different types of commands.
    def execute(self, channel, content):
        """Execute a single command. Format is documented on Confluence."""
        print '[{}] {}'.format(channel, content)

        if channel == 'tablet_control':
            self.tablet_control(content)
        elif channel == 'tablet_image':
            self.tablet.show_image(content)
        elif channel == 'tablet_video':
            self.tablet.play_video(content)
        elif channel == 'tablet_web':
            self.tablet.open_url(content)
        elif channel == 'tablet_audio':
            # If the empty string is sent, stop all audio
            if not content:
                self.tablet.stop_audio()
            else:
                if self.tablet.audio_is_playing():
                    print 'could not play ', content, ' audio is already playing!'
                else:
                    self.tablet.play_audio(content)

    def run_forever(self):
        """Receive commands and execute them in 1 millisecond intervals"""
        try:
            while True:
                self.update()
        except KeyboardInterrupt:
            print 'Interrupted'
            self._exit_gracefully()

if __name__ == '__main__':
    import argparse

    PARSER = argparse.ArgumentParser()
    PARSER.add_argument('--server', type=str, required=True, help='Server IP address.')
    PARSER.add_argument('--redis-port', dest='redis_port', nargs='?', default=6379)
    PARSER.add_argument('--server-port', dest='server_port', nargs='?', default=8000)
    ARGS = PARSER.parse_args()

    print 'Receiving commands...'

    CONSUMER = TabletConsumer(ARGS.server, ARGS.redis_port, ARGS.server_port)
    CONSUMER.run_forever()