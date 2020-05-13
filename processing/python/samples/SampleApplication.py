import AbstractApplication as Base
from threading import Semaphore


class DialogFlowSampleApplication(Base.AbstractApplication):
    def __init__(self):
        super(DialogFlowSampleApplication, self).__init__(serverIP='192.168.0.200')

    def main(self):
        # Set the correct language (and wait for it to be changed)
        self.langLock = Semaphore(0)
        self.setLanguage('nl-NL')
        self.langLock.acquire()

        # Pass the required Dialogflow parameters (add your Dialogflow parameters)
        self.setDialogflowKey('ronald-ywcxbh-a2ca41d812bb.json')
        self.setDialogflowAgent('ronald-ywcxbh')

        # Make the robot ask the question, and wait until it is done speaking
        self.speechLock = Semaphore(0)
        self.sayAnimated('Hello, what is your name?')
        self.speechLock.acquire()

        # Listen for an answer for at most 5 seconds
        self.name = None
        self.nameLock = Semaphore(0)
        self.setAudioContext('answer_name')
        self.startListening()
        self.nameLock.acquire(timeout=5)
        self.stopListening()
        # wait one more second after stopListening (if needed)
        if not self.name:
            self.nameLock.acquire(timeout=1)

        # Respond and wait for that to finish
        if self.name:
            self.sayAnimated('Nice to meet you ' + self.name + '!')
        else:
            self.sayAnimated('Sorry, I didn\'t catch your name.')
        self.speechLock.acquire()

        # Display a gesture (replace <gestureID> with your gestureID)
        self.gestureLock = Semaphore(0)
        self.doGesture('<gestureID>/behavior_1')
        self.gestureLock.acquire()

    def onRobotEvent(self, event):
        if event == 'LanguageChanged':
            self.langLock.release()
        elif event == 'TextDone':
            self.speechLock.release()
        elif event == 'GestureDone':
            self.gestureLock.release()

    def onAudioIntent(self, *args, intentName):
        if intentName == 'answer_name' and len(args) > 0:
            self.name = args[0]
            self.nameLock.release()


# Run the application
sample = DialogFlowSampleApplication()
sample.main()
sample.stop()
