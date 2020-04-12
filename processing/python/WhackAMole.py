import AbstractApplication as Base
from threading import Semaphore
import random
import time

class WhackAMole(Base.AbstractApplication):
    def __init__(self):
        super(WhackAMole, self).__init__(serverIP='192.168.56.102')
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
        print(self.current_button)
        # Turn on the leds of the defined button on the robot and check for button presses on the robot for a certain amount of time.
        # Listen for input
        new_input = "br" # would normally be the pushed button
        if new_input == self.current_button:
            return True
        time.sleep(self.generate_random(1, 2))
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

wam = WhackAMole()
wam.start()
wam.stop()