import time

from social_interaction_cloud.action import ActionRunner
from social_interaction_cloud.basic_connector import BasicSICConnector


class Example:
    """For this example you will need to turn on the PeopleDetection and FaceRecognition services on the
    Social Interaction Cloud webportal"""

    def __init__(self, server_ip, robot):
        self.sic = BasicSICConnector(server_ip, robot)

    def run(self):
        self.sic.start()
        action_runner = ActionRunner(self.sic)

        action_runner.run_waiting_action('set_language', 'en-US')
        action_runner.run_vision_listener('people', self.i_spy_with_my_little_eye, False)
        action_runner.run_waiting_action('say', 'Hello, I see you')

        action_runner.run_vision_listener('face', self.face_recognition, True)
        time.sleep(10)

        self.sic.stop()

    def i_spy_with_my_little_eye(self):
        print("I see someone!")

    def face_recognition(self, identifier):
        if identifier != '0':
            print("I recognize you as " + identifier)
        else:
            print("I don't recognize you")


example = Example('<SIC IP Address>', 'nao')
example.run()
