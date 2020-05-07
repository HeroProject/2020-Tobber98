import argparse
import sys
import time
from signal import signal, SIGTERM, SIGINT, pause

import redis
import qi


class SoundProcessingModule(object):
    def __init__(self, app, server):
        """
        Initialise services and variables.
        """
        super(SoundProcessingModule, self).__init__()
        app.start()
        session = app.session

        # Get the service
        self.audio_service = session.service('ALAudioDevice')
        # self.audio_service.enableEnergyComputation()
        self.module_name = 'SoundProcessingModule'

        self.redis = redis.Redis(host=server, ssl=True, ssl_ca_certs='../cert.pem')
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(**{'action_audio': self.execute})
        self.pubsub_thread = self.pubsub.run_in_thread(sleep_time=0.001)

        # Register cleanup handlers
        signal(SIGTERM, self.cleanup)
        signal(SIGINT, self.cleanup)

        self.is_robot_listening = False
        self.running = True

    def execute(self, message):
        data = message['data']  # only subscribed to 1 topic
        if data == 'start listening':
            if self.is_robot_listening:
                print('already listening!')
            else:
                self.start_listening()
        elif data == 'stop listening':
            if self.is_robot_listening:
                self.stop_listening()
            else:
                print('was not listening anyway...')
        else:
            print ('unknown command: ' + message.value())

    def run_forever(self):
        while self.running:
            pause()

    def cleanup(self, signum, frame):
        if self.running:
            if self.is_robot_listening:
                self.stop_listening()
            self.running = False
            print('Trying to exit gracefully...')
            try:
                self.pubsub_thread.stop()
                self.redis.close()
                print('Graceful exit was successful.')
            except redis.RedisError as err:
                print('A graceful exit has failed due to: ' + err.message)

    def start_listening(self):
        self.is_robot_listening = True

        # clear any previously stored audio
        self.redis.delete('audio_stream')

        # ask for the front microphone signal sampled at 16kHz and subscribe to the module
        self.audio_service.setClientPreferences(self.module_name, 16000, 3, 0)
        self.audio_service.subscribe(self.module_name)
        print 'subscribed, listening...'

    def stop_listening(self):
        self.is_robot_listening = False
        # unsubscribe from the module
        print '"stop listening" received, unsubscribing...'
        self.audio_service.unsubscribe(self.module_name)

    def processRemote(self, nbOfChannels, nbOfSamplesByChannel, timeStamp, inputBuffer):
        self.redis.rpush('audio_stream', bytes(inputBuffer))
        # self.pubsub.publish('audio_level', self.audio_service.getFrontMicEnergy())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', type=str, default='localhost', help='Server IP address. Default is localhost.')
    args = parser.parse_args()

    try:
        app = qi.Application(['SoundProcessing', '--qi-url=tcp://127.0.0.1:9559'])
    except RuntimeError:
        print ('Cannot connect to Naoqi')
        sys.exit(1)

    MySoundProcessingModule = SoundProcessingModule(app=app, server=args.server)
    app.session.registerService('SoundProcessingModule', MySoundProcessingModule)

    MySoundProcessingModule.run_forever()
