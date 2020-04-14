import AbstractApplication as Base
from threading import Semaphore
import random
import time

class WhackAMole(Base.AbstractApplication):
    def __init__(self):
        super(WhackAMole, self).__init__(serverIP='192.168.56.102')
        # super(WhackAMole, self).__init__(serverIP='127.0.0.1')
        self.score = 0
        self.speedup = 0
        self.buttons = ["bl", "br", "tl", "tr"] # Could potentially do head as well
        self.current_button = None

    def generate_random(self, min, max):
        if self.score * 0.05 < min - 0.5:
            self.speedup = self.score * 0.05
        return round(random.uniform(min - self.speedup, max - self.speedup), 2)

    def create_mole(self):
        time.sleep(self.generate_random(.2, 2)) # could be lock instead of sleep
        self.current_button = self.buttons[random.randrange(0, 4)]
        
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
        
        self.buttonLock.acquire(timeout=self.generate_random(1,2))
        if self.current_button == self.button_pressed:
            return True
        return False

    def start(self):
        #Set language to Dutch
        self.langLock = Semaphore(0)
        self.setLanguage('nl-NL')
        self.langLock.acquire()

        # Speech
        self.speechLock = Semaphore(0)
        self.say("Laten we beginnen. Sla alles wat oplicht.")
        self.speechLock.acquire()

        self.buttonLock = Semaphore(0)
        while(True):
            hit = self.create_mole()
            if hit:
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
        self.buttons2 = ["RightBumperPressed", "LeftBumperPressed", "BackBumperPressed", "FrontTactilTouched",
        "MiddleTactilTouched", "RearTactilTouched", "HandRightBackTouched", "HandRightLeftTouched", 
        "HandRightRightTouched", "HandLeftLeftTouched", "HandLeftRightTouched", "HandLeftBackTouched"]
        if event in self.buttons2:
            self.button_pressed = event
            self.buttonLock.release()

wam = WhackAMole()
wam.start()
wam.stop()