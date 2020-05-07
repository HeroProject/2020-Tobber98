import random 

class Simon(Base.AbstractApplication):
    def __init__(self):
        self.score = 0
        self.buttons = ["bl", "br", "tl", "tr"] # Could potentially do head as well
        self.sequence = []

    def add_button(self):
        self.sequence.append(self.buttons[random.randrange(0, 4)])
        print("The newly added button is {:s}".format(self.sequence[-1]))

    def new_round(self):
        self.add_button()
        for current in self.sequence:
            # Should be done with a timer but not rigtht now
            button_pressed = input("Press the next button: ")
            if button_pressed != current:
                print("Wrong, game over!")
                return False
        return True 
        
    def start(self):
        while(True):
            if not self.new_round():
                break
            print("Good job! Next round.")



        

simon = Simon()
simon.start()
