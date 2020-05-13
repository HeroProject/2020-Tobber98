import AbstractApplication as Base
from threading import Semaphore

class DialogFlowSampleApplication(Base.AbstractApplication):
    def __init__(self):
        super(DialogFlowSampleApplication, self).__init__(
            serverIP='192.168.0.25')

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
        self.sayAnimated('Hoi, wat is jouw naam?')
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
            self.sayAnimated('Leuk je te ontmoeten, ' + self.name + '! Ik ben Ronald de robot.')
        else:
            self.sayAnimated('Sorry, ik heb je niet verstaan.')
        self.speechLock.acquire()

        self.sayAnimated("Zullen we een spelletje spelen? Het heet Commando Ronald en ik wil het je wel uitleggen.")
        self.speechLock.acquire()

        #self.response 

        # Display a gesture (replace <gestureID> with your gestureID)
        self.gestureLock = Semaphore(0)
        # self.doGesture('<gestureID>/behavior_1')
        self.gestureLock.acquire(timeout=1)

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

        elif intentName == "ask_to_play" and len(args) > 0:
            pass
            
    def askToPlay(self, *args, intentPlay):
        if intentPlay:
            pass




# Run the application
sample = DialogFlowSampleApplication()
sample.main()
sample.stop()
