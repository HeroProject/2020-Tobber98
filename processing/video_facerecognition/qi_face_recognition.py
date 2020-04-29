import numpy as np
import argparse
import sys
import time
import os
from PIL import Image
import cv2
import face_recognition
from imutils.video import FPS
import pickle as pkl
import redis

FACE_ENCODING_PATH = 'face_encodings.p'
def main(debug, server, ssl):
    client = redis.Redis(host=server, ssl=ssl, ssl_ca_certs='../cert.pem')
    pubsub = client.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe('action_take_picture')

    # Initialize data to do face recognition
    face_encodings_list = []
    face_labels = []
    face_names = []
    face_count = []
    im_size_string = None
    im_width = 0
    im_height = 0
    frame = -1

    # Create a difference between background and forground image
    fgbg = cv2.createBackgroundSubtractorMOG2()

    def normalise_luminiscence(im,gamma=2.5):
        # build a lookup table mapping the pixel values [0, 255] to
        # their adjusted gamma values such that any image has the same luminiscence
        invGamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** invGamma) * 255
            for i in np.arange(0, 256)]).astype('uint8')

        # apply gamma correction using the lookup table
        return cv2.LUT(image, table, image)

    if os.path.isfile(FACE_ENCODING_PATH):
        face_encodings_list = pkl.load(open(FACE_ENCODING_PATH,'rb'))
        if debug:
            print('loading encodings', 'Length encoding ', len(face_encodings_list))
    fps = FPS().start()

    # Wait for a message on the image_size topic
    while im_size_string is None:
        msg = client.get('image_size')
        if msg is None:
            time.sleep(0.001)
        else:
            im_size_string = msg
            im_width = int(im_size_string[0:4])
            im_height = int(im_size_string[4:])

    while True:
        if debug:
            t0 = time.time()

        newframe = client.get('image_frame')
        if newframe is None:
            newframe = -1
        else:
            newframe = int(newframe)
        if newframe != 0 and newframe <= frame:
            #print 'no image'
            time.sleep(0.001)
            continue
        frame = newframe

        naoImage = client.get('image_stream')

        if debug:
            # Time the image transfer.
            t1 = time.time()
            print('acquisition delay from server', t1 - t0)

        # Create a PIL Image from our pixel array.
        im = Image.frombytes('RGB', (im_width, im_height), naoImage)
        cv_image = cv2.cvtColor(np.asarray(im, dtype=np.uint8), cv2.COLOR_BGRA2RGB)
        image = cv_image[:, :, ::-1]

        # For taking pictures...
        msg = pubsub.get_message()
        if msg is not None:
            img = time.strftime('%Y%m%d-%H%M%S')+'.jpg'
            im.save('../webserver/html/img/'+img)
            client.publish('picture_newfile', img)

        #Manipulate image in order to help face recognition
        #normalise_luminiscence(image)
        fgbg.apply(image)

        face_locations = face_recognition.face_locations(image, model='hog')
        face_encodings = face_recognition.face_encodings(image, face_locations)
        face_name = []

        for face_encoding in face_encodings:
            name = None
            match = face_recognition.compare_faces(face_encodings_list, face_encoding, tolerance=0.6)
            dist = face_recognition.face_distance(face_encodings_list, face_encoding)

            if all(values == False for values in match ) and all([d for d in dist if d > 0.7]):
                if debug:
                    print('New Person')

                count = len(face_encodings_list) if len(face_encodings_list) > 0 else 0
                name = str(count)
                face_count.append(count)
                face_encodings_list.append(face_encoding)
                face_names.append(name)
                pkl.dump(face_encodings_list, open(FACE_ENCODING_PATH, 'wb'))

            else:
                index = match.index(True)
                tmp = str(index)
                if debug:
                    print('Not consistent match with compare faces and euclidean distance \n')
                    print('NAME ', name, 'ArgMin ', np.argmin(dist), 'Count ', count)

                if index == np.argmin(dist):
                    name = tmp
                    face_name.append(name)
                    if debug:
                        print('Person already recognised and consistent \n')
                        print('NAME ', name, 'ArgMin ', np.argmin(dist))
                else:
                    if debug:
                        print('Mismatch in face recognition')
                    continue

            client.publish('recognised_face', name)

        if debug:
            for (top, right, bottom, left), name in zip(face_locations, face_name):
                cv2.rectangle(cv_image, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.rectangle(cv_image, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(cv_image, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

            cv2.namedWindow('Camera', cv2.WINDOW_NORMAL)
            cv2.imshow('Camera', cv_image)
            fps.update()
            cv2.waitKey(25)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    fps.stop()

    print('Elapsed time : {:.2f}'.format(fps.elapsed()))
    print('Approximate FPS: {:.2f}'.format(fps.fps()))

    pubsub.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', type=str, default='localhost', help='Server IP address. Default is localhost.')
    parser.add_argument('--no-ssl', action='store_true', default=False, help='Use this flag to disable the use of SSL.')
    parser.add_argument('--debug', action='store_true', default=False, help='Use this flag to enable several debug statements and drawings.')
    args = parser.parse_args()

    main(args.debug, args.server, not args.no_ssl)
