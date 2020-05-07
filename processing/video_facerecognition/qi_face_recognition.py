import threading
from signal import signal, SIGTERM, SIGINT, pause
import numpy as np
import argparse
import time
import os
from PIL import Image
import cv2
import face_recognition
from imutils.video import FPS
import pickle as pkl
import redis


class FaceRecognitionService:

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

        # Initialize face recognition data
        self.fps = FPS().start()
        self.face_labels = []
        self.face_names = []
        self.face_count = []

        self.face_encoding_path = 'face_encodings.p'
        if os.path.isfile(self.face_encoding_path):
            self.face_encodings_list = pkl.load(open(self.face_encoding_path, 'rb'))
            if self.debug:
                print('loading encodings', 'Length encoding ', len(self.face_encodings_list))

        # Create a difference between background and foreground image
        self.fgbg = cv2.createBackgroundSubtractorMOG2()

        # Register cleanup handlers
        signal(SIGTERM, self.cleanup)
        signal(SIGINT, self.cleanup)

        # Image size
        self.image_width = 0
        self.image_height = 0

        # Thread data
        self.face_recognition_thread = None
        self.is_recognizing = False
        self.save_image = False
        self.is_image_available = False
        self.image_available_flag = threading.Event()

        # Service is running
        self.running = True

    def execute(self, message):
        data = message['data']
        if data == 'start watching':
            if not self.is_recognizing:
                self.is_recognizing = True
                self.face_recognition_thread = threading.Thread(target=self.recognize_face)
                self.face_recognition_thread.start()
            else:
                print("Face recognition already running")
        elif data == 'stop watching':
            if self.is_recognizing:
                self.is_recognizing = False
                self.face_recognition_thread.join()
            else:
                print("Face recognition already stopped")
        else:
            print("Command not recognized: " + data)

    def recognize_face(self):
        while self.is_recognizing:
            if self.is_image_available:
                self.is_image_available = False
                image_stream = self.redis.get('image_stream')

                if self.image_width == 0:
                    image_size_string = self.redis.get('image_size')
                    self.image_width = int(image_size_string[0:4])
                    self.image_height = int(image_size_string[4:])

                # Create a PIL Image from byte string from redis result
                image = Image.frombytes('RGB', (self.image_width, self.image_height), image_stream)

                # If image needs to be saved, save it to the webserver
                if self.save_image:
                    img = time.strftime('%Y%m%d-%H%M%S') + '.jpg'
                    image.save('../webserver/html/img/' + img)
                    self.redis.publish('picture_newfile', img)
                    self.save_image = False

                # Create processable image
                cv_image = cv2.cvtColor(np.asarray(image, dtype=np.uint8), cv2.COLOR_BGRA2RGB)
                process_image = cv_image[:, :, ::-1]

                # Manipulate process_image in order to help face recognition
                # self.normalise_luminescence(process_image)
                self.fgbg.apply(process_image)

                face_locations = face_recognition.face_locations(process_image, model='hog')
                face_encodings = face_recognition.face_encodings(process_image, face_locations)
                face_name = []

                for face_encoding in face_encodings:
                    match = face_recognition.compare_faces(self.face_encodings_list, face_encoding, tolerance=0.6)
                    dist = face_recognition.face_distance(self.face_encodings_list, face_encoding)

                    if all(values == False for values in match) and all([d for d in dist if d > 0.7]):
                        if self.debug:
                            print('New Person')

                        count = len(self.face_encodings_list) if len(self.face_encodings_list) > 0 else 0
                        name = str(count)
                        self.face_count.append(count)
                        self.face_encodings_list.append(face_encoding)
                        self.face_names.append(name)
                        pkl.dump(self.face_encodings_list, open(self.face_encoding_path, 'wb'))

                    else:
                        index = match.index(True)
                        tmp = str(index)
                        if self.debug:
                            print('Not consistent match with compare faces and euclidean distance \n')
                            # print('NAME ', name, 'ArgMin ', np.argmin(dist), 'Count ', count)

                        if index == np.argmin(dist):
                            name = tmp
                            face_name.append(name)
                            if self.debug:
                                print('Person already recognised and consistent \n')
                                print('NAME ', name, 'ArgMin ', np.argmin(dist))
                        else:
                            if self.debug:
                                print('Mismatch in face recognition')
                            continue

                    self.redis.publish('recognised_face', name)

                    if self.debug:
                        for (top, right, bottom, left), name in zip(face_locations, face_name):
                            cv2.rectangle(cv_image, (left, top), (right, bottom), (0, 0, 255), 2)
                            cv2.rectangle(cv_image, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                            font = cv2.FONT_HERSHEY_DUPLEX
                            cv2.putText(cv_image, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

                        cv2.namedWindow('Camera', cv2.WINDOW_NORMAL)
                        cv2.imshow('Camera', cv_image)
                        self.fps.update()
                        cv2.waitKey(25)
                        key = cv2.waitKey(1) & 0xFF
                        if key == ord('q'):
                            break

                        print('Elapsed time : {:.2f}'.format(self.fps.elapsed()))
                        print('Approximate FPS: {:.2f}'.format(self.fps.fps()))
                else:
                    self.image_available_flag.wait()

    def set_image_available(self, message):
        if not self.is_image_available:
            self.is_image_available = True
            self.image_available_flag.set()

    def take_picture(self, message):
        self.save_image = True

    @staticmethod
    def normalise_luminescence(image, gamma=2.5):
        # build a lookup table mapping the pixel values [0, 255] to
        # their adjusted gamma values such that any image has the same luminescence
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255
                          for i in np.arange(0, 256)]).astype('uint8')

        # apply gamma correction using the lookup table
        return cv2.LUT(image, table, image)

    def run(self):
        while self.running:
            pause()

    def cleanup(self, signum, frame):
        if self.running:
            self.running = False
            print('Trying to exit gracefully...')
            try:
                if self.is_recognizing:
                    self.is_recognizing = False
                    self.face_recognition_thread.join()
                self.pubsub_thread.stop()
                self.redis.close()
                self.fps.stop()
                print('Graceful exit was successful.')
            except redis.RedisError as err:
                print('A graceful exit has failed due to: ' + err.message)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', type=str, default='localhost', help='Server IP address. Default is localhost.')
    parser.add_argument('--no-ssl', action='store_true', default=False, help='Use this flag to disable the use of SSL.')
    parser.add_argument('--debug', action='store_true', default=False, help='Use this flag to enable several debug statements and drawings.')
    args = parser.parse_args()

    face_recognition_service = FaceRecognitionService(args.server, not args.no_ssl, args.debug)
    face_recognition_service.run()
