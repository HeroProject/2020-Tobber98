import threading
from signal import signal, SIGTERM, SIGINT, pause

import numpy as np
import imutils
import cv2
from PIL import Image
import time
import argparse
import redis
import face_recognition


class PeopleDetectionService:

    def __init__(self, server, ssl=True, debug=False):
        # Redis initialization
        self.redis = redis.Redis(host=server, ssl=ssl, ssl_ca_certs='../cert.pem')
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(**{'action_video': self.execute,
                                 'image_available': self.set_image_available,
                                 'action_take_picture': self.take_picture})
        self.pubsub_thread = self.pubsub.run_in_thread(sleep_time=0.001)

        # Debug mode on/off
        self.debug = debug

        # Register cleanup handlers
        signal(SIGTERM, self.cleanup)
        signal(SIGINT, self.cleanup)

        # Image size
        self.image_width = 0
        self.image_height = 0

        # Thread data
        self.people_detection_thread = None
        self.is_detecting = False
        self.save_image = False
        self.is_image_available = False
        self.image_available_flag = threading.Event()

        # Service is running
        self.running = True

    def execute(self, message):
        data = message['data']
        if data == 'start watching':
            if not self.is_detecting:
                self.is_detecting = True
                self.people_detection_thread = threading.Thread(target=self.detect_people)
                self.people_detection_thread.start()
            else:
                print("People already running")
        elif data == 'stop watching':
            if self.is_detecting:
                self.is_detecting = False
                self.people_detection_thread.join()
            else:
                print("People already stopped")
        else:
            print("Command not recognized: " + data)

    def detect_people(self):
        while self.is_detecting:
            if self.is_image_available:
                self.is_image_available = False
                image_stream = self.redis.get('image_stream')

                if self.image_width == 0:
                    image_size_string = self.redis.get('image_size')
                    self.image_width = int(image_size_string[0:4])
                    self.image_height = int(image_size_string[4:])

                # Create a PIL Image from byte string from redis result
                image = Image.frombytes('RGB', (self.image_width, self.image_height), image_stream)

                if self.save_image:
                    image_name = time.strftime('%Y%m%d-%H%M%S') + '.jpg'
                    image.save('../webserver/html/img/' + image_name)
                    self.redis.publish('picture_newfile', image_name)
                    self.save_image = False

                ima = np.asarray(image, dtype=np.uint8)
                image_res = imutils.resize(ima, width=min(self.image_width, ima.shape[1]))
                process_image = cv2.cvtColor(image_res, cv2.COLOR_BGRA2RGB)

                # TODO distance metrics
                faces = self.detect_face(process_image)

                if faces:
                    if self.debug:
                        print('detected_person')
                    self.redis.publish('detected_person', '')

                if self.debug:
                    if len(faces) > 0:
                        self.draw_faces(process_image, faces)

                    cv2.imshow('Detected person', process_image)

                    cv2.waitKey(10)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        cv2.destroyAllWindows()
            else:
                self.image_available_flag.wait()

    def set_image_available(self, message):
        if not self.is_image_available:
            self.is_image_available = True
            self.image_available_flag.set()


    def take_picture(self, message):
        self.save_image = True

    @staticmethod
    def detect_face(frame):
        '''
        detect human faces in image using haar-cascade
        Args:
            frame:
        '''
        return face_recognition.face_locations(frame)

    @staticmethod
    def draw_faces(frame, faces):
        '''
        draw rectangle around detected faces
        Args:
            frame:
            faces:
        '''
        for (top, right, bottom, left) in faces:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            cv2.rectangle(frame, (left, bottom - 1), (right, bottom), (0, 0, 255), cv2.FILLED)

    def run(self):
        while self.running:
            pause()

    def cleanup(self, signum, frame):
        if self.running:
            self.running = False
            print('Trying to exit gracefully...')
            try:
                if self.is_detecting:
                    self.is_detecting = False
                    self.people_detection_thread.join()
                self.pubsub_thread.stop()
                self.redis.close()
                print('Graceful exit was successful.')
            except redis.RedisError as err:
                print('A graceful exit has failed due to: ' + err.message)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', type=str, default='localhost', help='Server IP address. Default is localhost.')
    parser.add_argument('--no-ssl', action='store_true', default=False, help='Use this flag to disable the use of SSL.')
    parser.add_argument('--debug', action='store_true', default=False, help='Use this flag to enable several debug statements and drawings.')
    args = parser.parse_args()

    people_detection_service = PeopleDetectionService(args.server, not args.no_ssl, args.debug)
    people_detection_service.run()
