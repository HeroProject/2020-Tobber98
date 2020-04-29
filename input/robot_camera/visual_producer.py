import argparse
import time
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
        self.resolution = resolution
        self.colorspace = colorspace
        self.frame_ps = frame_ps

        # Get the service ALVideoDevice
        self.video_service = session.service('ALVideoDevice')
        self.module_name = 'VideoProcessingModule'

        self.redis = redis.Redis(host=server, ssl=True, ssl_ca_certs='../cert.pem')
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe('action_video')

        self.frame = 0
        possible_resolutions = {'0':[160,120],'1':[320,240],'2':[640,480],'3':[1280,960],'4':[2560,1920],'7':[80,60],'8':[40,30]}
        if str(resolution) in possible_resolutions.keys():
            self.redis.set('image_size', str(possible_resolutions[str(resolution)][0])+' '+str(possible_resolutions[str(resolution)][1]))

    def update(self):
        msg = self.pubsub.get_message()
        if msg is not None:
            self.execute(msg)
        else:
            time.sleep(0.001)

    def execute(self, message):
        data = message['data'] # only subscribed to 1 topic
        if data == 'start watching':
            self.is_robot_watching = True
            self.watch()
        elif data == 'stop watching':
            self.is_robot_watching = False
        else:
            print 'unknown command:', message.value()

    def run_forever(self):
        try:
            while True:
                self.update()
        except KeyboardInterrupt:
            print 'Interrupted'
            self.pubsub.close()

    def watch(self):
        # subscribe to the module (top camera)
        subscriberID = self.video_service.subscribeCamera(self.module_name, 0, self.resolution, self.colorspace, self.frame_ps)
        print 'subscribed, watching...'

        # start a loop until the stop signal is received
        while self.is_robot_watching:
            naoImage = self.video_service.getImageRemote(subscriberID)
            if naoImage is None:
                print 'no image'
            else:
                #timestamp1 = time.time()
                self.redis.mset({'image_stream': bytes(naoImage[6]), 'image_frame': str(self.frame)})
                self.frame += 1
                #timestamp2 = time.time()
                #print 'set image ', naoImage[4], ' took: ', (timestamp2-timestamp1)
            # try to consume 'stop watching', which sets self.is_robot_watching to False
            self.update()

        # unsubscribe from the module
        print '"stop watching" received, unsubscribing...'
        self.video_service.unsubscribe(subscriberID)

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

    MyVideoProcessingModule = VideoProcessingModule(app = app, server = args.server, resolution = args.resolution, colorspace = args.colorspace, frame_ps = args.frame_ps)
    app.session.registerService('VideoProcessingModule', MyVideoProcessingModule)

    MyVideoProcessingModule.run_forever()
