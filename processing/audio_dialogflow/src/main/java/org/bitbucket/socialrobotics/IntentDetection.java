package org.bitbucket.socialrobotics;

import java.io.ByteArrayInputStream;
import java.io.Closeable;
import java.io.DataOutputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Arrays;
import java.util.Date;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import javax.swing.JOptionPane;

import org.apache.commons.lang3.ArrayUtils;

import com.google.api.gax.core.FixedCredentialsProvider;
import com.google.api.gax.rpc.ClientStream;
import com.google.api.gax.rpc.ResponseObserver;
import com.google.api.gax.rpc.StreamController;
import com.google.auth.oauth2.ServiceAccountJwtAccessCredentials;
import com.google.cloud.dialogflow.v2.AudioEncoding;
import com.google.cloud.dialogflow.v2.Context;
import com.google.cloud.dialogflow.v2.InputAudioConfig;
import com.google.cloud.dialogflow.v2.QueryInput;
import com.google.cloud.dialogflow.v2.QueryParameters;
import com.google.cloud.dialogflow.v2.QueryResult;
import com.google.cloud.dialogflow.v2.SessionName;
import com.google.cloud.dialogflow.v2.SessionsClient;
import com.google.cloud.dialogflow.v2.SessionsSettings;
import com.google.cloud.dialogflow.v2.StreamingDetectIntentRequest;
import com.google.cloud.dialogflow.v2.StreamingDetectIntentResponse;
import com.google.protobuf.ByteString;
import com.google.protobuf.Value;

import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPubSub;

public class IntentDetection {
	private static final String[] topics = new String[] { "audio_language", "audio_context", "dialogflow_key",
			"dialogflow_agent", "dialogflow_record", "action_audio" };
	private static final SimpleDateFormat dateFormat = new SimpleDateFormat("HH-mm-ss");
	private static final byte[] audiotopic = "audio_stream".getBytes();
	private static final AudioEncoding audioEncoding = AudioEncoding.AUDIO_ENCODING_LINEAR_16;
	private static final int sampleRateHertz = 16000;
	private final String server;
	private final Jedis publisher;
	private SessionsClient client;
	private SessionName session;
	private String language;
	private String context;
	private volatile boolean shouldRecord;

	public static void main(final String... args) {
		final String server = (args.length > 0) ? args[0] : JOptionPane.showInputDialog("Server IP");
		final IntentDetection dialogflow = new IntentDetection(server);
		dialogflow.run();
	}

	public IntentDetection(final String server) {
		this.server = server;
		this.publisher = new Jedis(server);
	}

	public void setKey(final String key) throws IOException {
		final InputStream stream = new ByteArrayInputStream(key.getBytes(StandardCharsets.UTF_8));
		final ServiceAccountJwtAccessCredentials credentials = ServiceAccountJwtAccessCredentials.fromStream(stream);
		final SessionsSettings settings = SessionsSettings.newBuilder()
				.setCredentialsProvider(FixedCredentialsProvider.create(credentials)).build();
		this.client = SessionsClient.create(settings);
	}

	public void setAgent(final String agent) {
		this.session = SessionName.of(agent, UUID.randomUUID().toString());
	}

	public void setLanguage(final String language) {
		this.language = language;
	}

	public void setContext(final String context) {
		this.context = context;
	}

	public void run() {
		try (final Jedis redis = new Jedis(this.server)) {
			System.out.println("Subscribing to " + this.server);
			redis.subscribe(new JedisPubSub() {
				private RedisAudioIterator audio;

				@Override
				public void onMessage(final String channel, final String message) {
					switch (channel) {
					case "audio_language":
						setLanguage(message);
						break;
					case "audio_context":
						setContext(message);
						break;
					case "dialogflow_key":
						try {
							setKey(message);
						} catch (final IOException e) {
							e.printStackTrace(); // FIXME
						}
						break;
					case "dialogflow_agent":
						setAgent(message);
						break;
					case "dialogflow_record":
						IntentDetection.this.shouldRecord = message.equals("1");
						break;
					case "action_audio":
						switch (message) {
						case "start listening":
							if (this.audio == null) {
								this.audio = new RedisAudioIterator();
								new Thread() {
									@Override
									public void run() {
										detectIntents(audio);
									}
								}.start();
							} else {
								System.err.println("already listening...");
							}
							break;
						case "stop listening":
							if (this.audio != null) {
								this.audio.close();
								this.audio = null;
							} else {
								System.err.println("already not listening...");
							}
							break;
						}
						break;
					}
				}
			}, topics);
		}
	}

	/**
	 * @param string      context The context to use (if any)
	 * @param audioStream The audio input stream
	 *
	 * @return Using the set agent and language, keep trying to match intents
	 *         whenever something is available from the audioStream and passes any
	 *         matched intent directly to the parent.
	 */
	public void detectIntents(final Iterator<byte[]> audio) {
		System.out.println("START INTENT DETECTION");
		// Instructs the speech recognizer how to process the audio content
		final InputAudioConfig.Builder inputAudioConfig = InputAudioConfig.newBuilder().setAudioEncoding(audioEncoding)
				.setLanguageCode(IntentDetection.this.language).setSampleRateHertz(sampleRateHertz)
				.setSingleUtterance(true);
		final ResponseObserver<StreamingDetectIntentResponse> responseObserver = new ResponseObserver<StreamingDetectIntentResponse>() {
			@Override
			public void onStart(final StreamController controller) {
			}

			@Override
			public void onResponse(final StreamingDetectIntentResponse response) {
				final QueryResult intent = response.getQueryResult();
				System.out.println("====================");
				if (intent.getIntentDetectionConfidence() > 0) { // if any intent was detected, tell the agent so
					System.out.format("Detected Intent: %s (confidence %f)\n", intent.getIntent().getDisplayName(),
							intent.getIntentDetectionConfidence());
					final Map<String, Value> parameters = intent.getParameters().getFieldsMap();
					if (!parameters.isEmpty()) {
						System.out.println(parameters);
					}
					final List<Object> params = new LinkedList<>();
					for (final Value value : parameters.values()) {
						processValue(value, params);
					}
					final StringBuilder message = new StringBuilder(intent.getAction());
					for (final Object param : params) {
						message.append("|").append(param);
					}
					IntentDetection.this.publisher.publish("audio_intent", message.toString());
				}
				final String queryText = intent.getQueryText();
				if (!queryText.isEmpty()) { // publish the final recognised text (if any)
					System.out.format("Recognised Text: '%s'\n", queryText);
					IntentDetection.this.publisher.publish("text_speech", queryText);
				} else {
					final String transcript = response.getRecognitionResult().getTranscript();
					if (!transcript.isEmpty()) { // publish what we heard so far (if anything)
						System.out.format("Transcript: '%s'\n", transcript);
						IntentDetection.this.publisher.publish("text_transcript", transcript);
					}
				}
				System.out.println("====================");
			}

			private void processValue(final Value value, final List<Object> params) {
				switch (value.getKindCase()) {
				case STRING_VALUE:
					if (value.getStringValue().length() > 1) {
						params.add(value.getStringValue());
					}
					break;
				case NUMBER_VALUE:
					params.add((int) value.getNumberValue());
					break;
				case BOOL_VALUE:
					params.add(value.getBoolValue());
					break;
				case STRUCT_VALUE:
					final Map<String, Value> struct = value.getStructValue().getFieldsMap();
					for (final Value subvalue : struct.values()) {
						processValue(subvalue, params);
					}
					break;
				default:
					throw new IllegalArgumentException("Unsupported value: " + value);
				}
			}

			@Override
			public void onError(final Throwable t) {
				t.printStackTrace(); // FIXME
			}

			@Override
			public void onComplete() {
				try {
					((Closeable) audio).close();
				} catch (final Exception e) {
					onError(e);
				} finally {
					setContext(null);
				}
			}
		};

		// Performs the streaming detect intent callable request
		final ClientStream<StreamingDetectIntentRequest> requestObserver = IntentDetection.this.client
				.streamingDetectIntentCallable().splitCall(responseObserver);
		// Set the context (if any)
		final QueryParameters.Builder queryParams = QueryParameters.newBuilder();
		if (IntentDetection.this.context != null && !IntentDetection.this.context.isEmpty()) {
			System.out.println("CONTEXT: " + this.context);
			queryParams.addContexts(Context.newBuilder()
					.setName(IntentDetection.this.session.toString() + "/contexts/" + IntentDetection.this.context)
					.setLifespanCount(1));
		}
		// Build the query with the InputAudioConfig
		final QueryInput.Builder queryInput = QueryInput.newBuilder().setAudioConfig(inputAudioConfig);

		try {
			// The first request contains the configuration
			final StreamingDetectIntentRequest request = StreamingDetectIntentRequest.newBuilder()
					.setSession(IntentDetection.this.session.toString()).setQueryInput(queryInput)
					.setQueryParams(queryParams).build();
			requestObserver.send(request);
			while (audio.hasNext()) {
				final byte[] next = audio.next(); // this is a blocking call
				if (next != null) {
					final ByteString chunk = ByteString.copyFrom(next);
					requestObserver.send(StreamingDetectIntentRequest.newBuilder().setInputAudio(chunk).build());
				}
			}
			// Half-close the stream
			requestObserver.closeSend();
		} catch (final Throwable e) {
			// Cancel stream
			requestObserver.closeSendWithError(e);
		}
		System.out.println("STOPPED INTENT DETECTION");
	}

	private final class RedisAudioIterator implements Iterator<byte[]>, Closeable {
		private final Jedis redis;
		private final List<Byte> allbytes;
		private volatile boolean closed = false;

		RedisAudioIterator() {
			this.redis = new Jedis(IntentDetection.this.server);
			this.redis.connect();
			if (IntentDetection.this.shouldRecord) {
				this.allbytes = new LinkedList<>();
			} else {
				this.allbytes = null;
			}
		}

		@Override
		public boolean hasNext() {
			if (this.closed) {
				this.redis.close();
				return false;
			} else {
				return true;
			}
		}

		@Override
		public byte[] next() {
			byte[] next;
			do {
				next = this.redis.lpop(audiotopic);
				if (next == null) { // nothing yet; wait
					try {
						Thread.sleep(0);
					} catch (final InterruptedException ignore) {
					}
				}
			} while (next == null && !this.closed);
			if (next != null && this.allbytes != null) {
				this.allbytes.addAll(Arrays.asList(ArrayUtils.toObject(next)));
			}
			return next;
		}

		@Override
		public void close() {
			if (!this.closed) {
				this.closed = true;
				if (this.allbytes != null) {
					try {
						final byte[] data = ArrayUtils
								.toPrimitive(this.allbytes.toArray(new Byte[this.allbytes.size()]));
						final String file = writeAudioToFile(data);
						IntentDetection.this.publisher.publish("audio_newfile", file);
					} catch (final Exception e) {
						e.printStackTrace(); // FIXME
					}
				}
			}
		}
	}

	private static String writeAudioToFile(final byte[] data) throws IOException {
		final String dir = "../../processing/webserver/html/audio";
		final String filename = dateFormat.format(new Date()) + ".wav";
		final FileOutputStream fileStream = new FileOutputStream(dir + "/" + filename);
		PCMtoWav(new DataOutputStream(fileStream), data);
		return filename;
	}

	private static void PCMtoWav(final DataOutputStream output, final byte[] data) throws IOException {
		normalizeVolume(data);
		writeString(output, "RIFF"); // chunk id
		writeInt(output, 36 + data.length); // chunk size
		writeString(output, "WAVE"); // format
		writeString(output, "fmt "); // subchunk 1 id
		writeInt(output, 16); // subchunk 1 size
		writeShort(output, (short) 1); // audio format (1 = PCM)
		writeShort(output, (short) 1); // number of channels
		writeInt(output, 16000); // sample rate
		writeInt(output, 16000 * 2); // byte rate (samplerate*channels*bits/8)
		writeShort(output, (short) 2); // block align (channels*bits/8)
		writeShort(output, (short) 16); // bits per sample
		writeString(output, "data"); // subchunk 2 id
		writeInt(output, data.length); // subchunk 2 size
		final short[] shorts = new short[data.length / 2];
		ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN).asShortBuffer().get(shorts);
		for (final short s : shorts) {
			writeShort(output, s);
		}
	}

	private static void writeInt(final DataOutputStream output, final int value) throws IOException {
		output.write(value >> 0);
		output.write(value >> 8);
		output.write(value >> 16);
		output.write(value >> 24);
	}

	private static void writeShort(final DataOutputStream output, final short value) throws IOException {
		output.write(value >> 0);
		output.write(value >> 8);
	}

	private static void writeString(final DataOutputStream output, final String value) throws IOException {
		for (int i = 0; i < value.length(); i++) {
			output.write(value.charAt(i));
		}
	}

	private static int N_SHORTS = 0xffff;
	private static final short[] VOLUME_NORM_LUT = new short[N_SHORTS];
	private static int MAX_NEGATIVE_AMPLITUDE = 0x8000;
	static {
		for (int s = 0; s < N_SHORTS; s++) {
			final double v = s - MAX_NEGATIVE_AMPLITUDE;
			final double sign = Math.signum(v);
			VOLUME_NORM_LUT[s] = (short) (sign
					* (1.240769e-22 - (-4.66022 / 0.0001408133) * (1 - Math.exp(-0.0001408133 * v * sign))));
		}
	}

	private static void normalizeVolume(final byte[] audioSamples) {
		for (int i = 0; i < audioSamples.length; i += 2) {
			short s1 = audioSamples[i + 1];
			short s2 = audioSamples[i];
			s1 = (short) ((s1 & 0xff) << 8);
			s2 = (short) (s2 & 0xff);
			short res = (short) (s1 | s2);
			res = VOLUME_NORM_LUT[res + MAX_NEGATIVE_AMPLITUDE];
			audioSamples[i] = (byte) res;
			audioSamples[i + 1] = (byte) (res >> 8);
		}
	}
}
