package org.bitbucket.socialrobotics;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Point;
import java.awt.Transparency;
import java.awt.color.ColorSpace;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.image.BufferedImage;
import java.awt.image.ComponentColorModel;
import java.awt.image.DataBuffer;
import java.awt.image.DataBufferByte;
import java.awt.image.Raster;
import java.awt.image.SampleModel;
import java.awt.image.WritableRaster;
import java.nio.ByteBuffer;
import java.util.prefs.Preferences;

import javax.swing.JCheckBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;

import com.github.sarxos.webcam.Webcam;
import com.github.sarxos.webcam.WebcamPanel;
import com.github.sarxos.webcam.WebcamPanel.ImageSupplier;

import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPubSub;
import redis.clients.jedis.Pipeline;
import redis.clients.jedis.Protocol;

public class DebugVideo extends JFrame implements ImageSupplier {
	private static final long serialVersionUID = 1L;
	private static final int width = 640, height = 480;
	private static final byte[] videotopic = "image_stream".getBytes();
	private static final String frametopic = "image_frame";
	private final String server;
	private final boolean ssl;
	private final Webcam webcam;
	private final WebcamPanel display;
	private final JFrame popup;
	private final JLabel status;
	private boolean openWindow;
	private byte[] current = new byte[0];
	private long frame = 0;

	public static void main(final String... args) {
		final Preferences prefs = Preferences.userRoot().node("cbsr");
		final String server = (args.length > 0) ? args[0]
				: JOptionPane.showInputDialog("Server IP", prefs.get("server", ""));
		prefs.put("server", server);

		System.setProperty("javax.net.ssl.trustStore", "../truststore.jks");
		System.setProperty("javax.net.ssl.trustStorePassword", "changeit");

		try {
			final DebugVideo video = new DebugVideo(server);
			video.run();
		} catch (final Exception e) {
			e.printStackTrace();
			System.exit(-1);
		}
	}

	public DebugVideo(final String server) {
		super("CBSR Video");
		this.server = server;
		this.ssl = !this.server.equals("192.168.99.100");

		this.webcam = Webcam.getDefault();
		this.webcam.setViewSize(new Dimension(width, height));

		this.display = new WebcamPanel(this.webcam, null, false, this);
		this.display.setFPSDisplayed(true);
		this.display.setImageSizeDisplayed(true);
		this.popup = new JFrame();
		this.popup.add(this.display);
		this.popup.pack();

		setLayout(new BorderLayout(10, 5));
		this.status = new JLabel();
		toggleStatus(false);
		add(this.status, BorderLayout.WEST);
		final JCheckBox toggleOpenWindow = new JCheckBox("Show feed", this.openWindow);
		toggleOpenWindow.addActionListener(new ActionListener() {
			@Override
			public void actionPerformed(final ActionEvent e) {
				DebugVideo.this.openWindow = toggleOpenWindow.isSelected();
			}
		});
		add(toggleOpenWindow, BorderLayout.EAST);

		pack();
		setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		setVisible(true);
	}

	private void toggleStatus(final boolean watching) {
		if (watching) {
			this.status.setText("Watching!");
			this.status.setForeground(Color.GREEN);
		} else {
			this.status.setText("Not watching...");
			this.status.setForeground(Color.RED);
		}
	}

	public void run() {
		try (final Jedis redis = new Jedis(this.server, Protocol.DEFAULT_PORT, this.ssl)) {
			redis.set("image_size", width + " " + height);
			System.out.println("Subscribing to " + this.server);
			redis.subscribe(new JedisPubSub() {
				@Override
				public void onMessage(final String channel, final String message) {
					switch (message) {
					case "start watching":
						DebugVideo.this.webcam.open();
						new RedisWebcamSync().start();
						toggleStatus(true);
						if (DebugVideo.this.openWindow) {
							DebugVideo.this.display.start();
							DebugVideo.this.popup.setVisible(true);
						}
						break;
					case "stop watching":
						DebugVideo.this.webcam.close();
						toggleStatus(false);
						if (DebugVideo.this.openWindow) {
							DebugVideo.this.display.stop();
							DebugVideo.this.popup.setVisible(false);
						}
						break;
					}
				}
			}, "action_video");
		}
	}

	@Override
	public BufferedImage get() {
		final ComponentColorModel cm = new ComponentColorModel(ColorSpace.getInstance(ColorSpace.CS_sRGB), false, false,
				Transparency.OPAQUE, DataBuffer.TYPE_BYTE);
		final SampleModel sm = cm.createCompatibleSampleModel(width, height);
		final DataBufferByte db = new DataBufferByte(width * height * 3);
		final WritableRaster r = Raster.createWritableRaster(sm, db, new Point(0, 0));
		final BufferedImage bm = new BufferedImage(cm, r, false, null);
		r.setDataElements(0, 0, width, height, this.current);
		return bm;
	}

	private final class RedisWebcamSync extends Thread {
		private final Jedis redis;

		RedisWebcamSync() {
			this.redis = new Jedis(DebugVideo.this.server, Protocol.DEFAULT_PORT, DebugVideo.this.ssl);
			this.redis.connect();
		}

		@Override
		public void run() {
			while (DebugVideo.this.webcam.isOpen()) {
				final ByteBuffer buffer = DebugVideo.this.webcam.getImageBytes();
				final byte[] img = new byte[buffer.remaining()];
				buffer.get(img);
				final Pipeline pipe = this.redis.pipelined();
				pipe.set(videotopic, img);
				pipe.set(frametopic, Long.toString(DebugVideo.this.frame++));
				pipe.sync();
				DebugVideo.this.current = img;
			}
			this.redis.close();
		}
	}
}
