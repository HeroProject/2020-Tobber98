from social_interaction_cloud.action import ActionRunner
from social_interaction_cloud.basic_connector import BasicSICConnector


class Example:
    """Example that uses speech recognition. Prerequisites are the availability of a dialogflow_key_file,
    a dialogflow_agent_id, and a running Dialogflow service. For help meeting these Prerequisites see
    https://socialrobotics.atlassian.net/wiki/spaces/CBSR/pages/260276225/The+Social+Interaction+Cloud+Manual"""

    def __init__(self, server_ip, robot, dialogflow_key_file, dialogflow_agent_id):
        self.sic = BasicSICConnector(server_ip, robot, dialogflow_key_file, dialogflow_agent_id)

        self.user_model = {}

    def run(self):
        self.sic.start()
        action_runner = ActionRunner(self.sic)
        action_runner.load_waiting_action('set_language', 'en-US')
        action_runner.load_waiting_action('wake_up')
        action_runner.run_loaded_actions()

        action_runner.run_waiting_action('say', 'Hi I am Nao. What is your name?')
        action_runner.run_waiting_action('speech_recognition', 'answer_name', 3, additional_callback=self.on_intent)
        action_runner.run_waiting_action('say', 'Nice to meet you ' + self.user_model['name'])

        action_runner.run_waiting_action('rest')
        self.sic.stop()

    def on_intent(self, intent_name, *args):
        if intent_name == 'answer_name' and len(args) > 0:
            self.user_model['name'] = args[0]


example = Example('<SIC IP Address>',
                  'nao',
                  '<dialogflow_key_file.json>',
                  '<dialogflow_agent_id>')
example.run()
