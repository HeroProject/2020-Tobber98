import argparse
import sys
import time
from signal import signal, SIGTERM, SIGINT
from threading import Thread

import redis
import qi


class VideoProcessingModule(object):
    def __init__(self, app, server, resolution, colorspace, frame_ps):
        """
        Initialise services and variables.
        """
        super(VideoProcessingModule, self).__init__()
        app.start()
        session = app.session
        self.colorspace = colorspace
        self.frame_ps = frame_ps
        # The watching thread will poll the camera 2 times the frame rate to make sure it is not the bottleneck.
        self.polling_sleep = 1 / (self.frame_ps * 2)

        # Get the service ALVideoDevice
        self.video_service = session.service('ALVideoDevice')
        self.module_name = 'VideoProcessingModule'

        self.redis = redis.Redis(host=server, ssl=True, ssl_ca_certs='../cert.pem')
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(**{'action_video': self.execute})
        self.pubsub_thread = self.pubsub.run_in_thread(sleep_time=0.001)

        possible_resolutions = {'0': [160, 120], '1': [320, 240], '2': [640, 480], '3': [1280, 960],
                                '4': [2560, 1920], '7': [80, 60], '8': [40, 30]}

        if str(resolution) in possible_resolutions.keys():
            self.resolution = resolution
            self.redis.set('image_size', str(possible_resolutions[str(resolution)][0]) + ' ' + str(
                possible_resolutions[str(resolution)][1]))
        else:
            raise ValueError(str(resolution) + " is not a valid resolution")

        # Register cleanup handlers
        signal(SIGTERM, self.cleanup)
        signal(SIGINT, self.cleanup)

        self.is_robot_watching = False
        self.subscriber_id = None
        self.watching_thread = None
        self.running = True

    def execute(self, message):
        data = message['data']  # only subscribed to 1 topic
        if data == 'start watching':
            if self.is_robot_watching:
                print('Robot is already watching')
            else:
                self.start_watching()
        elif data == 'stop watching':
            if self.is_robot_watching:
                self.stop_watching()
            else:
                print('Robot already stopped watching')
        else:
            print('unknown command: ' + message.value())

    def run_forever(self):
        print('Video producer started')
        while self.running:
            time.sleep(0.1)

    def cleanup(self, signum, frame):
        if self.running:
            if self.is_robot_watching:
                self.stop_watching()
            self.running = False
            print('Trying to exit gracefully...')
            try:
                self.pubsub_thread.stop()
                self.redis.close()
                print('Graceful exit was successful.')
            except redis.RedisError as err:
                print('A graceful exit has failed due to: ' + err.message)

    def start_watching(self):
        # subscribe to the module (top camera)
        print('Start watching received, subscribing...')
        self.is_robot_watching = True
        self.subscriber_id = self.video_service.subscribeCamera(self.module_name, 0, self.resolution,
                                                                self.colorspace, self.frame_ps)
        print('Subscribed, start watching thread...')
        self.watching_thread = Thread(target=self.watching, args=[self.subscriber_id])
        self.watching_thread.start()

    def stop_watching(self):
        # unsubscribe from the module
        print('Stop watching received, stopping watching thread...')
        self.is_robot_watching = False
        self.watching_thread.join()
        print('Watching thread stopped. Unsubscribing...')
        self.video_service.unsubscribe(self.subscriber_id)
        print('Unsubscribed.')

    def watching(self, subscriber_id):
        # start a loop until the stop signal is received
        while self.is_robot_watching:
            nao_image = self.video_service.getImageRemote(subscriber_id)
            if nao_image is None:
                print('no image')
            else:
                pipe = self.redis.pipeline()
                pipe.set('image_stream', bytes(nao_image[6]))
                pipe.publish('image_available', '')
                pipe.execute()

            time.sleep(self.polling_sleep)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', type=str, default='localhost', help='Server IP address. Default is localhost.')
    parser.add_argument('--resolution', type=int, default=2, help='Naoqi image resolution.')
    parser.add_argument('--colorspace', type=int, default=11, help='Naoqi color channel.')
    parser.add_argument('--frame_ps', type=int, default=20, help='Framerate at which images are generated.')
    args = parser.parse_args()

    try:
        app = qi.Application(['VideoProcessing', '--qi-url=tcp://127.0.0.1:9559'])
    except RuntimeError:
        print ('Cannot connect to Naoqi')
        sys.exit(1)

    MyVideoProcessingModule = VideoProcessingModule(app=app, server=args.server, resolution=args.resolution,
                                                    colorspace=args.colorspace, frame_ps=args.frame_ps)
    app.session.registerService('VideoProcessingModule', MyVideoProcessingModule)
    MyVideoProcessingModule.run_forever()
