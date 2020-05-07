"""
Redis consumer, runs on the robot.
"""
from signal import signal, SIGINT, SIGTERM, pause
import time
import redis
from tablet import Tablet


class TabletConsumer(object):
    """Receives commands from Redis and executes them on the tablet"""
    def __init__(self, server):
        self.tablet = Tablet(server)

        # Catch SIGINT/SIGTERM for cleanup purposes to stop threads
        signal(SIGINT, self.cleanup)
        signal(SIGTERM, self.cleanup)

        # The Redis channels on which the tablet can receive commands
        channels = [
            'tablet_control',
            'tablet_audio',
            'tablet_image',
            'tablet_video',
            'tablet_web',
        ]

        # Create the consumer on those channels
        self.redis = redis.Redis(host=server, ssl=True, ssl_ca_certs='../cert.pem')
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(**dict.fromkeys(channels, self.execute))
        self.pubsub_thread = self.pubsub.run_in_thread(sleep_time=0.001)

        # Set the base URI for web pages
        self.webcontent_uri = 'https://' + server + ':8000/index.html'

        self.running = True

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
            value = float(command.split(' ')[1])/100
            print 'setting volume to {}'.format(value)
            try:
                self.tablet.set_volume(value)
            except ValueError, exception:
                print 'error: ', exception.message
        else:
            print '!! Command not found.'

    # pylint: disable=too-many-branches, too-many-statements
    # We need this many if statements to handle the different types of commands.
    def execute(self, message):
        """Execute a single command. Format is documented on Confluence."""
        channel = message['channel']
        content = message['data']
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
        while self.running:
            pause()

    def cleanup(self, signum, frame):
        if self.running:
            self.running = False
            print('Trying to exit gracefully...')
            try:
                self.tablet.stop_audio()
                self.pubsub_thread.stop()
                self.redis.close()
                print('Graceful exit was successful.')
            except redis.RedisError as err:
                print('A graceful exit has failed due to: ' + err.message)


if __name__ == '__main__':
    import argparse

    PARSER = argparse.ArgumentParser()
    PARSER.add_argument('--server', type=str, required=True, help='Server IP address.')
    ARGS = PARSER.parse_args()

    print 'Receiving commands...'

    try:
        CONSUMER = TabletConsumer(ARGS.server)
        CONSUMER.run_forever()
    except RuntimeError:
        print 'No tablet available.'
