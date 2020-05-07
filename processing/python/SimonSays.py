import AbstractApplication as Base
from threading import Semaphore
import random
import time


class SimonSays(Base.AbstractApplication):
    def __init__(self):
        super(SimonSays, self).__init__(serverIP='192.168.0.200')

        self.score = 0
        self.speedup = 0
        self.host = True
        self.can_press = False

        self.ingame_buttons = ["bl", "br", "tl", "tr"]
        self.physical_buttons_pressed = ["RightBumperPressed", "LeftBumperPressed", "HandRightBackPressed"
                                         "HandRightLeftTouched", "HandRightRightTouched", "HandLeftLeftTouched",
                                         "HandLeftRightTouched", "HandLeftBackPressed"]

        self.physical_buttons_released = ["RightBumperReleased", "LeftBumperReleased", "HandRightBackReleased",
                                          "HandRightLeftReleased", "HandRightRightReleased", "HandLeftLeftReleased",
                                          "HandLeftRightReleased", "HandLeftBackReleased"]

        self.current_button = None
        self.button_pressed = None

        self.move_to_make = None

        self.setDialogflowKey('ronald-ywcxbh-a2ca41d812bb.json')
        self.setDialogflowAgent('ronald-ywcxbh')

    # Generate rondom float between min and max values given
    def generate_random(self, min, max):
        if self.score * 0.05 < min - 0.5:
            self.speedup = self.score * 0.05
        return round(abs(random.uniform(min - self.speedup, max - self.speedup)), 2)

    def physical_to_ingame(self, button):
        if button == "RightBumperPressed":
            return "br"
        elif button == "LeftBumperPressed":
            return "bl"
        elif button in ("HandRightBackTouched", "HandRightLeftTouched", "HandRightRightTouched"):
            return "tr"
        elif button in ("HandLeftBackTouched", "HandLeftLeftTouched", "HandLeftRightTouched"):
            return 'tl'

    # Generate single turn of the game
    def create_mole(self):
        time.sleep(self.generate_random(1.5, 2.5))
        self.current_button = self.ingame_buttons[random.randrange(0, 4)]

        # Say the the button to press, left/right is reversed.
        word_to_say = ""
        if self.current_button == "br":
            word_to_say = "Linkervoet!"
        elif self.current_button == "bl":
            word_to_say = "Rechtervoet!"
        elif self.current_button == "tr":
            word_to_say = "Linkerhand!"
        else:
            word_to_say = "Rechterhand!"

        self.say(word_to_say)
        self.speechLock.acquire()

        t = self.generate_random(3, 6)
        self.can_press = True
        self.setLeds({'name': 'rotate', 'colour': 0x0033FF33,
                      'rotation_time': 1, 'time': t})
        self.buttonLock.acquire(timeout=t)
        if self.current_button == self.physical_to_ingame(self.button_pressed):
            return True
        return False

    def guess(self):
        self.say("Ik luister.")
        self.speechLock.acquire()
        self.turnLock = Semaphore(0)
        self.setAudioContext("make_move")
        self.setAudioHints("linkervoet", "rechtervoet",
                           "linkerhand", "rechterhand", "fout")
        self.startListening()
        self.setLeds({'name': 'rotate', 'colour': 0x0033FF33,
                      'rotation_time': 1, 'time': 5.0})
        self.turnLock.acquire(timeout=5)
        self.stopListening()

        if self.move_to_make == "fout":
            self.say("Ah jammer, nu mag jij weer!")
            self.speechLock.acquire()
            self.host = True
            return False

        elif self.move_to_make == "linkervoet":
            self.doGesture("simonsayshost-a4203c/move-left-foot")
            self.movementLock.acquire()

        elif self.move_to_make == "rechtervoet":
            self.doGesture("simonsayshost-a4203c/move-right-foot")
            self.movementLock.acquire()

        elif self.move_to_make == "linkerhand":
            self.doGesture("simonsayshost-a4203c/move-left-arm")
            self.movementLock.acquire()

        elif self.move_to_make == "rechterhand":
            self.doGesture("simonsayshost-a4203c/move-right-arm")
            self.movementLock.acquire()

        else:
            self.say("Sorry, ik kon je niet goed horen!")
            self.speechLock.acquire()

        # Listen if correct?
        return True

    # Start of the game
    def start(self):
        self.playing = True

        # Set language to Dutch
        self.langLock = Semaphore(0)
        self.setLanguage('nl-NL')
        self.langLock.acquire()

        # Put robot in right position for host
        self.movementLock = Semaphore(0)
        self.doGesture("simonsayshost-a4203c/sit-down")
        self.movementLock.acquire()

        # Start of game message
        self.speechLock = Semaphore(0)
        self.say("Laten we beginnen. Druk op alles wat ik zeg! Als je wilt stoppen hoef je alleen maar op mijn hoofd te drukken.")
        self.speechLock.acquire()

        # Call button and wait for response
        self.buttonLock = Semaphore(0)
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
    def onRobotEvent(self, event):
        if event == "LanguageChanged":
            self.langLock.release()

        if event == "TextDone":
            self.speechLock.release()

        if event in self.physical_buttons_pressed:
            print("... {}".format(event))
            if self.can_press:
                print("And this came through: {} ...".format(event))
                self.can_press = False
                self.setLeds({'name': 'fade', 'group': 'FaceLeds',
                              'colour': 0x000011FF, 'time': .05})
                self.button_pressed = event
                self.buttonLock.release()

        if event in self.physical_buttons_released:
            print("... ", event)
            self.setLeds({'name': 'off', 'group': 'FaceLeds'})

        if event in ["FrontTactilTouched", "MiddleTactilTouched", "RearTactilTouched"]:
            self.playing = False

        if event == "GestureDone":
            self.movementLock.release()

    # When there is an audio intent found that corresponds with the current context,
    # perform a certain action.
    def onAudioIntent(self, *args, intentName):
        print("Intent: ", intentName)
        if intentName == 'make_move' and len(args) > 0:
            print(args[0])
            self.move_to_make = args[0]
            self.turnLock.release()


if __name__ == "__main__":
    wam = SimonSays()
    wam.start()
    wam.stop()
