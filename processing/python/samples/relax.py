import AbstractApplication as Base
from threading import Semaphore
import random
import time

class Test(Base.AbstractApplication):
    def __init__(self):
        super(Test, self).__init__(serverIP='192.168.0.200')

    # Start of the game
    def start(self):
        self.buttonLock = Semaphore(0)
        self.setIdle()
        self.setRest()
        self.buttonLock.acquire()

    
    # On return of an event perform this function
    def onRobotEvent(self, event):
        if event == "SetIdle":
            self.buttonLock.release()

    # def onGetAngles(self, angles):
    #     print(angles)

if __name__ == "__main__":
    wam = Test()
    wam.start()
    wam.stop()