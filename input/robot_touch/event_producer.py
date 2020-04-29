import argparse
import redis
import qi
import functools
import sys

class ReactToEvent(object):

    def __init__(self, app, server):
        # Get the ALMemory service
        app.start()
        memory_service = app.session.service('ALMemory')

		# Commented for now; no use case yet
        #sound_detect_service = app.session.service('ALSoundDetection')
        #sound_detect_service.setParameter('Sensitivity', 0.9)
        #sound_detect_service.subscribe('SoundDetection')

        # Connect to the Naoqi events
        self.right_bumper_pressed = memory_service.subscriber('RightBumperPressed')
        self.left_bumper_pressed = memory_service.subscriber('LeftBumperPressed')
        self.back_bumper_pressed = memory_service.subscriber('BackBumperPressed')
        self.front_tactil_touched = memory_service.subscriber('FrontTactilTouched')
        self.middle_tactil_touched = memory_service.subscriber('MiddleTactilTouched')
        self.rear_tactil_touched = memory_service.subscriber('RearTactilTouched')
        self.hand_right_back_touched = memory_service.subscriber('HandRightBackTouched')
        self.hand_right_left_touched = memory_service.subscriber('HandRightLeftTouched')
        self.hand_right_right_touched = memory_service.subscriber('HandRightRightTouched')
        self.hand_left_left_touched = memory_service.subscriber('HandLeftLeftTouched')
        self.hand_left_right_touched = memory_service.subscriber('HandLeftRightTouched')
        self.hand_left_back_touched = memory_service.subscriber('HandLeftBackTouched')
        #self.sound_detected = memory_service.subscriber('SoundDetected')

        # Subscribe to the events
        self.right_bumper_pressed_id = self.right_bumper_pressed.signal.connect(functools.partial(self.rightBumperPressed, 'RightBumperPressed'))
        self.left_bumper_pressed_id = self.left_bumper_pressed.signal.connect(functools.partial(self.leftBumperPressed, 'LeftBumperPressed'))
        self.back_bumper_pressed_id = self.back_bumper_pressed.signal.connect(functools.partial(self.backBumperPressed, 'BackBumperPressed'))
        self.front_tactil_touched_id = self.front_tactil_touched.signal.connect(functools.partial(self.frontTactilTouched, 'FrontTactilTouched'))
        self.middle_tactil_touched_id = self.middle_tactil_touched.signal.connect(functools.partial(self.middleTactilTouched, 'MiddleTactilTouched'))
        self.rear_tactil_touched_id = self.rear_tactil_touched.signal.connect(functools.partial(self.rearTactilTouched, 'RearTactilTouched'))
        self.hand_right_back_touched_id = self.hand_right_back_touched.signal.connect(functools.partial(self.handRightBackTouched, 'HandRightBackTouched'))
        self.hand_right_left_touched_id = self.hand_right_left_touched.signal.connect(functools.partial(self.handRightLeftTouched, 'HandRightLeftTouched'))
        self.hand_right_right_touched_id = self.hand_right_right_touched.signal.connect(functools.partial(self.handRightRightTouched, 'HandRightRightTouched'))
        self.hand_left_left_touched_id = self.hand_left_left_touched.signal.connect(functools.partial(self.handLeftLeftTouched, 'HandLeftLeftTouched'))
        self.hand_left_right_touched_id = self.hand_left_right_touched.signal.connect(functools.partial(self.handLeftRightTouched, 'HandLeftRightTouched'))
        self.hand_left_back_touched_id = self.hand_left_back_touched.signal.connect(functools.partial(self.handLeftBackTouched, 'HandLeftBackTouched'))
        #self.sound_detected_id = self.sound_detected.signal.connect(functools.partial(self.soundDetected, 'SoundDetected'))

        # Bumper pressed/released logic
        self.right_bumper_is_pressed = False
        self.left_bumper_is_pressed = False

        # Initialise Redis
        self.redis = redis.Redis(host=server, ssl=True, ssl_ca_certs='../cert.pem')

    def produce(self, value):
        self.redis.publish('events_robot', value)

    def rightBumperPressed(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.right_bumper_pressed.signal.disconnect(self.right_bumper_pressed_id)

        if self.right_bumper_is_pressed:
            self.produce('RightBumperReleased')
            print('RightBumperReleased detected')
            self.right_bumper_is_pressed = False
        else:
            self.produce('RightBumperPressed')
            print('RightBumperPressed detected')
            self.right_bumper_is_pressed = True

        # Reconnect again to the event
        self.right_bumper_pressed_id = self.right_bumper_pressed.signal.connect(functools.partial(self.rightBumperPressed, 'RightBumperPressed'))

    def leftBumperPressed(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.left_bumper_pressed.signal.disconnect(self.left_bumper_pressed_id)

        if self.left_bumper_is_pressed:
            self.produce('LeftBumperReleased')
            print('LeftBumperReleased detected')
            self.left_bumper_is_pressed = False
        else:
            self.produce('LeftBumperPressed')
            print('LeftBumperPressed detected')
            self.left_bumper_is_pressed = True


        # Reconnect again to the event
        self.left_bumper_pressed_id = self.left_bumper_pressed.signal.connect(functools.partial(self.leftBumperPressed, 'LeftBumperPressed'))

    def backBumperPressed(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.back_bumper_pressed.signal.disconnect(self.back_bumper_pressed_id)

        self.produce('BackBumperPressed')
        print('BackBumperPressed detected')

        # Reconnect again to the event
        self.back_bumper_pressed_id = self.back_bumper_pressed.signal.connect(functools.partial(self.backBumperPressed, 'BackBumperPressed'))

    def frontTactilTouched(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.front_tactil_touched.signal.disconnect(self.front_tactil_touched_id)

        self.produce('FrontTactilTouched')
        print('FrontTactilTouched detected')

        # Reconnect again to the event
        self.front_tactil_touched_id = self.front_tactil_touched.signal.connect(functools.partial(self.frontTactilTouched, 'FrontTactilTouched'))

    def middleTactilTouched(self, strVarName, value):
       # Disconnect to the event to avoid repetitions
        self.middle_tactil_touched.signal.disconnect(self.middle_tactil_touched_id)

        self.produce('MiddleTactilTouched')
        print('MiddleTactilTouched detected')

        # Reconnect again to the event
        self.middle_tactil_touched_id = self.middle_tactil_touched.signal.connect(functools.partial(self.middleTactilTouched, 'MiddleTactilTouched'))

    def rearTactilTouched(self, strVarName, value):
       # Disconnect to the event to avoid repetitions
        self.rear_tactil_touched.signal.disconnect(self.rear_tactil_touched_id)

        self.produce('RearTactilTouched')
        print('RearTactilTouched detected')

        # Reconnect again to the event
        self.rear_tactil_touched_id = self.rear_tactil_touched.signal.connect(functools.partial(self.rearTactilTouched, 'RearTactilTouched'))

    def handRightBackTouched(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.hand_right_back_touched.signal.disconnect(self.hand_right_back_touched_id)

        self.produce('HandRightBackTouched')
        print('HandRightBackTouched detected')

        # Reconnect again to the event
        self.hand_right_back_touched_id = self.hand_right_back_touched.signal.connect(functools.partial(self.handRightBackTouched, 'HandRightBackTouched'))

    def handRightLeftTouched(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.hand_right_left_touched.signal.disconnect(self.hand_right_left_touched_id)

        self.produce('HandRightLeftTouched')
        print('HandRightLeftTouched detected')

        # Reconnect again to the event
        self.hand_right_left_touched_id = self.hand_right_left_touched.signal.connect(functools.partial(self.handRightLeftTouched, 'HandRightLeftTouched'))

    def handRightRightTouched(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.hand_right_right_touched.signal.disconnect(self.hand_right_right_touched_id)

        self.produce('HandRightRightTouched')
        print('HandRightRightTouched detected')

        # Reconnect again to the event
        self.hand_right_right_touched_id = self.hand_right_right_touched.signal.connect(functools.partial(self.handRightRightTouched, 'HandRightRightTouched'))

    def handLeftLeftTouched(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.hand_left_left_touched.signal.disconnect(self.hand_left_left_touched_id)

        self.produce('HandLeftLeftTouched')
        print('HandLeftLeftTouched detected')

        # Reconnect again to the event
        self.hand_left_left_touched_id = self.hand_left_left_touched.signal.connect(functools.partial(self.handLeftLeftTouched, 'HandLeftLeftTouched'))

    def handLeftRightTouched(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.hand_left_right_touched.signal.disconnect(self.hand_left_right_touched_id)

        self.produce('HandLeftRightTouched')
        print('HandLeftRightTouched detected')

        # Reconnect again to the event
        self.hand_left_right_touched_id = self.hand_left_right_touched.signal.connect(functools.partial(self.handLeftRightTouched, 'HandLeftRightTouched'))

    def handLeftBackTouched(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.hand_left_back_touched.signal.disconnect(self.hand_left_back_touched_id)

        self.produce('HandLeftBackTouched')
        print('HandLeftBackTouched detected')

        # Reconnect again to the event
        self.hand_left_back_touched_id = self.hand_left_back_touched.signal.connect(functools.partial(self.handLeftBackTouched, 'HandLeftBackTouched'))

    def soundDetected(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.sound_detected.signal.disconnect(self.sound_detected_id)

        self.produce('SoundDetected')
        print('Sound detected')

        # Reconnect again to the event
        self.sound_detected_id = self.sound_detected.signal.connect(functools.partial(self.soundDetected, 'SoundDetected'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', type=str, default='localhost', help='Server IP address. Default is localhost.')
    args = parser.parse_args()

    try:
        app = qi.Application(['ReactToEvent', '--qi-url=tcp://127.0.0.1:9559'])
    except RuntimeError:
        print ('Cannot connect to Naoqi')
        sys.exit(1)

    react_to_event = ReactToEvent(app=app, server=args.server)
    app.run()
