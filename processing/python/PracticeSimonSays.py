# import AbstractApplication as Base
import abstract_connector as Base
from threading import Semaphore
import random
import time


class SimonSays(Base.AbstractSICConnector):  # AbstractApplication):
    def __init__(self):
        super(SimonSays, self).__init__(server_ip='192.168.0.200', robot='nao')

        # Dialogflow data
        self.set_dialogflow_key('ronald-ywcxbh-de715f4ba54d.json')
        self.set_dialogflow_agent('ronald-ywcxbh')

        # Booleans to determine who is host and if explanation is needed
        self.first_time = False
        self.host = True

        # Elements of the game that need to be tracked
        self.score = 0
        self.robot_score = 0
        self.speedup = 0
        self.consecutive_missed = 0
        self.can_press = False
        self.current_button = None
        self.button_pressed = None
        self.response = None

        # Difficulty management
        self.difficulty = 2  # Level range 0 to 4
        self.lives = [3, 2, 1, 1, 1]
        self.time_to_press = [10, 8, 5, 5, 2]
        self.flipped = [False, False, False, True, True]
        self.lives_left = self.lives[self.difficulty]

        # Available buttons to press and release in game
        self.ingame_buttons = {
            "bl": "Rechtervoet", "br": "Linkervoet", "tl": "Rechterhand", "tr": "Linkerhand"}
        self.button_dict = {"RightBumperPressed": "br", "LeftBumperPressed": "bl", "HandRightBackPressed": "tr",
                            "HandRightLeftTouched": "tr", "HandRightRightTouched": "tr", "HandLeftLeftTouched": "tl",
                            "HandLeftRightTouched": "tl", "HandLeftBackPressed": "tl"}
        self.physical_buttons_released = ["RightBumperReleased", "LeftBumperReleased", "HandRightBackReleased",
                                          "HandRightLeftReleased", "HandRightRightReleased", "HandLeftLeftReleased",
                                          "HandLeftRightReleased", "HandLeftBackReleased"]
        self.speech_dict = {"linkervoet": "move-right-foot", "rechtervoet": "move-left-foot",
                            "linkerhand": "move-right-arm", "rechterhand": "move-left-arm"}

        # Created locks
        self.listenLock = Semaphore(0)
        self.langLock = Semaphore(0)
        self.speechLock = Semaphore(0)
        self.movementLock = Semaphore(0)
        self.buttonLock = Semaphore(0)
        self.faceLock = Semaphore(0)

    # Generate rondom float between min and max values given
    def generate_random(self, min, max):
        if self.score * 0.05 < min - 0.5:
            self.speedup = self.score * 0.05
        return round(abs(random.uniform(min - self.speedup, max - self.speedup)), 2)

    def listen(self, context=None, hints=None, time=5):
        self.set_audio_context(context)
        self.set_audio_hints(*hints)
        self.start_listening()
        self.set_leds({'name': 'rotate', 'colour': 0x0033FF33,
                       'rotation_time': 1, 'time': time})
        self.listenLock.acquire(timeout=time)
        self.stop_listening()
        self.listenLock.acquire(timeout=1)

    # Generate single turn of the game
    def create_mole(self):
        self.current_button = None
        time.sleep(self.generate_random(1.5, 2.5))

        self.current_button = list(self.ingame_buttons)[random.randrange(0, 4)]
        if random.getrandbits(1) and self.flipped[self.difficulty]:
            flipped_button = self.current_button[0] + 'l' if self.current_button[1] == 'r' else self.current_button[0] + 'r'
            self.say("Mijn" + self.ingame_buttons[flipped_button] + '!')
        else:
            self.say(self.ingame_buttons[self.current_button] + '!')
        self.speechLock.acquire()

        t = self.time_to_press[self.difficulty] - self.score * 0.1 if self.time_to_press[self.difficulty] - self.score * 0.1 > 1 else 1
        self.can_press = True
        self.set_leds({'name': 'rotate', 'colour': 0x0033FF33,
                       'rotation_time': 0.5, 'time': t})
        self.buttonLock.acquire(timeout=t)
        if self.button_pressed:
            if self.current_button == self.button_dict[self.button_pressed]:
                return True
        return False

    # Subroutine to make a guess of the word that is said and perform a motion
    def guess(self):
        self.response = None
        self.button_pressed = None
        self.say("Ik luister.")
        self.speechLock.acquire()

        self.listen("make_move", ("linkervoet", "rechtervoet", "linkerhand", "rechterhand", "fout"))

        if self.button_pressed in ["FrontTactilTouched", "MiddleTactilTouched", "RearTactilTouched"]:
            return False

        if self.response == "fout" or self.button_pressed in list(self.button_dict):
            self.say("Ah jammer.")
            self.speechLock.acquire()
            return False

        if self.response in list(self.speech_dict):
            self.consecutive_missed = 0
            self.do_gesture("simonsayshost-a4203c/" +
                            self.speech_dict[self.response])
            self.movementLock.acquire()
            self.robot_score += 3
        elif  self.consecutive_missed > 2 or self.robot_score > 10:
            self.consecutive_missed = 0
            self.do_gesture("simonsayshost-a4203c/" + list(self.speech_dict.values())[random.randrange(0, 4)])
            self.movementLock.acquire()
        else:
            self.consecutive_missed += 1
            self.say("Sorry, ik kon je niet goed horen!")
            self.speechLock.acquire()
        return True

    def run_until_quit(self):
        # Call button and wait for response
        self.right = 0
        while True:
            if self.host:
                if not self.create_mole():
                    self.say("Dat was niet goed probeer het nog een keer.")
                    self.speechLock.acquire()
                else:
                    self.right += 1
                    self.say("Juist zo moet het.")
                    self.speechLock.acquire()
                if self.right > 3:
                    self.say("Nu moet jij zeggen wat ik moet doen.")
                    self.speechLock.acquire()
                    self.host = not self.host

            else:
                if not self.guess():
                    break

        self.say("Oké, we stoppen.")
        self.speechLock.acquire()

    # Start of the game
    def start_game(self):
        # Set language to Dutch
        self.set_language('nl-NL')
        self.langLock.acquire()

        # Put robot in right position for host
        self.set_autonomous_life_off("get")
        self.movementLock.acquire()
        if self.autonomous:
            self.set_autonomous_life_off("set")
            self.movementLock.acquire()
        self.do_gesture("simonsayshost-a4203c/sit-down")
        self.movementLock.acquire()

        self.playing = True
        self.run_until_quit()

    # On return of an event perform this function
    def on_robot_event(self, event):
        if event == "LanguageChanged":
            self.langLock.release()

        if event == "TextDone":
            self.speechLock.release()

        if event in list(self.button_dict):
            if self.can_press:
                print("... {}".format(event))
                self.can_press = False
                self.set_leds({'name': 'fade', 'group': 'FaceLeds',
                               'colour': 0x000011FF, 'time': .05})
                self.button_pressed = event
                self.buttonLock.release()

        if event in self.physical_buttons_released:
            self.set_leds({'name': 'fade', 'group': 'FaceLeds',
                           'colour': 0x00FFFFFF, 'time': .05})

        if event in ["FrontTactilTouched", "MiddleTactilTouched", "RearTactilTouched"]:
            self.playing = False

        if event == "GestureDone"or event == "SetAutonomousLifeDisabledDone":
            self.movementLock.release()

        if event.split("|")[0] == "GetAutonomousLifeDisabled":
            self.autonomous = True if event.split("|")[1] == "True" else False
            self.movementLock.release()

    # When there is an audio intent found that corresponds with the current context,
    # perform a certain action.
    def on_audio_intent(self, *args, intent_name):
        print("Args: ", args)
        print("Intent: ", intent_name)
        if intent_name == 'make_move' and len(args) > 0:
            print(args[0])
            self.response = args[0]
            self.listenLock.release()

        elif intent_name == 'answer_closed' and len(args) > 0:
            print(args[0])
            self.response = True if args[0] == 'ja' else False
            self.listenLock.release()
            # release maybe?
        
        elif intent_name == "choose_level" and len(args) > 0:
            # check if actual number
            self.response = args[0]
        
        else:
            print("Error error error")
            self.listenLock.release()


if __name__ == "__main__":
    wam = SimonSays()
    wam.start()
    wam.start_game()
    wam.stop()
