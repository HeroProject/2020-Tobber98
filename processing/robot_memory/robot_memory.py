import argparse
import ast
from datetime import datetime
import time
import redis
from signal import signal, SIGTERM, SIGINT, pause


class EntryIncorrectFormatError(Exception):
    """Raised when the received memory entry has an incorrect format"""
    pass


class UserDoesNotExistError(Exception):
    """Raised when a database operation is attempted on a non existing user"""
    pass


class RobotMemory:

    def __init__(self, server):
        # Redis initialization
        self.redis = redis.Redis(host=server, ssl=True, ssl_ca_certs='../cert.pem')
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(**{'memory_add_entry': self.entry_handler,
                                 'memory_user_session': self.get_user_session,
                                 'memory_set_user_data': self.set_user_data,
                                 'memory_get_user_data': self.get_user_data})
        self.pubsub_thread = self.pubsub.run_in_thread(sleep_time=0.001)

        # Register cleanup handlers
        signal(SIGTERM, self.cleanup)
        signal(SIGINT, self.cleanup)

        # Flag that everything is running
        self.running = True

    def run(self):
        while self.running:
            pause()

    def get_user_session(self, message):
        try:
            # retrieve data from message
            user_key = 'user:' + self.get_data(message, 1, correct_format='user_id')[0]

            timestamp = str(datetime.now())
            # check if user exists and if they exist return their session number
            if self.redis.exists(user_key):
                with self.redis.pipeline() as pipe:
                    pipe.hincrby(user_key, 'session_number', amount=1)
                    pipe.hset(user_key, 'last_interaction', timestamp)
                    result = pipe.execute()
                self.produce_data('session_number', str(result[0]))
            # if user does not exist, create it, and return the session number of 1 (first session)
            else:
                self.redis.hmset(user_key, {'creation_date': timestamp,
                                            'last_interaction': timestamp,
                                            'session_number': '1'})
                self.produce_data('session_number', '1')
        except (EntryIncorrectFormatError, redis.DataError) as err:
                print('Could not retrieve user session: ' + err.message)

    def entry_handler(self, message):
        try:
            # retrieve data from message
            data = self.get_data(message, 3, 'user_id;entry_name;entry')
            # a user needs to exist to link the entry to.
            user_key = 'user:' + data[0]
            if not(self.redis.exists(user_key)):
                raise UserDoesNotExistError('User with ID ' + user_key + 'does not exist')

            # generate the latest hash id for this particular entry type
            entry_key = data[1]
            count = self.redis.hincrby(user_key, entry_key, 1)
            hash_name = entry_key + ':' + data[0] + ':' + str(count)

            # the supplied data needs to have the form a a dict.
            entry = ast.literal_eval(data[2])
            if not(isinstance(entry, dict)):
                raise EntryIncorrectFormatError('Entry is not a dict.')
            entry.update({'datetime': str(datetime.now())})  # timestamp the entry

            # store the entry dict as a hash in redis with hash name: entry_type:user_id:entry_id
            self.redis.hmset(hash_name, entry)
            self.produce_event('MemoryEntryStored')

        except(ValueError, SyntaxError, EntryIncorrectFormatError) as err:
                print('Memory entry does not have the right format: ' + err.message)
        except (redis.DataError, UserDoesNotExistError) as err:
                print('The database action failed: ' + err.message)

    def set_user_data(self, message):
        try:
            data = self.get_data(message, 3, 'user_id;key;value')
            self.redis.hset('user:' + data[0], data[1], data[2])
            self.produce_event('UserDataSet')
        except (EntryIncorrectFormatError, redis.DataError) as err:
            print('User data could not be set due to: ' + err.message)

    def get_user_data(self, message):
        try:
            data = self.get_data(message, 2, 'user_id;key')
            value = self.redis.hget('user:' + data[0], data[1])
            self.produce_data(data[1], value)
        except EntryIncorrectFormatError as err:
            print('Could not get user data due to: ' + err.message)

    def produce_event(self, value):
        self.redis.publish('events_memory', value)

    def produce_data(self, key, value):
        self.redis.publish('memory_data', str(key) + ';' + str(value))

    @staticmethod
    def get_data(message, correct_length, correct_format=''):
        data = message['data'].split(';')
        if len(data) != correct_length:
            raise EntryIncorrectFormatError('Data does not have format ' + correct_format)
        return data

    def cleanup(self, signum, frame):
        if self.running:
            self.running = False
            print('Trying to exit gracefully...')
            try:
                self.pubsub_thread.stop()
                self.redis.close()
                print('Graceful exit was successful.')
            except redis.RedisError as err:
                print('A graceful exit has failed due to: ' + err.message)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', type=str, default='localhost', help='Server IP address. Default is localhost.')
    args = parser.parse_args()

    robot_memory = RobotMemory(args.server)
    robot_memory.run()
