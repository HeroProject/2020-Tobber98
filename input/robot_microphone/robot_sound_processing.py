import argparse
import time
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
        #self.audio_service.enableEnergyComputation()
        self.module_name = 'SoundProcessingModule'

        self.redis = redis.Redis(host=server)
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe('action_audio')

        self.is_robot_listening = False

    def update(self):
        msg = self.pubsub.get_message()
        if msg is not None:
            self.execute(msg)
        else:
            time.sleep(0)

    def execute(self, message):
        data = message['data'] # only subscribed to 1 topic
        if data == 'start listening':
            if self.is_robot_listening:
                print 'already listening!'
            else:
                self.is_robot_listening = True
                self.listen()
        elif data == 'stop listening':
            if self.is_robot_listening:
                self.is_robot_listening = False
            else:
                print 'was not listening anyway...'
        else:
            print 'unknown command:', message.value()

    def run_forever(self):
        try:
            while True:
                self.update()
        except KeyboardInterrupt:
            print 'Interrupted'
            self.pubsub.close()

    def listen(self):
        # clear any previously stored audio
        self.redis.delete('audio_stream')

        # ask for the front microphone signal sampled at 16kHz and subscribe to the module
        self.audio_service.setClientPreferences(self.module_name, 16000, 3, 0)
        self.audio_service.subscribe(self.module_name)
        print 'subscribed, listening...'

        # start a loop until the stop signal is received
        # the audio_service calls processRemote which actually produces the audio
        while self.is_robot_listening:
            # try to consume 'stop listening', which sets self.is_robot_listening to False
            self.update()

        # unsubscribe from the module
        print '"stop listening" received, unsubscribing...'
        self.audio_service.unsubscribe(self.module_name)

    def processRemote(self, nbOfChannels, nbOfSamplesByChannel, timeStamp, inputBuffer):
        self.redis.rpush('audio_stream', bytes(inputBuffer))
        #self.pubsub.publish('audio_level', self.audio_service.getFrontMicEnergy())

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', type=str, default='localhost', help='Server IP address. Default is localhost.')
    args = parser.parse_args()

    try:
        app = qi.Application(['SoundProcessing', '--qi-url=tcp://127.0.0.1:9559'])
    except RuntimeError:
        print ('Cannot connect to Naoqi')
        sys.exit(1)

    MySoundProcessingModule = SoundProcessingModule(app = app, server = args.server)
    app.session.registerService('SoundProcessingModule', MySoundProcessingModule)

    MySoundProcessingModule.run_forever()