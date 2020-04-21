import AbstractApplication as Base
from threading import Semaphore
import random
import time

class SimonSays(Base.AbstractApplication):
    def __init__(self):
        super(SimonSays, self).__init__(serverIP='192.168.0.13')
        # super(SimonSays, self).__init__(serverIP='127.0.0.1')
        self.score = 0
        self.speedup = 0
        self.ingame_buttons = ["bl", "br", "tl", "tr"] # Could potentially do head as well
        self.physical_buttons = ["RightBumperPressed", "LeftBumperPressed", "HandRightBackTouched", 
        "HandRightLeftTouched", "HandRightRightTouched", "HandLeftLeftTouched", 
        "HandLeftRightTouched", "HandLeftBackTouched"]
        # self.buttons2 = ["RightBumperPressed", "LeftBumperPressed"8, "FrontTactilTouched",
        # "MiddleTactilTouched", "RearTactilTouched", "HandRightBackTouched", "HandRightLeftTouched", 
        # "HandRightRightTouched", "HandLeftLeftTouched", "HandLeftRightTouched", "HandLeftBackTouched"]
        self.current_button = None
        self.button_pressed = None

    # Generate rondom float between min and max values given
    def generate_random(self, min, max):
        if self.score * 0.05 < min - 0.5:
            self.speedup = self.score * 0.05
        return round(random.uniform(min - self.speedup, max - self.speedup), 2)

    def physical_to_ingame(self, button):
        print("In the function: ", button)
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
        time.sleep(self.generate_random(.2, 2)) # could be lock instead of sleep
        self.current_button = self.ingame_buttons[random.randrange(0, 4)]

        
        #Say the the button to press
        word_to_say = ""
        if self.current_button == "bl":
            word_to_say = "Linkervoet!"
        elif self.current_button == "br":
            word_to_say = "Rechtervoet!"
        elif self.current_button == "tl":
            word_to_say = "Linkerhand!"
        else:
            word_to_say = "Rechterhand!"
        self.say(word_to_say)
        self.speechLock.acquire()

        print(self.current_button)
        
        self.buttonLock.acquire(timeout=self.generate_random(5,10))
        print("Current button to press: {}\nButton pressed: {}".format(self.current_button, self.button_pressed))
        if self.current_button == self.physical_to_ingame(self.button_pressed):
            return True
        print("test 2")
        return False

    # Start of the game
    def start(self):
        #Set language to Dutch
        self.langLock = Semaphore(0)
        self.setLanguage('nl-NL')
        self.langLock.acquire()

        # Start of game message
        self.speechLock = Semaphore(0)
        self.say("Laten we beginnen. Sla alles wat oplicht.")
        self.speechLock.acquire()

        # Call button and wait for response
        self.buttonLock = Semaphore(0)
        while(True):
            # hit = self.create_mole()
            if self.create_mole():
                self.score += 1
            else:
                break

        self.say("Ah jammer, je was niet snel genoeg. Je score was {:d}!".format(self.score))
        self.speechLock.acquire()
    
    # On return of an event perform this function
    def onRobotEvent(self, event):
        if event == "LanguageChanged":
            self.langLock.release()
        if event == "TextDone":
            self.speechLock.release()
        if event in self.physical_buttons:
            # Stop listening for a short while after getting input!
            print(event)
            self.button_pressed = event
            self.buttonLock.release()


if __name__ == "__main__":
    wam = SimonSays()
    wam.start()
    wam.stop()