import AbstractApplication as Base
from threading import Semaphore
import random
import time

class Test(Base.AbstractApplication):
    def __init__(self):
        super(Test, self).__init__(serverIP='192.168.0.200')
        self.buttons = ["RightBumperPressed", "LeftBumperPressed", "BackBumperPressed", "FrontTactilTouched",
        "MiddleTactilTouched", "RearTactilTouched", "HandRightBackTouched", "HandRightLeftTouched", 
        "HandRightRightTouched", "HandLeftLeftTouched", "HandLeftRightTouched", "HandLeftBackTouched"]
        self.button_pressed = None

    # Start of the game
    def start(self):
        self.setLeds(["FaceLeds", "blue", "1"])
        # self.getAngles()
        self.buttonLock = Semaphore(0)
        while(True):
            self.buttonLock.acquire()
            print(self.button_pressed)

    
    # On return of an event perform this function
    def onRobotEvent(self, event):
        if event in self.buttons:
            self.button_pressed = event
            self.buttonLock.release()

    # def onGetAngles(self, angles):
    #     print(angles)

if __name__ == "__main__":
    wam = Test()
    wam.start()
    wam.stop()