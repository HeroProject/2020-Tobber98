# import AbstractApplication as Base
import abstract_connector as Base
from threading import Semaphore
import random
import time


class SimonSays(Base.AbstractSICConnector):   #AbstractApplication):
    def __init__(self):
        super(SimonSays, self).__init__(server_ip='192.168.0.200', robot='nao')
        
        # Dialogflow data
        self.set_dialogflow_key('ronald-ywcxbh-a2ca41d812bb.json')
        self.set_dialogflow_agent('ronald-ywcxbh')

        # Booleans to determine who is host and if explanation is needed
        self.first_time = False
        self.host = True

        # Elements of the game that need to be tracked
        self.score = 0
        self.speedup = 0
        self.can_press = False
        self.current_button = None
        self.button_pressed = None
        self.move_to_make = None

        # Available buttons to press and release in game
        self.ingame_buttons = {"bl": "Rechtervoet", "br": "Linkervoet", "tl": "Rechterhand", "tr": "Linkerhand"}
        self.button_dict = {"RightBumperPressed": "br", "LeftBumperPressed": "bl", "HandRightBackPressed": "tr",
                                         "HandRightLeftTouched": "tr", "HandRightRightTouched": "tr", "HandLeftLeftTouched": "tl",
                                         "HandLeftRightTouched": "tl", "HandLeftBackPressed": "tl"}
        self.physical_buttons_released = ["RightBumperReleased", "LeftBumperReleased", "HandRightBackReleased",
                                          "HandRightLeftReleased", "HandRightRightReleased", "HandLeftLeftReleased",
                                          "HandLeftRightReleased", "HandLeftBackReleased"]

        self.speech_dict = {"linkervoet": "move-left-foot", "rechtervoet": "move-right-foot",
                        "linkerhand": "move-left-arm", "rechterhand": "move-right-arm"}

        # Created locks
        self.turnLock = Semaphore(0)
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

    # Generate single turn of the game
    def create_mole(self):
        self.current_button = None
        time.sleep(self.generate_random(1.5, 2.5))
        self.current_button = list(self.ingame_buttons)[random.randrange(0, 4)]

        self.say(self.ingame_buttons[self.current_button] + '!')
        self.speechLock.acquire()

        t = self.generate_random(3, 6)
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
        self.button_pressed = None
        self.say("Ik luister.")
        self.speechLock.acquire()
        self.set_audio_context("make_move")
        self.set_audio_hints("linkervoet", "rechtervoet",
                           "linkerhand", "rechterhand", "fout")
        self.start_listening()
        self.set_leds({'name': 'rotate', 'colour': 0x0033FF33,
                      'rotation_time': 1, 'time': 5.0})
        self.turnLock.acquire(timeout=5)
        self.stop_listening()

        if self.move_to_make == "fout" or self.button_pressed in ["FrontTactilTouched", "MiddleTactilTouched", "RearTactilTouched"]:
            self.say("Ah jammer, nu mag jij weer!")
            self.speechLock.acquire()
            self.host = True
            return False

        if self.move_to_make in list(self.speech_dict):
            self.do_gesture("simonsayshost-a4203c/" + self.speech_dict[self.move_to_make])
            self.movementLock.acquire()
        else:
            self.say("Sorry, ik kon je niet goed horen!")
            self.speechLock.acquire()
        return True

    # Explanation of the game where the robot shows what the player is supposed to do
    def explain_game(self):
        self.say_animated("Hé, leuk dat je *spelnaam* met mij wil spelen. \
            Ik zal het proberen uit te leggen. Er zijn twee manieren om het spel te spelen. \
            De eerste manier is dat ik zeg wat jij aan moet tikken en de tweede manier is dat jij zegt wat ik moet bewegen.")
        self.speechLock.acquire()

        self.set_leds({"name": "rotate", "colour": 0x0033FF33,
                      "rotation_time": 1, "time": 4})
        self.say("Mijn ogen zullen draaien, zoals ze nu doen, als je kunt drukken op mijn knoppen. \
                Hetzelfde geldt voor wanneer ik luister terwijl jij spelleider bent. \
                Laten we beginnen met een oefenronde. Ik zeg iets en jij moet op de knop drukken.")
        self.speechLock.acquire()

        self.do_gesture("simonsayshost-a4203c/sit-down")
        self.movementLock.acquire()
        while not self.create_mole():
            if self.can_press:
                self.say("Ah, je was niet snel genoeg. We proberen het nog een keer.")
                self.speechLock.acquire()
                self.can_press = False
            else:
                self.say("Ah, dat was de verkeerde knop. We proberen het nog een keer.")
                self.speechLock.acquire()
        self.say("Jippie, dat is precies zoals het moet.")
        self.speechLock.acquire()

    # Start of the game
    def start_game(self):
        # Set language to Dutch
        self.set_language('nl-NL')
        self.langLock.acquire()

        if self.first_time:
            self.explain_game()

        self.playing = True

        # Put robot in right position for host
        self.do_gesture("simonsayshost-a4203c/check-autonomous")
        self.movementLock.acquire()
        self.set_autonomous_life_off()
        self.movementLock.acquire()
        self.do_gesture("simonsayshost-a4203c/sit-down")
        self.movementLock.acquire()

        # Start of game message
        self.say("Laten we beginnen. Druk op mijn hoofd om the stoppen!")
        self.speechLock.acquire()

        # Call button and wait for response
        while(self.playing):
            if self.host:
                if self.create_mole():
                    self.score += 1
                else:
                    break
            else:
                if self.guess():
                    self.score += 1
                else:
                    break

        if self.playing:
            if self.can_press:
                self.say(
                    "Ah jammer, je was niet snel genoeg. Je score was {:d}!".format(self.score))
            else:
                self.say(
                    "Ah jammmer, dat was de verkeerde knop. Je score was {:d}!".format(self.score))
        else:
            self.say("Oké, we stoppen.")
        self.speechLock.acquire()
        self.score = 0

    # On return of an event perform this function
    def on_robot_event(self, event):
        if event == "LanguageChanged":
            print("test")
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

    # When there is an audio intent found that corresponds with the current context,
    # perform a certain action.
    def on_audio_intent(self, *args, intentName):
        print("Intent: ", intentName)
        if intentName == 'make_move' and len(args) > 0:
            print(args[0])
            self.move_to_make = args[0]
            self.turnLock.release()


if __name__ == "__main__":
    wam = SimonSays()
    wam.start()
    wam.start_game()
    wam.stop()
