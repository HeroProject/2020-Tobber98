package org.bitbucket.socialrobotics.connector;

import java.util.Arrays;

import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPubSub;

class RedisConsumerRunner extends RedisRunner {
	private static final String[] topics = new String[] { "events_robot", "tablet_connection", "tablet_answer",
			"detected_person", "recognised_face", "webrequest_response", "audio_language", "text_speech",
			"audio_intent", "audio_newfile", "picture_newfile", "detected_emotion" };

	public RedisConsumerRunner(final CBSRenvironment parent, final String server) {
		super(parent, server);
	}

	@Override
	public void run() {
		final Jedis redis = getRedis();
		while (isRunning()) {
			try {
				redis.subscribe(new JedisPubSub() { // process incoming messages (into percepts)
					@Override
					public void onMessage(final String channel, final String message) {
						switch (channel) {
						case "events_robot":
							RedisConsumerRunner.this.parent.addEvent(message);
							break;
						case "tablet_connection":
							RedisConsumerRunner.this.parent.setTabletConnected();
							break;
						case "tablet_answer":
							RedisConsumerRunner.this.parent.addAnswer(message);
							break;
						case "detected_person":
							RedisConsumerRunner.this.parent.addDetectedPerson();
							break;
						case "recognised_face":
							RedisConsumerRunner.this.parent.addRecognizedFace(message);
							break;
						case "webrequest_response":
							final String[] response = message.split("\\|");
							RedisConsumerRunner.this.parent.addWebResponse(response[0], response[1]);
							break;
						case "audio_language":
							RedisConsumerRunner.this.parent.setAudioLanguage(message);
							break;
						case "text_speech":
							RedisConsumerRunner.this.parent.addSpeechText(message);
							break;
						case "audio_intent":
							final String[] intent = message.split("\\|");
							RedisConsumerRunner.this.parent.addIntent(intent[0],
									(intent.length > 1) ? Arrays.copyOfRange(intent, 1, intent.length) : new String[0]);
							break;
						case "audio_newfile":
							RedisConsumerRunner.this.parent.addAudioRecording(message);
							break;
						case "picture_newfile":
							RedisConsumerRunner.this.parent.addPicture(message);
							break;
						case "detected_emotion":
							RedisConsumerRunner.this.parent.addDetectedEmotion(message);
							break;
						}
					}
				}, topics);
			} catch (final Exception e) {
				if (isRunning()) {
					e.printStackTrace(); // FIXME
				}
			}
		}
	}
}