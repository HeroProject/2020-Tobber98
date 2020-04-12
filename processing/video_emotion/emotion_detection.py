''' All Credits goes to https://github.com/vjgpt/Face-and-Emotion-Recognition '''
import cv2
import numpy as np
import dlib
import face_recognition
from imutils import face_utils
from keras.models import load_model
from statistics import mode
from utils.datasets import get_labels
from utils.inference import apply_offsets
from utils.preprocessor import preprocess_input
import argparse
import redis
import imutils
import time
from PIL import Image

# TO SET CORRECTLY
emotion_model_path = 'emotion_model.hdf5'
emotion_labels = get_labels('fer2013')

# hyper-parameters for bounding boxes shape
frame_window = 10
emotion_offsets = (20, 40)

# loading models
detector = dlib.get_frontal_face_detector()
emotion_classifier = load_model(emotion_model_path)

# getting input model shapes for inference
emotion_target_size = emotion_classifier.input_shape[1:3]

# starting lists for calculating modes
# this is because you wanna look at "average" emotion within some time window (aka number of frames), i.e., the mode,
# because the method is not 100% accurate for every single frame.
# E.g., for a time window of 5 frames, if you get, "happy"x2 times, "sad"x1 time, and "happy"x2 times again,
# then the mode is "happy", and "sad" was a fluke.
emotion_window = []

# frame can be a static image, or a frame from a video stream
def process_frame(frame, client):
    gray_image = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)

    # this is gonna detect faces
    faces = detector(rgb_image)
    #print ('Detected', len(faces), 'face(s)')

    # for every set of face coordinates detected,
    for face_coordinates in faces:
        x1, x2, y1, y2 = apply_offsets(face_utils.rect_to_bb(face_coordinates), emotion_offsets)

        gray_face = gray_image[y1:y2, x1:x2]
        try:
            gray_face = cv2.resize(gray_face, emotion_target_size)
        except:
            continue

        gray_face = preprocess_input(gray_face, True)
        gray_face = np.expand_dims(gray_face, 0)
        gray_face = np.expand_dims(gray_face, -1)
        emotion_prediction = emotion_classifier.predict(gray_face)

        # now only the emotion predicted as most probable is returned, but you can
        # consider computing a probability-weighted modes by taking in the emotion window
        emotion_label_arg = np.argmax(emotion_prediction)
        emotion_text = emotion_labels[emotion_label_arg]

        # debug: using x1 coordinate to understand who's left and who's right
        #print (x1, emotion_text)

        emotion_window.append(emotion_text)

        if len(emotion_window) > frame_window:
            emotion_window.pop(0)
        try:
            emotion_mode = mode(emotion_window)
            client.publish('detected_emotion', emotion_mode) # TODO: separate per person?
        except:
            continue

def main(server):
    client = redis.Redis(host=server)

    # Wait for an image_size to be set
    im_size_string = None
    im_width = None
    im_height = None
    frame = 0

    while im_size_string is None:
        msg = client.get('image_size')
        if msg is None:
            time.sleep(0)
        else:
            im_size_string = msg
            im_width = int(im_size_string[0:4])
            im_height = int(im_size_string[4:])

    while True:
        newframe = client.get('image_frame')
        if newframe is None:
            newframe = -1
        else:
            newframe = int(newframe)
        if newframe != 0 and newframe <= frame:
            #print 'no image'
            time.sleep(0)
            continue
        frame = newframe

        naoImage = client.get('image_stream')
        im = Image.frombytes('RGB', (im_width, im_height), naoImage)
        ima = np.asarray(im, dtype=np.uint8)
        image_res = imutils.resize(ima, width=min(im_width, ima.shape[1]))

        process_frame(image_res, client)

if __name__ == '__main__':
    parser =  argparse.ArgumentParser()
    parser.add_argument('--server', type=str, default='localhost', help='Server IP address. Default is localhost.')
    args = parser.parse_args()

    main(args.server)
