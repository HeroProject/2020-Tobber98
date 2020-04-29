
package org.bitbucket.socialrobotics;

import java.awt.BorderLayout;
import java.awt.Color;
import java.io.File;
import java.util.prefs.Preferences;

import javax.sound.sampled.AudioSystem;
import javax.sound.sampled.Clip;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;

import com.harium.hci.espeak.Voice;

import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPubSub;
import redis.clients.jedis.Protocol;

public class DebugSpeaker extends JFrame {
	private static final long serialVersionUID = 1L;
	private static final String[] topics = new String[] { "audio_language", "action_say", "action_say_animated",
			"action_play_audio", "action_gesture", "action_eyecolour", "action_idle", "action_turn",
			"action_turn_small" };
	private final String server;
	private final boolean ssl;
	private final String espeak;
	private final String webserver;
	private final Voice voice;
	private final Jedis publisher;
	private final JLabel status;
	private final JLabel language;

	public static void main(final String... args) {
		final Preferences prefs = Preferences.userRoot().node("cbsr");
		final String server = (args.length > 0) ? args[0]
				: JOptionPane.showInputDialog("Server IP", prefs.get("server", ""));
		prefs.put("server", server);
		final String os = System.getProperty("os.name").toLowerCase();
		final String espeak = os.startsWith("win") ? "C:\\Program Files (x86)\\eSpeak\\command_line" : "/usr/local/bin";
		final String espeakpath = (args.length > 1) ? args[1] : espeak;
		final String webserver = (args.length > 2) ? args[2] : "../../processing/webserver";

		System.setProperty("javax.net.ssl.trustStore", "../truststore.jks");
		System.setProperty("javax.net.ssl.trustStorePassword", "changeit");

		try {
			final DebugSpeaker speaker = new DebugSpeaker(server, espeakpath, webserver);
			speaker.run();
		} catch (final Exception e) {
			e.printStackTrace();
			System.exit(-1);
		}
	}

	public DebugSpeaker(final String server, final String espeak, final String webserver) {
		super("CBSR Speaker");
		this.server = server;
		this.ssl = !this.server.equals("192.168.99.100");
		this.espeak = espeak;
		this.webserver = webserver;
		this.voice = new Voice();
		this.publisher = new Jedis(server, Protocol.DEFAULT_PORT, this.ssl);

		setLayout(new BorderLayout(10, 5));
		this.status = new JLabel();
		toggleStatus(false);
		add(this.status, BorderLayout.WEST);
		this.language = new JLabel("unknown");
		add(this.language, BorderLayout.EAST);

		pack();
		setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		setVisible(true);
	}

	private void toggleStatus(final boolean playing) {
		if (playing) {
			this.status.setText("Playing audio!");
			this.status.setForeground(Color.GREEN);
		} else {
			this.status.setText("Not playing audio...");
			this.status.setForeground(Color.RED);
		}
	}

	public void run() {
		try (final Jedis redis = new Jedis(this.server, Protocol.DEFAULT_PORT, this.ssl)) {
			redis.ping();
			System.out.println("Subscribing to " + this.server);
			redis.subscribe(new JedisPubSub() {
				@Override
				public void onMessage(final String channel, final String message) {
					new Thread() {
						@Override
						public void run() {
							switch (channel) {
							case "audio_language":
								System.out.println("Switching language to " + message);
								setLanguage(message);
								break;
							case "action_say":
							case "action_say_animated":
								System.out.println("Saying: " + message);
								say(message);
								break;
							case "action_play_audio":
								System.out.println("Playing: " + message);
								final String dir = DebugSpeaker.this.webserver + "/html/audio";
								final File audiofile = new File(dir + "/" + message);
								playAudio(audiofile);
								break;
							// all below actions are stub that will produce the correct events,
							// so any script waiting on them can continue:
							case "action_gesture":
								publishEvent("GestureStarted");
								System.out.println("Gesture: " + message);
								publishEvent("GestureDone");
								break;
							case "action_eyecolour":
								publishEvent("EyeColourStarted");
								System.out.println("Eyecolour: " + message);
								publishEvent("EyeColourDone");
								break;
							case "action_idle":
								System.out.println("Idle: " + message);
								if (message.equals("true") || message.equals("straight")) {
									publishEvent("SetIdle");
								} else {
									publishEvent("SetNonIdle");
								}
								break;
							case "action_turn":
								publishEvent("TurnStarted");
								System.out.println("Turn: " + message);
								publishEvent("TurnDone");
								break;
							case "action_turn_small":
								publishEvent("SmallTurnStarted");
								System.out.println("SmallTurn: " + message);
								publishEvent("SmallTurnDone");
								break;
							}
						}
					}.start();
				}
			}, topics);
		}
	}

	private synchronized void publishEvent(final String name) {
		this.publisher.publish("events_robot", name);
	}

	private void setLanguage(final String lang) {
		this.voice.setName(lang.toLowerCase());
		this.language.setText(lang);
		publishEvent("LanguageChanged");
	}

	private void say(final String rawtext) {
		final String text = rawtext.replaceAll("\\\\.+\\\\", ""); // remove any special naoqi commands from the text
		if (text.isEmpty()) { // espeak hangs otherwise
			publishEvent("TextStarted");
			publishEvent("TextDone");
			return;
		}
		final String[] command = new String[] { this.espeak + File.separator + "espeak", "-v",
				this.voice.getName() + this.voice.getVariant(), text };
		final ProcessBuilder b = new ProcessBuilder(command);
		try {
			toggleStatus(true);
			publishEvent("TextStarted");
			final Process process = b.start();
			process.waitFor();
			publishEvent("TextDone");
			toggleStatus(false);
			process.destroy();
		} catch (final Exception e) {
			e.printStackTrace(); // FIXME
		}
	}

	private void playAudio(final File audio) {
		try {
			final Clip sound = AudioSystem.getClip();
			sound.open(AudioSystem.getAudioInputStream(audio));
			toggleStatus(true);
			publishEvent("PlayAudioStarted");
			sound.start();
			while (sound.getMicrosecondPosition() < sound.getMicrosecondLength()) {
				Thread.sleep(1);
			}
			publishEvent("PlayAudioDone");
			toggleStatus(false);
			sound.close();
		} catch (final Exception e) {
			e.printStackTrace(); // FIXME
		}
	}
}
