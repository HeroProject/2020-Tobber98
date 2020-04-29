package org.bitbucket.socialrobotics;

import java.awt.BorderLayout;
import java.awt.Color;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.prefs.Preferences;

import javax.sound.sampled.AudioFormat;
import javax.sound.sampled.AudioSystem;
import javax.sound.sampled.DataLine;
import javax.sound.sampled.LineEvent;
import javax.sound.sampled.LineListener;
import javax.sound.sampled.Mixer;
import javax.sound.sampled.TargetDataLine;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;

import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPubSub;
import redis.clients.jedis.Protocol;

public class DebugMicrophone extends JFrame implements LineListener {
	private static final long serialVersionUID = 1L;
	private static final byte[] audiotopic = "audio_stream".getBytes();
	private final String server;
	private final boolean ssl;
	private final AudioFormat format;
	private final TargetDataLine dataline;
	private final JLabel status;

	public static void main(final String... args) {
		final Preferences prefs = Preferences.userRoot().node("cbsr");
		final String server = (args.length > 0) ? args[0]
				: JOptionPane.showInputDialog("Server IP", prefs.get("server", ""));
		prefs.put("server", server);

		System.setProperty("javax.net.ssl.trustStore", "../truststore.jks");
		System.setProperty("javax.net.ssl.trustStorePassword", "changeit");

		try {
			final DebugMicrophone mic = new DebugMicrophone(server);
			mic.run();
		} catch (final Exception e) {
			e.printStackTrace();
			System.exit(-1);
		}
	}

	public DebugMicrophone(final String server) throws Exception {
		super("CBSR Audio");
		this.server = server;
		this.ssl = !this.server.equals("192.168.99.100");

		this.format = new AudioFormat(16000, 16, 1, true, false);
		final DataLine.Info info = new DataLine.Info(TargetDataLine.class, this.format);
		final Map<String, Mixer> mixers = new LinkedHashMap<>();
		for (final Mixer.Info mixerinfo : AudioSystem.getMixerInfo()) {
			final Mixer mixer = AudioSystem.getMixer(mixerinfo);
			if (mixer.isLineSupported(info)) {
				mixers.put(mixerinfo.getName(), mixer);
			}
		}
		final int found = mixers.size();
		Mixer mixer = null;
		switch (found) {
		case 0:
			throw new Exception("No suitable input device found!");
		case 1:
			mixer = mixers.values().iterator().next();
			break;
		default:
			final Object pick = JOptionPane.showInputDialog(null, "", "Input Device", JOptionPane.QUESTION_MESSAGE,
					null, mixers.keySet().toArray(new Object[found]), null);
			mixer = mixers.get(pick);
			break;
		}
		this.dataline = (TargetDataLine) mixer.getLine(info);
		this.dataline.addLineListener(this);

		setLayout(new BorderLayout(10, 5));
		this.status = new JLabel();
		toggleStatus(false);
		add(this.status, BorderLayout.WEST);

		pack();
		setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		setVisible(true);
	}

	private void toggleStatus(final boolean listening) {
		if (listening) {
			this.status.setText("Listening!");
			this.status.setForeground(Color.GREEN);
		} else {
			this.status.setText("Not listening...");
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
					switch (message) {
					case "start listening":
						try {
							DebugMicrophone.this.dataline.open(DebugMicrophone.this.format);
							DebugMicrophone.this.dataline.start();
							toggleStatus(true);
						} catch (final Exception e) {
							e.printStackTrace(); // FIXME
						}
						break;
					case "stop listening":
						try {
							DebugMicrophone.this.dataline.stop();
							DebugMicrophone.this.dataline.flush();
							DebugMicrophone.this.dataline.close();
							toggleStatus(false);
						} catch (final Exception e) {
							e.printStackTrace(); // FIXME
						}
						break;
					}
				}
			}, "action_audio");
		}
	}

	@Override
	public void update(final LineEvent event) {
		System.out.println(event);
		if (event.getType() == LineEvent.Type.OPEN) {
			new RedisMicrophoneSync().start();
		}
	}

	private final class RedisMicrophoneSync extends Thread {
		private final Jedis redis;

		RedisMicrophoneSync() {
			this.redis = new Jedis(DebugMicrophone.this.server, Protocol.DEFAULT_PORT, DebugMicrophone.this.ssl);
			this.redis.connect();
		}

		@Override
		public void run() {
			final byte[] next = new byte[DebugMicrophone.this.dataline.getBufferSize()];
			while (DebugMicrophone.this.dataline.isOpen()) {
				final int read = DebugMicrophone.this.dataline.read(next, 0, next.length);
				if (read > 0) {
					this.redis.rpush(audiotopic, next);
				}
			}
			this.redis.close();
		}
	}
}
