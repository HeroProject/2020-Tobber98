package org.bitbucket.socialrobotics.connector;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;

import org.bitbucket.socialrobotics.connector.actions.RobotAction;
import org.bitbucket.socialrobotics.connector.actions.SetLanguageAction;
import org.bitbucket.socialrobotics.connector.actions.StartListeningAction;
import org.bitbucket.socialrobotics.connector.actions.StopListeningAction;
import org.bitbucket.socialrobotics.connector.actions.StopWatchingAction;

import eis.EIDefaultImpl;
import eis.exceptions.ActException;
import eis.exceptions.EntityException;
import eis.exceptions.ManagementException;
import eis.exceptions.NoEnvironmentException;
import eis.iilang.Action;
import eis.iilang.EnvironmentState;
import eis.iilang.Identifier;
import eis.iilang.Numeral;
import eis.iilang.Parameter;
import eis.iilang.ParameterList;
import eis.iilang.Percept;
import eis.iilang.TruthValue;

public class CBSRenvironment extends EIDefaultImpl {
	private static final long serialVersionUID = 1L;
	protected Map<String, Parameter> parameters;
	protected BlockingQueue<Percept> perceptQueue;
	protected RedisRunner consumer;
	protected RedisRunner producer;
	protected volatile boolean tabletConnected = false;

	public CBSRenvironment() {
		try {
			final File jar = new File(getClass().getProtectionDomain().getCodeSource().getLocation().toURI());
			System.setProperty("javax.net.ssl.trustStore", jar.getParent() + "/truststore.jks");
			System.setProperty("javax.net.ssl.trustStorePassword", "changeit");
		} catch (final Exception e) {
			e.printStackTrace();
		}
	}

	@Override
	public void init(final Map<String, Parameter> parameters) throws ManagementException {
		super.init(parameters);
		this.parameters = parameters;
		this.perceptQueue = new LinkedBlockingQueue<>();
		setState(EnvironmentState.PAUSED);

		final String server = getParameter("server", "localhost");
		final boolean ssl = !getParameter("ssl", "").equals("false");
		this.consumer = new RedisConsumerRunner(this, server, ssl);
		this.consumer.start();
		this.producer = new RedisProducerRunner(this, server, ssl);
		this.producer.start();

		final String flowkey = getParameter("flowkey", "");
		final String flowagent = getParameter("flowagent", "");
		final String flowlang = getParameter("flowlang", "nl-NL");

		setState(EnvironmentState.RUNNING);
		try { // single entity
			addEntity("pepper", "robot");
		} catch (final EntityException e) {
			throw new ManagementException("Unable to initialise robot entity", e);
		}

		// start-up actions
		addAction(new StopListeningAction());
		addAction(new StopWatchingAction());
		if (!flowkey.isEmpty()) {
			addAction(new RobotAction(null) {
				@Override
				public boolean isValid() {
					return true;
				}

				@Override
				public String getTopic() {
					return "dialogflow_key";
				}

				@Override
				public String getData() {
					try {
						return new String(Files.readAllBytes(Paths.get(flowkey)), StandardCharsets.UTF_8);
					} catch (final IOException e) {
						e.printStackTrace(); // FIXME
						return "";
					}
				}
			});
		}
		if (!flowagent.isEmpty()) {
			addAction(new RobotAction(null) {
				@Override
				public boolean isValid() {
					return true;
				}

				@Override
				public String getTopic() {
					return "dialogflow_agent";
				}

				@Override
				public String getData() {
					return flowagent;
				}
			});
		}
		addAction(new SetLanguageAction(Arrays.asList(new Identifier[] { new Identifier(flowlang) })));
	}

	private String getParameter(final String name, final String def) {
		return (this.parameters.get(name) instanceof Identifier) ? ((Identifier) this.parameters.get(name)).getValue()
				: def;
	}

	@Override
	public void kill() throws ManagementException {
		this.consumer.shutdown();
		this.producer.shutdown();
		this.perceptQueue.clear();

		super.kill();
	}

	@Override
	protected List<Percept> getAllPerceptsFromEntity(final String entity) throws NoEnvironmentException {
		final List<Percept> percepts = new LinkedList<>();
		this.perceptQueue.drainTo(percepts);
		return percepts;
	}

	@Override
	protected boolean isSupportedByEnvironment(final Action action) {
		final RobotAction robotAction = RobotAction.getRobotAction(action);
		return (robotAction != null && robotAction.isValid());
	}

	@Override
	protected boolean isSupportedByType(final Action action, final String type) {
		return isSupportedByEnvironment(action);
	}

	@Override
	protected boolean isSupportedByEntity(final Action action, final String entity) {
		return isSupportedByEnvironment(action);
	}

	@Override
	protected Percept performEntityAction(final String entity, final Action action) throws ActException {
		final RobotAction robotAction = RobotAction.getRobotAction(action);
		if (robotAction != null && robotAction.isValid()) {
			if (robotAction instanceof StartListeningAction) {
				final StartListeningAction slAction = (StartListeningAction) robotAction;
				if (!slAction.getContext().isEmpty()) {
					addAction(new RobotAction(null) {
						@Override
						public boolean isValid() {
							return true;
						}

						@Override
						public String getTopic() {
							return "audio_context";
						}

						@Override
						public String getData() {
							return slAction.getContext();
						}
					});
				}
			}
			addAction(robotAction);
		} else {
			throw new ActException(ActException.FAILURE, "Not able to perform " + action.toProlog());
		}
		return null;
	}

	public boolean isTabletConnected() {
		return this.tabletConnected;
	}

	public void setTabletConnected() {
		this.tabletConnected = true;
	}

	public void setTabletDisconnected() {
		this.tabletConnected = false;
	}

	/**
	 * Queues the intent information as a percept to be received by the agent.
	 *
	 * @param intent The name of the intent
	 * @param params Optional parameters (following from the intent definition)
	 */
	public void addIntent(final String intent, final String... params) {
		System.out.println(intent + ": " + Arrays.asList(params));
		final Parameter[] parameters = new Parameter[params.length];
		for (int i = 0; i < params.length; ++i) {
			if (params[i].equals("true")) {
				parameters[i] = new TruthValue(true);
			} else if (params[i].equals("false")) {
				parameters[i] = new TruthValue(false);
			} else {
				try {
					parameters[i] = new Numeral(Integer.parseInt(params[i]));
				} catch (final NumberFormatException e) {
					parameters[i] = new Identifier(params[i]);
				}
			}
		}
		this.perceptQueue.add(new Percept("intent", new Identifier(intent), new ParameterList(parameters)));
	}

	/**
	 * Queues the robot event information as a percept to be received by the agent.
	 *
	 * @param event The event name
	 */
	public void addEvent(final String event) {
		this.perceptQueue.add(new Percept("event", new Identifier(event)));
	}

	/**
	 * Queues the answer (to a posed question) as a percept to be received by the
	 * agent.
	 *
	 * @param answer The answer
	 */
	public void addAnswer(final String answer) {
		try {
			this.perceptQueue.add(new Percept("answer", new Numeral(Integer.parseInt(answer))));
		} catch (final NumberFormatException e) {
			this.perceptQueue.add(new Percept("answer", new Identifier(answer)));
		}
	}

	/**
	 * Queues 'personDetected' as a percept to be received by the agent. This means
	 * one or more persons have been detected (with a certainty threshold).
	 */
	public void addDetectedPerson() {
		this.perceptQueue.add(new Percept("personDetected"));
	}

	/**
	 * Queues the detected emotion as a percept to be received by the agent.
	 */
	public void addDetectedEmotion(final String emotion) {
		this.perceptQueue.add(new Percept("emotionDetected", new Identifier(emotion)));
	}

	/**
	 * Queues the id of the face as a percept to be received by the agent.
	 *
	 * @param id The identifier for the face
	 */
	public void addRecognizedFace(final String id) {
		this.perceptQueue.add(new Percept("faceRecognized", new Identifier(id)));
	}

	/**
	 * Queues the url and text as a percept to be received by the agent.
	 *
	 * @param url  A link to the web page to show
	 * @param text The accompanying text the robot should say
	 */
	public void addWebResponse(final String url, final String text) {
		this.perceptQueue.add(new Percept("webResponse", new Identifier(url), new Identifier(text)));
	}

	/**
	 * Queues the language key as a percept to be received by the agent, and changes
	 * the language used in the intent recognition.
	 *
	 * @param lang The language key
	 */
	public void setAudioLanguage(final String lang) {
		this.perceptQueue.add(new Percept("audioLanguage", new Identifier(lang)));
	}

	/**
	 * Queues the file name of an audio recording as a percept to be received by the
	 * agent.
	 *
	 * @param filename The filename (including extension) of the recording.
	 */
	public void addAudioRecording(final String filename) {
		this.perceptQueue.add(new Percept("audioRecording", new Identifier(filename)));
	}

	/**
	 * Queues the file name of a picture as a percept to be received by the agent.
	 *
	 * @param filename The filename (including extension) of the pictre.
	 */
	public void addPicture(final String filename) {
		this.perceptQueue.add(new Percept("picture", new Identifier(filename)));
	}

	/**
	 * Queues the text as recognised from the audiostream by dialogflow as a percept
	 * to be received by the agent.
	 *
	 * @param text The recognised text.
	 */
	public void addSpeechText(final String text) {
		this.perceptQueue.add(new Percept("speechText", new Identifier(text)));
	}

	/**
	 * Queues the given Kafka action for transmission by the producer.
	 *
	 * @param action
	 */
	public void addAction(final RobotAction action) {
		((RedisProducerRunner) this.producer).queueAction(action);
	}
}
