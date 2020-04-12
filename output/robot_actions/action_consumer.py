import argparse
from naoqi import ALProxy
from threading import Thread
import time
import redis
import os
import wget

YELLOW = 0x969600
MAGENTA = 0xff00ff
ORANGE = 0xfa7800
GREEN = 0x00ff00

class RobotConsumer():
    def __init__(self, server, topics):
        self.server = server
        self.redis = redis.Redis(host=server)
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(*topics)

        robot_ip = '127.0.0.1'
        robot_port = 9559

        self.tts = ALProxy('ALTextToSpeech', robot_ip, robot_port)
        self.atts = ALProxy('ALAnimatedSpeech', robot_ip, robot_port)
        self.animation = ALProxy('ALAnimationPlayer', robot_ip, robot_port)
        self.leds = ALProxy('ALLeds', robot_ip, robot_port)
        self.language = ALProxy('ALDialog', robot_ip, robot_port)
        self.awareness = ALProxy('ALBasicAwareness', robot_ip, robot_port)
        self.awareness.setEngagementMode('FullyEngaged')
        self.motion = ALProxy('ALMotion', robot_ip, robot_port)
        self.audio_player = ALProxy('ALAudioPlayer', robot_ip, robot_port)

    def update(self):
        msg = self.pubsub.get_message()
        if msg is not None:
            t = Thread(target = self.execute, args = (msg, ))
            t.start()
        else:
            time.sleep(0)

    def produce(self, value):
        self.redis.publish('events_robot', value)

    def execute(self, message):
        channel = message['channel']
        data = message['data']
        print channel + ': ' + data
        if channel == 'action_say':
            self.produce('TextStarted')
            self.tts.say(data)
            self.produce('TextDone')
        elif channel == 'action_say_animated':
            self.produce('TextStarted')
            self.atts.say(data)
            self.produce('TextDone')
        elif channel == 'action_gesture':
            self.produce('GestureStarted')
            self.animation.run(data)
            self.produce('GestureDone')
        elif channel == 'action_eyecolour':
            self.produce('EyeColourStarted')
            self.changeEyeColour(data)
            self.produce('EyeColourDone')
        elif channel == 'audio_language':
            self.changeLanguage(data)
            self.produce('LanguageChanged')
        elif channel == 'action_idle':
            self.motion.setStiffnesses('Head', 0.6)
            if data == 'true':
                self.awareness.setEnabled(False)
                # HeadPitch of -0.3 for looking slightly upwards. HeadYaw of 0 for looking forward rather than sidewards.
                self.motion.setAngles(['HeadPitch', 'HeadYaw'], [-0.3, 0], 0.1)
                self.produce('SetIdle')
            elif data == 'straight':
                self.awareness.setEnabled(False)
                self.motion.setAngles(['HeadPitch', 'HeadYaw'], [0, 0], 0.1)
                self.produce('SetIdle')
            else:
                self.awareness.setEnabled(True)
                self.produce('SetNonIdle')
        elif channel == 'action_turn':
            self.motion.setStiffnesses('Leg', 0.8)
            self.produce('TurnStarted')
            self.motion.moveInit()
            if data == 'left':
                self.motion.post.moveTo(0.0,0.0,1.5,1.0)
            else: # right
                self.motion.post.moveTo(0.0,0.0,-1.5,1.0)
            self.motion.waitUntilMoveIsFinished()
            self.produce('TurnDone')
        elif channel == 'action_turn_small':
            self.motion.setStiffnesses('Leg', 0.8)
            self.produce('SmallTurnStarted')
            self.motion.moveInit()
            if data == 'left':
                self.motion.post.moveTo(0.0,0.0,0.25,1.0)
            else: # right
                self.motion.post.moveTo(0.0,0.0,-0.25,1.0)
            self.motion.waitUntilMoveIsFinished()
            self.produce('SmallTurnDone')
        elif channel == 'action_play_audio':
            self.audio_player.stopAll()
            if data:
                wget.download('http://'+self.server+':8000/audio/'+data, data)
                self.produce('PlayAudioStarted')
                self.audio_player.playFile(os.getcwd()+'/'+data)
                self.produce('PlayAudioDone')
                os.remove(data)
        elif channel == 'action_speech_param':
            params = data.split(';')
            self.tts.setParameter(params[0], float(params[1]))
        else:
            print 'Unknown command'

    def changeEyeColour(self, value):
        self.leds.off('FaceLeds')
        if value == 'rainbow':    # make the eye colours rotate
            p1 = Thread(target = self.leds.fadeListRGB, args = ('FaceLedsBottom', [YELLOW, MAGENTA, ORANGE, GREEN], [0, 0.5, 1, 1.5], ))
            p2 = Thread(target = self.leds.fadeListRGB, args = ('FaceLedsTop', [MAGENTA, ORANGE, GREEN, YELLOW], [0, 0.5, 1, 1.5], ))
            p3 = Thread(target = self.leds.fadeListRGB, args = ('FaceLedsExternal', [ORANGE, GREEN, YELLOW, MAGENTA], [0, 0.5, 1, 1.5], ))
            p4 = Thread(target = self.leds.fadeListRGB, args = ('FaceLedsInternal', [GREEN, YELLOW, MAGENTA, ORANGE], [0, 0.5, 1, 1.5], ))

            p1.start()
            p2.start()
            p3.start()
            p4.start()

            p1.join()
            p2.join()
            p3.join()
            p4.join()
        elif value == 'greenyellow':    # make the eye colours a combination of green and yellow
            p1 = Thread(target = self.leds.fadeListRGB, args = ('FaceLedsBottom', [YELLOW, GREEN, YELLOW, GREEN], [0, 0.5, 1, 1.5], ))
            p2 = Thread(target = self.leds.fadeListRGB, args = ('FaceLedsTop', [GREEN, YELLOW, GREEN, YELLOW], [0, 0.5, 1, 1.5], ))
            p3 = Thread(target = self.leds.fadeListRGB, args = ('FaceLedsExternal', [YELLOW, GREEN, YELLOW, GREEN], [0, 0.5, 1, 1.5], ))
            p4 = Thread(target = self.leds.fadeListRGB, args = ('FaceLedsInternal', [GREEN, YELLOW, GREEN, YELLOW], [0, 0.5, 1, 1.5], ))

            p1.start()
            p2.start()
            p3.start()
            p4.start()

            p1.join()
            p2.join()
            p3.join()
            p4.join()
        elif value:
            self.leds.fadeRGB('FaceLeds', value, 0.1)

    def changeLanguage(self, value):
        if value == 'nl-NL':
            self.language.setLanguage('Dutch')
        else:
            self.language.setLanguage('English')

    def runForever(self):
        try:
            while True:
                self.update()
        except KeyboardInterrupt:
            print 'Interrupted'
            self.pubsub.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', type=str, default='localhost', help='Server IP address. Default is localhost.')
    args = parser.parse_args()

    robot_consumer = RobotConsumer(server=args.server, topics=['action_say', 'action_say_animated', 'action_gesture', 'action_eyecolour', 'audio_language', 'action_idle', 'action_play_audio', 'action_speech_param', 'action_turn', 'action_turn_small'])
    robot_consumer.runForever()
