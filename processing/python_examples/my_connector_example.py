from social_interaction_cloud.abstract_connector import AbstractSICConnector
from time import sleep


class MyConnector(AbstractSICConnector):
    """This example shows you how to create your won SIC connector by inheriting AbstractSICConnector.
    For more information go to
    https://socialrobotics.atlassian.net/wiki/spaces/CBSR/pages/616398873/Python+Examples#Abstract-SIC-Connector"""
    def __init__(self, server_ip, robot):
        super(MyConnector, self).__init__(server_ip, robot)

    def run(self):
        self.start()
        self.set_language('en-US')
        sleep(1)  # wait for the language to change
        self.say('Hello, world!')
        sleep(3)  # wait for the robot to be done speaking (to see the relevant prints)
        self.stop()

    def on_robot_event(self, event):
        print(event)


# Run the application
my_connector = MyConnector(server_ip='<SIC IP Address>', robot='nao')
my_connector.run()
