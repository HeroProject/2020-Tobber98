import numpy as np
import imutils
import cv2
from PIL import Image
import time
import argparse
import redis
import face_recognition

def detect_face(frame):
    '''
    detect human faces in image using haar-cascade
    Args:
        frame:
    '''
    return face_recognition.face_locations(frame)

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

def main(server, debug):
    client = redis.Redis(host=server)
    pubsub = client.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe('action_take_picture')

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
        #timestamp1 = time.time()
        
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
        #timestamp2 = time.time()
        #print 'get image took: ', (timestamp2-timestamp1)
        #print 'time diff: ', (fetch[2][0]-int(fetch[1]))

        im = Image.frombytes('RGB', (im_width, im_height), naoImage)
        ima = np.asarray(im, dtype=np.uint8)
        image_res = imutils.resize(ima, width=min(im_width, ima.shape[1]))
        image = cv2.cvtColor(image_res, cv2.COLOR_BGRA2RGB)

        # For taking pictures...
        msg = pubsub.get_message()
        if msg is not None:
            img = time.strftime('%Y%m%d-%H%M%S')+'.jpg'
            im.save('../webserver/html/img/'+img)
            client.publish('picture_newfile', img)

        # TODO distance metrics
        faces = detect_face(image)

        #timestamp3 = time.time()
        #print 'detection took: ', (timestamp3-timestamp2)
        #print

        if faces:
            print 'detected_person'
            client.publish('detected_person', '')

        if debug:
            if len(faces) > 0:
                draw_faces(image, faces)

            cv2.imshow('Detected person', image)

            cv2.waitKey(10)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break
    pubsub.close()

if __name__ == '__main__':
    parser =  argparse.ArgumentParser()
    parser.add_argument('--server', type=str, default='localhost', help='Server IP address. Default is localhost.')
    parser.add_argument('--debug', type=str, default=False, help='Illustrate the detection.')
    args = parser.parse_args()

    main(args.server, args.debug)
