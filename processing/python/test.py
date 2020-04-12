import AbstractApplication as Base
from threading import Semaphore


class DialogFlowSampleApplication(Base.AbstractApplication):
    def __init__(self):
        super(DialogFlowSampleApplication, self).__init__(serverIP='192.168.0.25')

    def main(self):
        # Set the correct language (and wait for it to be changed)
        self.langLock = Semaphore(0)
        self.setLanguage('en-US')
        self.langLock.acquire()

    def onRobotEvent(self, event):
        if event == 'LanguageChanged':
            self.langLock.release()


# Run the application
sample = DialogFlowSampleApplication()
sample.main()
sample.stop()
