import sys
import os
import time
import argparse
from six.moves import queue
import threading
import redis

from google.cloud import speech_v1p1beta1 as speech # use the language detection feature (but still in beta)
from google.cloud.speech import enums
from google.cloud.speech import types

# fill the name of the json file containing the GAC (should be within the same directory as this file)
GOOGLE_APPLICATION_CREDENTIALS = 'simple interaction-fd6d5bcf29d0.json'

# See http://g.co/cloud/speech/docs/languages
# for a list of supported languages.
LANGUAGES = ['en-US', 'nl-NL']

class GoogleAsrEnvironmentKafka(object):
    def __init__(self, server, topics, languages):
        self.server = server
        self.redis = redis.Redis(host=server)
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(*topics)

        self.audio_stream = None
        self.rate = 16000 # hertz

        # Adds an environment variable containing the path to your google application credentials (GAC)
        self.credentials_file = GOOGLE_APPLICATION_CREDENTIALS
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '{}/{}'.format(os.getcwd(), self.credentials_file)

        # See http://g.co/cloud/speech/docs/languages
        # for a list of supported languages.
        self.main_language = languages[0]
        self.supported_languages = languages

        self.google_client = speech.SpeechClient()
        self.google_config = speech.types.RecognitionConfig(encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16, sample_rate_hertz=self.rate, language_code=self.main_language, alternative_language_codes=self.supported_languages)
        self.google_streaming_config = speech.types.StreamingRecognitionConfig(config=self.google_config)

    def update(self):
        msg = self.pubsub.get_message()
        if msg is not None:
            self.execute(msg)

    def execute(self, message):
        channel = message['channel']
        data = message['data']
        if channel == 'action_audio' and data == 'start listening':
            # Get (and publish) the audio transcript
            t1 = time.time()
            transcript = self.get_transcript()
            t2 = time.time()
            print 'time to get text back from Google:', t2 - t1
            self.redis.publish('text_speech', transcript)
        elif channel == 'audio_language':
            # Update the new supported language
            self.supported_languages = []
            self.main_language = data
            print '\tnew language', self.main_language
            # Reconfigure google client to the new single language received
            self.google_config = speech.types.RecognitionConfig(encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16, sample_rate_hertz=self.rate, language_code=self.main_language, alternative_language_codes=self.supported_languages)
            self.google_streaming_config = speech.types.StreamingRecognitionConfig(config=self.google_config)

    def run_forever(self):
        try:
            while True:
                self.update()
                time.sleep(0.001)
        except (KeyboardInterrupt, EOFError):
            print 'Interrupted'
            self.redis.close()

    def get_transcript(self):
        self.audio_stream = AudioStream(self.server)

        # Start reading audio stream from the server
        with self.audio_stream as stream:
            # Set-up the Google request with the audio data received from the server
            audio_generator = stream.generator()
            requests = (types.StreamingRecognizeRequest(audio_content=content) for content in audio_generator)
            responses = self.google_client.streaming_recognize(self.google_streaming_config, requests)

            # Use Google speech-to-text response to return only the transcript
            speech_text = self.__extract_audio_transcript(responses)
            print 'speech returned from server: {}'.format(speech_text)

        return speech_text

    def __extract_audio_transcript(self, responses):
        """Iterates through google server responses and return the final one.

        The responses passed is a generator that will block until a response
        is provided by the server.

        Each response may contain multiple results, and each result may contain
        multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here,
        only the transcription for the top alternative of the top result is returned.

        The iteration over responses is only useful if interim_result is set to True in
        Google config. If interim_result is set to False (default), then the response
        only contains the final result.
        """
        try:
            for response in responses:
                # The `results` list is consecutive. For streaming, we only care about
                # the first result being considered, since once it's `is_final`, it
                # moves on to considering the next utterance.
                result = response.results[0]
                if result.is_final:
                    transcript = result.alternatives[0].transcript
                    return transcript
        except:
            return ''

class AudioStream(object):
    def __init__(self, server):
        self.redis = redis.Redis(host=server) # new instance needed for blocking
        self.topic = 'audio_stream'
        self.buffer = queue.Queue()
        self.closed = True
        self.receive_audio_process = None

    def __enter__(self):
        self.receive_audio_process = self.start_receiving()
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self.closed = True
        self.buffer.put(None)
        self.redis.close()
        self.receive_audio_process.join()

    def start_receiving(self):
        receive_audio_process = threading.Thread(target=self.receive_audio)
        receive_audio_process.start()
        return receive_audio_process

    def receive_audio(self):
        print 'receiving robot audio from kafka'

        try:
            msg = self.redis.blpop(self.topic) # wait for the first fragment
            while msg is not None and not self.closed:
                self.buffer.put(msg)
                msg = self.redis.lpop(self.topic) # check for more fragments
        except KeyboardInterrupt:
            print 'Interrupted'

        print 'finished receiving robot audio'

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self.buffer.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self.buffer.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', type=str, default='localhost', help='Server IP address. Default is localhost.')
    args = parser.parse_args()

    t1 = time.time()
    env = GoogleAsrEnvironmentKafka(server=args.server, topics=['action_audio', 'audio_language'], languages=LANGUAGES)
    env.run_forever()
    t2 = time.time()
    print 'time consumer has been running:', t2 - t1