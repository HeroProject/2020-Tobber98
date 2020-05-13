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
        self.is_sensor_touched = {'RightBumperPressed': False,
                                  'LeftBumperPressed': False,
                                  'BackBumperPressed': False,
                                  'FrontTactilTouched': False,
                                  'MiddleTactilTouched': False,
                                  'RearTactilTouched': False,
                                  'HandRightBackTouched': False,
                                  'HandRightLeftTouched': False,
                                  'HandRightRightTouched': False,
                                  'HandLeftBackTouched': False,
                                  'HandLeftLeftTouched': False,
                                  'HandLeftRightTouched': False}

        self.sensor_alt = {'RightBumperPressed': 'RightBumperReleased',
                           'LeftBumperPressed': 'LeftBumperReleased',
                           'BackBumperPressed': 'BackBumperReleased',
                           'FrontTactilTouched': 'FrontTactilReleased',
                           'MiddleTactilTouched': 'MiddleTactilReleased',
                           'RearTactilTouched': 'RearTactilReleased',
                           'HandRightBackTouched': 'HandRightBackReleased',
                           'HandRightLeftTouched': 'HandRightLeftReleased',
                           'HandRightRightTouched': 'HandRightRightReleased',
                           'HandLeftBackTouched': 'HandLeftBackReleased',
                           'HandLeftLeftTouched': 'HandLeftLeftReleased',
                           'HandLeftRightTouched': 'HandLeftRightReleased'}

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
        self.hand_left_back_touched = memory_service.subscriber('HandLeftBackTouched')
        self.hand_left_left_touched = memory_service.subscriber('HandLeftLeftTouched')
        self.hand_left_right_touched = memory_service.subscriber('HandLeftRightTouched')

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
        self.hand_left_back_touched_id = self.hand_left_back_touched.signal.connect(functools.partial(self.handLeftBackTouched, 'HandLeftBackTouched'))
        self.hand_left_left_touched_id = self.hand_left_left_touched.signal.connect(functools.partial(self.handLeftLeftTouched, 'HandLeftLeftTouched'))
        self.hand_left_right_touched_id = self.hand_left_right_touched.signal.connect(functools.partial(self.handLeftRightTouched, 'HandLeftRightTouched'))

        # Initialise Redis
        self.redis = redis.Redis(host=server, ssl=True, ssl_ca_certs='../cert.pem')

    def produce(self, value):
        self.redis.publish('events_robot', value)

    def process_sensor_touch(self, event):

        if self.is_sensor_touched[event]:
            self.produce(self.sensor_alt[event])
            print(self.sensor_alt[event] + " detected")
            self.is_sensor_touched[event] = False
        else:
            self.produce(event)
            print(event + "detected")
            self.is_sensor_touched[event] = True

    def rightBumperPressed(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.right_bumper_pressed.signal.disconnect(self.right_bumper_pressed_id)

        self.process_sensor_touch('RightBumperPressed')

        # Reconnect again to the event
        self.right_bumper_pressed_id = self.right_bumper_pressed.signal.connect(functools.partial(self.rightBumperPressed, 'RightBumperPressed'))

    def leftBumperPressed(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.left_bumper_pressed.signal.disconnect(self.left_bumper_pressed_id)

        self.process_sensor_touch('LeftBumperPressed')

        # Reconnect again to the event
        self.left_bumper_pressed_id = self.left_bumper_pressed.signal.connect(functools.partial(self.leftBumperPressed, 'LeftBumperPressed'))

    def backBumperPressed(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.back_bumper_pressed.signal.disconnect(self.back_bumper_pressed_id)

        self.process_sensor_touch('BackBumperPressed')

        # Reconnect again to the event
        self.back_bumper_pressed_id = self.back_bumper_pressed.signal.connect(functools.partial(self.backBumperPressed, 'BackBumperPressed'))

    def frontTactilTouched(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.front_tactil_touched.signal.disconnect(self.front_tactil_touched_id)

        self.process_sensor_touch('FrontTactilTouched')

        # Reconnect again to the event
        self.front_tactil_touched_id = self.front_tactil_touched.signal.connect(functools.partial(self.frontTactilTouched, 'FrontTactilTouched'))

    def middleTactilTouched(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.middle_tactil_touched.signal.disconnect(self.middle_tactil_touched_id)

        self.process_sensor_touch('MiddleTactilTouched')

        # Reconnect again to the event
        self.middle_tactil_touched_id = self.middle_tactil_touched.signal.connect(functools.partial(self.middleTactilTouched, 'MiddleTactilTouched'))

    def rearTactilTouched(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.rear_tactil_touched.signal.disconnect(self.rear_tactil_touched_id)

        self.process_sensor_touch('RearTactilTouched')

        # Reconnect again to the event
        self.rear_tactil_touched_id = self.rear_tactil_touched.signal.connect(functools.partial(self.rearTactilTouched, 'RearTactilTouched'))

    def handRightBackTouched(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.hand_right_back_touched.signal.disconnect(self.hand_right_back_touched_id)

        self.process_sensor_touch('HandRightBackTouched')

        # Reconnect again to the event
        self.hand_right_back_touched_id = self.hand_right_back_touched.signal.connect(functools.partial(self.handRightBackTouched, 'HandRightBackTouched'))

    def handRightLeftTouched(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.hand_right_left_touched.signal.disconnect(self.hand_right_left_touched_id)

        self.process_sensor_touch('HandRightLeftTouched')

        # Reconnect again to the event
        self.hand_right_left_touched_id = self.hand_right_left_touched.signal.connect(functools.partial(self.handRightLeftTouched, 'HandRightLeftTouched'))

    def handRightRightTouched(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.hand_right_right_touched.signal.disconnect(self.hand_right_right_touched_id)

        self.process_sensor_touch('HandRightRightTouched')

        # Reconnect again to the event
        self.hand_right_right_touched_id = self.hand_right_right_touched.signal.connect(functools.partial(self.handRightRightTouched, 'HandRightRightTouched'))

    def handLeftBackTouched(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.hand_left_back_touched.signal.disconnect(self.hand_left_back_touched_id)

        self.process_sensor_touch('HandLeftBackTouched')

        # Reconnect again to the event
        self.hand_left_back_touched_id = self.hand_left_back_touched.signal.connect(functools.partial(self.handLeftBackTouched, 'HandLeftBackTouched'))

    def handLeftLeftTouched(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.hand_left_left_touched.signal.disconnect(self.hand_left_left_touched_id)

        self.process_sensor_touch('HandLeftLeftTouched')

        # Reconnect again to the event
        self.hand_left_left_touched_id = self.hand_left_left_touched.signal.connect(functools.partial(self.handLeftLeftTouched, 'HandLeftLeftTouched'))

    def handLeftRightTouched(self, strVarName, value):
        # Disconnect to the event to avoid repetitions
        self.hand_left_right_touched.signal.disconnect(self.hand_left_right_touched_id)

        self.process_sensor_touch('HandLeftRightTouched')

        # Reconnect again to the event
        self.hand_left_right_touched_id = self.hand_left_right_touched.signal.connect(functools.partial(self.handLeftRightTouched, 'HandLeftRightTouched'))


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
