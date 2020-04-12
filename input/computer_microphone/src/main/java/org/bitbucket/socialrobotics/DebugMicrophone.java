package org.bitbucket.socialrobotics;

import java.awt.BorderLayout;
import java.awt.Color;

import javax.sound.sampled.AudioFormat;
import javax.sound.sampled.AudioSystem;
import javax.sound.sampled.DataLine;
import javax.sound.sampled.LineEvent;
import javax.sound.sampled.LineListener;
import javax.sound.sampled.LineUnavailableException;
import javax.sound.sampled.TargetDataLine;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;

import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPubSub;

public class DebugMicrophone extends JFrame implements LineListener {
	private static final long serialVersionUID = 1L;
	private static final byte[] audiotopic = "audio_stream".getBytes();
	private final String server;
	private final AudioFormat format;
	private final TargetDataLine dataline;
	private final JLabel status;

	public static void main(final String... args) {
		final String server = (args.length > 0) ? args[0] : JOptionPane.showInputDialog("Server IP");
		try {
			final DebugMicrophone mic = new DebugMicrophone(server);
			mic.run();
		} catch (final Exception e) {
			e.printStackTrace(); // FIXME
		}
	}

	public DebugMicrophone(final String server) throws LineUnavailableException {
		super("CBSR Audio");
		this.server = server;

		this.format = new AudioFormat(16000, 16, 1, true, false);
		final DataLine.Info info = new DataLine.Info(TargetDataLine.class, this.format);
		this.dataline = (TargetDataLine) AudioSystem.getLine(info);
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
		try (final Jedis redis = new Jedis(this.server)) {
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
			this.redis = new Jedis(DebugMicrophone.this.server);
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
