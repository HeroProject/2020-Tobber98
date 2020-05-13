from transitions import Machine
from social_interaction_cloud.action import ActionRunner
from social_interaction_cloud.basic_connector import BasicSICConnector


class ExampleRobot(object):
    """Example that shows how to impelement a State Machine with pyTransitions. For more information go to
    https://socialrobotics.atlassian.net/wiki/spaces/CBSR/pages/616398873/Python+Examples#State-Machines-with-PyTransitions"""

    states = ['asleep', 'awake', 'introduced', 'got_acquainted', 'goodbye']

    def __init__(self, sic: BasicSICConnector):
        self.sic = sic
        self.action_runner = ActionRunner(self.sic)
        self.machine = Machine(model=self, states=ExampleRobot.states, initial='asleep')

        self.user_model = {}

        # Define transitions
        self.machine.add_transition(trigger='start', source='*', dest='awake',
                                    before='wake_up', after='introduce')
        self.machine.add_transition(trigger='introduce', source='awake', dest='introduced',
                                    before='introduction', after='get_acquainted')
        self.machine.add_transition(trigger='get_acquainted', source='introduced', dest='got_acquainted',
                                    before='getting_acquainted', after='say_goodbye')
        self.machine.add_transition(trigger='say_goodbye', source='got_acquainted', dest='goodbye',
                                    before='saying_goodbye', after='rest')
        self.machine.add_transition(trigger='rest', source='*', dest='asleep',
                                    before='stop')

    def wake_up(self):
        self.action_runner.load_waiting_action('set_language', 'en-US')
        self.action_runner.load_waiting_action('wake_up')
        self.action_runner.run_loaded_actions()

    def introduction(self):
        self.action_runner.run_waiting_action('say_animated', 'Hi I am Nao and I am a social robot.')

    def getting_acquainted(self):
        self.action_runner.run_waiting_action('say_animated', 'What is your name?')
        self.action_runner.run_waiting_action('speech_recognition', 'answer_name', 3,
                                              additional_callback=self.on_intent)
        self.action_runner.run_waiting_action('say_animated', 'Nice to meet you ' + self.user_model['name'])

    def on_intent(self, intent_name, *args):
        if intent_name == 'answer_name' and len(args) > 0:
            self.user_model['name'] = args[0]

    def saying_goodbye(self):
        self.action_runner.run_waiting_action('say_animated', 'Well this was fun.')
        self.action_runner.run_waiting_action('say_animated', 'I will see you around.')

    def stop(self):
        self.action_runner.run_waiting_action('rest')


class StateMachineExample(object):

    def __init__(self, server_ip, robot, dialogflow_key_file, dialogflow_agent_id):
        self.sic = BasicSICConnector(server_ip, robot, dialogflow_key_file, dialogflow_agent_id)
        self.sic.start()
        self.robot = ExampleRobot(self.sic)

    def run(self):
        self.robot.start()
        self.sic.stop()


example = StateMachineExample('192.168.178.45',
                              'nao',
                              'dialogflowagent.json',
                              'mikeagent-dsvpjs')
example.run()
