package org.bitbucket.socialrobotics;

import java.awt.Point;
import java.awt.Transparency;
import java.awt.color.ColorSpace;
import java.awt.image.BufferedImage;
import java.awt.image.ComponentColorModel;
import java.awt.image.DataBuffer;
import java.awt.image.DataBufferByte;
import java.awt.image.Raster;
import java.awt.image.SampleModel;
import java.awt.image.WritableRaster;
import java.util.prefs.Preferences;

import javax.swing.JOptionPane;

import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPubSub;
import redis.clients.jedis.Protocol;

public class StreamVideo {
	private static final byte[] videotopic = "image_stream".getBytes();
	private final String server;
	private final boolean ssl;
	private final VideoServer stream;

	public static void main(final String... args) {
		final Preferences prefs = Preferences.userRoot().node("cbsr");
		final String server = (args.length > 0) ? args[0]
				: JOptionPane.showInputDialog("Server IP", prefs.get("server", ""));
		prefs.put("server", server);
		final boolean ssl = (args.length <= 1); // any text as second arg disables ssl

		System.setProperty("javax.net.ssl.trustStore", "../truststore.jks");
		System.setProperty("javax.net.ssl.trustStorePassword", "changeit");

		try {
			final StreamVideo stream = new StreamVideo(server, ssl);
			stream.listen();
			stream.run();
		} catch (final Exception e) {
			e.printStackTrace();
			System.exit(-1);
		}
	}

	public StreamVideo(final String server, final boolean ssl) throws Exception {
		this.server = server;
		this.ssl = ssl;
		this.stream = new VideoServer();
	}

	public void listen() {
		new Thread() {
			@Override
			public void run() {
				try (final Jedis redis = new Jedis(StreamVideo.this.server, Protocol.DEFAULT_PORT,
						StreamVideo.this.ssl)) {
					redis.ping();
					System.out.println("Subscribing to " + StreamVideo.this.server);
					redis.subscribe(new JedisPubSub() {
						@Override
						public void onMessage(final String channel, final String message) {
							synchronized (StreamVideo.this) {
								StreamVideo.this.notifyAll();
							}
						}
					}, "image_available");
				}
			}
		}.start();
	}

	public void run() {
		System.out.println("Connecting to " + this.server + "...");
		try (final Jedis redis = new Jedis(this.server, Protocol.DEFAULT_PORT, this.ssl)) {
			this.stream.start();

			int width = 0, height = 0;
			while (true) {
				try {
					synchronized (this) {
						wait(); // until imageAvailable
					}
					if (width == 0 || height == 0) {
						final String imgsize = redis.get("image_size");
						width = Integer.parseInt(imgsize.substring(0, 3));
						height = Integer.parseInt(imgsize.substring(4, imgsize.length()));
					}
					final byte[] img = redis.get(videotopic);
					this.stream.pushImage(get(img, width, height));
				} catch (final Exception e) {
					e.printStackTrace(); // FIXME
				}
			}
		}
	}

	private static BufferedImage get(final byte[] img, final int width, final int height) {
		final ComponentColorModel cm = new ComponentColorModel(ColorSpace.getInstance(ColorSpace.CS_sRGB), false, false,
				Transparency.OPAQUE, DataBuffer.TYPE_BYTE);
		final SampleModel sm = cm.createCompatibleSampleModel(width, height);
		final DataBufferByte db = new DataBufferByte(width * height * 3);
		final WritableRaster r = Raster.createWritableRaster(sm, db, new Point(0, 0));
		final BufferedImage bm = new BufferedImage(cm, r, false, null);
		r.setDataElements(0, 0, width, height, img);
		return bm;
	}
}
