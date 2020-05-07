''' All Credits goes to https://github.com/vjgpt/Face-and-Emotion-Recognition '''
import threading
from signal import signal, SIGTERM, SIGINT, pause

import cv2
import numpy as np
import dlib
from imutils import face_utils
from statistics import mode

# direct import from keras has a bug see: https://stackoverflow.com/a/59810484/3668659
from tensorflow.python.keras.models import load_model

from utils.datasets import get_labels
from utils.inference import apply_offsets
from utils.preprocessor import preprocess_input
import argparse
import redis
import imutils
import time
from PIL import Image


class EmotionDetectionService:

    def __init__(self, server, ssl=True):
        # Redis initialization
        self.redis = redis.Redis(host=server, ssl=ssl, ssl_ca_certs='../cert.pem')
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(**{'action_video': self.execute,
                                 'image_available': self.set_image_available})
        self.pubsub_thread = self.pubsub.run_in_thread(sleep_time=0.001)

        # Register cleanup handlers
        signal(SIGTERM, self.cleanup)
        signal(SIGINT, self.cleanup)

        # TO SET CORRECTLY
        self.emotion_model_path = 'emotion_model.hdf5'
        self.emotion_labels = get_labels('fer2013')

        # hyper-parameters for bounding boxes shape
        self.frame_window = 10
        self.emotion_offsets = (20, 40)

        # loading models
        # tb._SYMBOLIC_SCOPE.value = True
        self.detector = dlib.get_frontal_face_detector()
        self.emotion_classifier = load_model(self.emotion_model_path)

        # getting input model shapes for inference
        self.emotion_target_size = self.emotion_classifier.input_shape[1:3]

        # Image size
        self.image_width = 0
        self.image_height = 0

        # Thread data
        self.emotion_detection_thread = None
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
                self.emotion_detection_thread = threading.Thread(target=self.detect_emotion)
                self.emotion_detection_thread.start()
            else:
                print("People already running")
        elif data == 'stop watching':
            if self.is_detecting:
                self.is_detecting = False
                self.emotion_detection_thread.join()
            else:
                print("People already stopped")
        else:
            print("Command not recognized: " + data)

    def detect_emotion(self):
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
                ima = np.asarray(image, dtype=np.uint8)
                frame = imutils.resize(ima, width=min(self.image_width, ima.shape[1]))

                # starting lists for calculating modes
                # this is because you wanna look at "average" emotion within some time window (aka number of frames), i.e., the mode,
                # because the method is not 100% accurate for every single frame.
                # E.g., for a time window of 5 frames, if you get, "happy"x2 times, "sad"x1 time, and "happy"x2 times again,
                # then the mode is "happy", and "sad" was a fluke.
                emotion_window = []

                gray_image = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)

                # this is gonna detect faces
                faces = self.detector(rgb_image)

                # for every set of face coordinates detected,
                for face_coordinates in faces:
                    x1, x2, y1, y2 = apply_offsets(face_utils.rect_to_bb(face_coordinates), self.emotion_offsets)

                    gray_face = gray_image[y1:y2, x1:x2]
                    try:
                        gray_face = cv2.resize(gray_face, self.emotion_target_size)
                    except:
                        continue

                    gray_face = preprocess_input(gray_face, True)
                    gray_face = np.expand_dims(gray_face, 0)
                    gray_face = np.expand_dims(gray_face, -1)
                    emotion_prediction = self.emotion_classifier.predict(gray_face)

                    # now only the emotion predicted as most probable is returned, but you can
                    # consider computing a probability-weighted modes by taking in the emotion window
                    emotion_label_arg = np.argmax(emotion_prediction)
                    emotion_text = self.emotion_labels[emotion_label_arg]

                    # debug: using x1 coordinate to understand who's left and who's right
                    #print (x1, emotion_text)

                    emotion_window.append(emotion_text)

                    if len(emotion_window) > self.frame_window:
                        emotion_window.pop(0)
                    try:
                        emotion_mode = mode(emotion_window)
                        self.redis.publish('detected_emotion', emotion_mode)  # TODO: separate per person?
                    except:
                        continue
            else:
                self.image_available_flag.wait()

    def set_image_available(self, message):
        if not self.is_image_available:
            self.is_image_available = True
            self.image_available_flag.set()


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
                    self.emotion_detection_thread.join()
                self.pubsub_thread.stop()
                self.redis.close()
                print('Graceful exit was successful.')
            except redis.RedisError as err:
                print('A graceful exit has failed due to: ' + err.message)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', type=str, default='localhost', help='Server IP address. Default is localhost.')
    parser.add_argument('--no-ssl', action='store_true', default=False, help='Use this flag to disable the use of SSL.')
    args = parser.parse_args()

    emotion_detection_service = EmotionDetectionService(args.server, not args.no_ssl)
    emotion_detection_service.run()
