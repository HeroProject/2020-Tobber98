# import AbstractApplication as Base
import abstract_connector as Base
from threading import Semaphore
import random
import time

import sys
import pandas as pd
from datetime import datetime


class SimonSays(Base.AbstractSICConnector):  # AbstractApplication):
    def __init__(self):
        super(SimonSays, self).__init__(server_ip='192.168.0.200', robot='nao')

        # Dialogflow data
        self.set_dialogflow_key('ronald-ywcxbh-de715f4ba54d.json')
        self.set_dialogflow_agent('ronald-ywcxbh')

        # Booleans to determine who is host and if explanation is needed
        self.first_time = False
        self.host = True

        # data collection
        self.start_time = time.time()
        self.scores = []
        self.times_player = 0
        self.times_host = 0
        self.min_difficulty = 2
        self.max_difficulty = 2
        self.times_missed_button = 0
        self.times_too_late = 0
        self.times_spoken = 0
        self.times_misheard = 0

        # Elements of the game that need to be tracked
        self.high_score = 0
        self.score = 0
        self.robot_score = 0
        self.speedup = 0
        self.consecutive_missed = 0
        self.can_press = False
        self.current_button = None
        self.button_pressed = None
        self.response = None

        # Difficulty management
        self.difficulty = 2  # Level range 0 to 4
        self.lives = [3, 2, 1, 1, 1]
        self.time_to_press = [10, 8, 5, 5, 2]
        self.flipped = [False, False, False, True, True]
        self.lives_left = self.lives[self.difficulty]

        # Available buttons to press and release in game
        self.ingame_buttons = {
            "bl": "Rechtervoet", "br": "Linkervoet", "tl": "Rechterhand", "tr": "Linkerhand"}
        self.button_dict = {"RightBumperPressed": "br", "LeftBumperPressed": "bl", "HandRightBackPressed": "tr",
                            "HandRightLeftTouched": "tr", "HandRightRightTouched": "tr", "HandLeftLeftTouched": "tl",
                            "HandLeftRightTouched": "tl", "HandLeftBackPressed": "tl"}
        self.physical_buttons_released = ["RightBumperReleased", "LeftBumperReleased", "HandRightBackReleased",
                                          "HandRightLeftReleased", "HandRightRightReleased", "HandLeftLeftReleased",
                                          "HandLeftRightReleased", "HandLeftBackReleased"]
        self.speech_dict = {"linkervoet": "move-right-foot", "rechtervoet": "move-left-foot",
                            "linkerhand": "move-right-arm", "rechterhand": "move-left-arm"}

        # Created locks
        self.listenLock = Semaphore(0)
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

    def listen(self, context=None, hints=None, time=5):
        self.set_audio_context(context)
        self.set_audio_hints(*hints)
        self.start_listening()
        self.set_leds({'name': 'rotate', 'colour': 0x0033FF33,
                       'rotation_time': 1, 'time': time})
        self.listenLock.acquire(timeout=time)
        self.stop_listening()
        self.listenLock.acquire(timeout=1)

    # Generate single turn of the game
    def create_mole(self):
        self.current_button = None
        time.sleep(self.generate_random(1.5, 2.5))

        self.current_button = list(self.ingame_buttons)[random.randrange(0, 4)]
        if random.getrandbits(1) and self.flipped[self.difficulty]:
            flipped_button = self.current_button[0] + 'l' if self.current_button[1] == 'r' else self.current_button[0] + 'r'
            self.say("Mijn" + self.ingame_buttons[flipped_button] + '!')
        else:
            self.say(self.ingame_buttons[self.current_button] + '!')
        self.speechLock.acquire()

        t = self.time_to_press[self.difficulty] - self.score * 0.1 if self.time_to_press[self.difficulty] - self.score * 0.1 > 1 else 1
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
        self.response = None
        self.button_pressed = None
        self.say("Ik luister.")
        self.speechLock.acquire()
        self.times_spoken += 1

        self.listen("make_move", ("linkervoet", "rechtervoet", "linkerhand", "rechterhand", "fout"))

        if self.button_pressed in ["FrontTactilTouched", "MiddleTactilTouched", "RearTactilTouched"]:
            return False

        if self.response == "fout" or self.button_pressed in list(self.button_dict):
            self.say("Ah jammer.")
            self.speechLock.acquire()
            return False

        if self.response in list(self.speech_dict):
            self.consecutive_missed = 0
            self.do_gesture("simonsayshost-a4203c/" +
                            self.speech_dict[self.response])
            self.movementLock.acquire()
            self.robot_score += 3
        elif  self.consecutive_missed > 2 or self.robot_score > 10:
            self.consecutive_missed = 0
            self.do_gesture("simonsayshost-a4203c/" + list(self.speech_dict.values())[random.randrange(0, 4)])
            self.movementLock.acquire()
        else:
            self.consecutive_missed += 1
            self.say("Sorry, ik kon je niet goed horen!")
            self.speechLock.acquire()
            self.times_misheard += 1
        return True

    # Explanation of the game where the robot shows what the player is supposed to do
    def explain_game(self):
        self.say("Hé, leuk dat je *spelnaam* met mij wil spelen. \
            Ik zal het proberen uit te leggen. Er zijn twee manieren om het spel te spelen. \
            De eerste manier is dat ik zeg wat jij aan moet tikken en de tweede manier is dat jij zegt wat ik moet bewegen.")
        self.speechLock.acquire()

        self.set_leds({"name": "rotate", "colour": 0x0033FF33,
                       "rotation_time": 1, "time": 4})
        self.say("Mijn ogen zullen draaien, zoals ze nu doen, als je kunt drukken op mijn knoppen. \
                Hetzelfde geldt voor wanneer ik luister terwijl jij spelleider bent. \
                Laten we beginnen met een oefenronde. Ik zeg iets en jij moet op de knop drukken.")
        self.speechLock.acquire()

        while not self.create_mole():
            if self.can_press:
                self.can_press = False
                self.say(
                    "Je was niet snel genoeg. We proberen het nog een keer.")
                self.speechLock.acquire()
            else:
                self.say(
                    "Dat was de verkeerde knop. We proberen het nog een keer.")
                self.speechLock.acquire()
        self.say("Zo moet het.")
        self.speechLock.acquire()

    def run_until_quit(self):
        # Call button and wait for response
        while(self.playing):
            while True:
                if self.host:
                    if self.create_mole():
                        self.score += 1
                    else:
                        self.lives_left -= 1
                        if self.lives_left > 0:
                            continue
                        else:
                            self.times_player += 1
                            if self.score > self.high_score:
                                self.high_score = self.score
                            break
                else:
                    if not self.guess():
                        self.times_host += 1
                        break
                
                if not self.playing:
                    break

            if self.playing:
                if self.can_press and self.host:
                    self.say(
                        "Je was niet snel genoeg. Je score was {:d}!".format(self.score))
                    self.speechLock.acquire()
                    self.times_too_late += 1
                elif self.host:
                    self.say(
                        "Dat was de verkeerde knop. Je score was {:d}!".format(self.score))
                    self.speechLock.acquire()
                    self.times_missed_button += 1
                self.say("Okay, we wisselen.")
                self.current_button = None
                self.buttonLock = Semaphore(0)
                self.host = not self.host
                self.scores.append(self.score)
                self.score = 0
                self.robot_score = 0
                self.speechLock.acquire()
                print(self.host)
                if self.host:
                    self.say("Welk niveau wil je spelen, kies een getal tussen 1 tot 5.")
                    self.speechLock.acquire()
                    self.response = None
                    self.choose_difficulty = True
                    self.listen("choose_level", ('1', '2', '3', '4', '5'))

                    if self.response:
                        self.difficulty = int(self.response) - 1
                        self.lives_left = self.lives[self.difficulty]
                        self.say("Het niveau is veranderd naar {}.".format(self.difficulty + 1))
                        if self.min_difficulty > self.difficulty:
                            self.min_difficulty = self.difficulty
                        if self.max_difficulty < self.difficulty:
                            self.max_difficulty = self.difficulty

                    else:
                        self.say("Ik kon je niet verstaan het niveau blijft {}.".format(self.difficulty + 1))
                    self.speechLock.acquire()
                    self.choose_difficulty = False

            else:
                self.say("Oké, we stoppen.")
                self.score = 0
                self.speechLock.acquire()
                break

    # Start of the game
    def start_game(self):
        # Set language to Dutch
        self.set_language('nl-NL')
        self.langLock.acquire()

        # Put robot in right position for host
        self.set_autonomous_life_off("get")
        self.movementLock.acquire()
        if self.autonomous:
            self.set_autonomous_life_off("set")
            self.movementLock.acquire()
        self.do_gesture("simonsayshost-a4203c/sit-down")
        self.movementLock.acquire()

        if self.first_time:
            self.explain_game()

        self.playing = True

        # Start of game message
        self.say("Laten we beginnen. Druk op mijn hoofd om the stoppen!")
        self.speechLock.acquire()

        self.run_until_quit()

    # On return of an event perform this function
    def on_robot_event(self, event):
        if event == "LanguageChanged":
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

        if event.split("|")[0] == "GetAutonomousLifeDisabled":
            self.autonomous = True if event.split("|")[1] == "True" else False
            self.movementLock.release()

    # When there is an audio intent found that corresponds with the current context,
    # perform a certain action.
    def on_audio_intent(self, *args, intent_name):
        print("Args: ", args)
        print("Intent: ", intent_name)

        if intent_name == 'make_move' and len(args) > 0:
            print(args[0])
            self.response = args[0]
            self.listenLock.release()

        elif intent_name == "choose_level" and len(args) > 0:
            try:
                self.response = int(args[0])
            except:
                self.response = None
    
    # Collects data at the end of the play interaction and appends it as row to excel file
    def collect_data(self, id):
        avg_score = sum(self.scores) / len(self.scores) if len(self.scores) > 0 else 0
        row_dict = {'id': id, 
            'time': datetime.now().strftime("%d/%m/%Y %H:%M:%S"), 
            'version': 'basic', 
            'play_time': time.time() - self.start_time, 
            'high_score': self.high_score, 
            'avg_score': avg_score, 
            'times_host': self.times_host, 
            'times_player': self.times_player, 
            'min_difficulty': self.min_difficulty, 
            'max_difficulty': self.max_difficulty, 
            'times_missed_button': self.times_missed_button, 
            'times_too_late': self.times_too_late, 
            'times_robot_feedback': 0,
            'times_spoken': self.times_spoken, 
            'times_misheard': self.times_misheard}

        df = pd.read_excel("simon_says_data.xlsx")
        df = df.append(pd.DataFrame([list(row_dict.values())], columns=list(df.columns)))
        df.to_excel("simon_says_data.xlsx", float_format="%.2f", columns=list(df.columns), index=False)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("No id was given")
        exit(0)

    wam = SimonSays()
    try:
        wam.start()
        wam.start_game()
        wam.stop()
    except:
        pass
    finally:
        wam.collect_data(sys.argv[1])