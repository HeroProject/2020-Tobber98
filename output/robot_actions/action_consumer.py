import argparse
import ssl
from signal import signal, SIGTERM, SIGINT, pause

from naoqi import ALProxy
from threading import Thread
import redis
import os
import wget
import shutil

import json

YELLOW = 0x969600
MAGENTA = 0xff00ff
ORANGE = 0xfa7800
GREEN = 0x00ff00


class RobotConsumer:
    def __init__(self, server, topics):
        self.server = server
        self.redis = redis.Redis(host=server, ssl=True, ssl_ca_certs='../cert.pem')
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(**dict.fromkeys(topics, self.execute))
        self.pubsub_thread = self.pubsub.run_in_thread(sleep_time=0.001)

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

        # create a folder on robot to temporarily store loaded audio files
        self.audio_folder = os.path.join(os.getcwd(), 'sounds')
        if not (os.path.exists(self.audio_folder)):
            os.mkdir(self.audio_folder)

        # Ignores SSL certificate when using wget to download audio files from server over https
        # Solution from: https://thomas-cokelaer.info/blog/2016/01/python-certificate-verified-failed/
        ssl._create_default_https_context = ssl._create_unverified_context

        # Register cleanup handlers
        signal(SIGTERM, self.cleanup)
        signal(SIGINT, self.cleanup)

        self.running = True
        self.followed_face = None
        self.rotate_eyes_id = None

    def produce(self, value):
        self.redis.publish('events_robot', value)

    def execute(self, message):
        t = Thread(target=self.process_message, args=(message,))
        t.start()

    def process_message(self, message):
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
        elif channel == 'action_followface':
            self.follow_face(data)
        elif channel == 'action_eyecolour':
            self.produce('EyeColourStarted')
            self.change_eye_colour(data)
            self.produce('EyeColourDone')
        elif channel == 'action_change_leds':
            self.produce('ChangeLedsStarted')
            self.change_leds(data)
            self.produce('changeLedsDone') 
        elif channel == 'audio_language':
            self.change_language(data)
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
            else:  # right
                self.motion.post.moveTo(0.0,0.0,-1.5,1.0)
            self.motion.waitUntilMoveIsFinished()
            self.produce('TurnDone')
        elif channel == 'action_turn_small':
            self.motion.setStiffnesses('Leg', 0.8)
            self.produce('SmallTurnStarted')
            self.motion.moveInit()
            if data == 'left':
                self.motion.post.moveTo(0.0,0.0,0.25,1.0)
            else:  # right
                self.motion.post.moveTo(0.0,0.0,-0.25,1.0)
            self.motion.waitUntilMoveIsFinished()
            self.produce('SmallTurnDone')
        elif channel == 'action_load_audio':
            if data:
                audio_file = self.download_audio(data)
                audio_id = self.audio_player.loadFile(audio_file)
                self.redis.publish('robot_audio_loaded', audio_id)
                self.produce('LoadAudioDone')
        elif channel == 'action_play_audio':
            self.audio_player.stopAll()
            params = data.split(';')
            if params[0] and params[1] == 'raw':
                audio_file = self.download_audio(params[0])
                self.produce('PlayAudioStarted')
                self.audio_player.playFile(audio_file)
                self.produce('PlayAudioDone')
                os.remove(audio_file)
            elif params[0] and params[1] == 'loaded':
                self.produce('PlayAudioStarted')
                self.audio_player.play(int(params[0]))
                self.produce('PlayAudioDone')
        elif channel == 'action_clear_loaded_audio':
            self.audio_player.unloadAllFiles()
            shutil.rmtree(self.audio_folder)
            os.mkdir(self.audio_folder)
            self.produce('ClearLoadedAudioDone')
        elif channel == 'action_speech_param':
            params = data.split(';')
            self.tts.setParameter(params[0], float(params[1]))
        elif channel == 'action_wakeup':
            self.produce('WakeUpStarted')
            self.motion.wakeUp()
            self.produce('WakeUpDone')
        elif channel == 'action_rest':
            self.produce('RestStarted')
            self.motion.rest()
            self.produce('RestDone')
        elif channel == 'action_set_breathing':
            params = data.split(';')
            enable = bool(int(params[1]))
            self.motion.setBreathEnabled(params[0], enable)
            if enable:
                self.produce('BreathingEnabled')
            else:
                self.produce('BreathingDisabled')
        else:
            print 'Unknown command'

    def follow_face(self, value):
        print("Test")
        print value, type(value)
        if int(value) == 1:
            print "followed_face is: ", self.followed_face
            if not self.followed_face:
                self.produce("FollowFaceStarted")
                self.followed_face = self.animation.run("simonsayshost-a4203c/follow-face", _async=True)
                self.produce("FollowFaceDone")
        else:
            if self.followed_face:
                self.produce("StopFollowFaceStarted")
                self.followed_face.cancel()
                self.followed_face = None
                self.produce("StopFollowFaceDone")

    def change_eye_colour(self, value):
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

    def change_leds(self, value):
        led_dict = json.loads(value)
        
        if led_dict['name'] == 'off':
            if self.rotate_eyes_id:
                self.leds.stop(self.rotate_eyes_id)
            self.leds.off(str(led_dict['group']))
        elif led_dict['name'] == 'fade':
            self.leds.stop(self.rotate_eyes_id)
            self.leds.fadeRGB(str(led_dict['group']), led_dict['colour'], led_dict['time'])
        elif led_dict['name'] == 'fadeList':
            self.leds.stop(self.rotate_eyes_id)
            self.leds.fadeListRGB(str(led_dict['group']), led_dict['colour'], led_dict['time'])
        elif led_dict['name'] == 'rotate':
            self.rotate_eyes_id = self.leds.post.rotateEyes(led_dict['colour'], led_dict['rotation_time'], led_dict['time'])
        elif led_dict['name'] == 'stop_rotate':
            self.leds.stop(self.rotate_eyes_id)

    def change_language(self, value):
        if value == 'nl-NL':
            self.language.setLanguage('Dutch')
        else:
            self.language.setLanguage('English')

    def download_audio(self, file_name):
        local_audio_location = os.path.join(self.audio_folder, file_name)
        wget.download('https://' + self.server + ':8000/audio/' + file_name, local_audio_location)
        return local_audio_location

    def run_forever(self):
        while self.running:
            pause()

    def cleanup(self, signum, frame):
        if self.running:
            self.running = False
            print('Trying to exit gracefully...')
            try:
                self.pubsub_thread.stop()
                self.redis.close()
                print('Graceful exit was successful.')
            except redis.RedisError as err:
                print('A graceful exit has failed due to: ' + err.message)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', type=str, default='localhost', help='Server IP address. Default is localhost.')
    args = parser.parse_args()

    robot_consumer = RobotConsumer(server=args.server, topics=['action_say', 'action_say_animated', 'action_gesture',
                                                               'action_eyecolour', 'audio_language', 'action_idle',
                                                               'action_play_audio', 'action_load_audio', 'action_clear_audio',
                                                               'action_speech_param', 'action_turn',
                                                               'action_turn_small', 'action_wakeup', 'action_rest',
                                                               'action_set_breathing', 'action_change_leds', 'action_followface'])
    robot_consumer.run_forever()
