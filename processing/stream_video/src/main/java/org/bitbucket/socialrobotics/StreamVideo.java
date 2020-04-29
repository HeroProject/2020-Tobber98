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
import redis.clients.jedis.Protocol;

public class StreamVideo {
	private static final byte[] videotopic = "image_stream".getBytes();
	private static final String sizetopic = "image_size";
	private static final String frametopic = "image_frame";
	private final String server;
	private final boolean ssl;
	private final VideoServer stream;
	private int frame = -1;

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

	public void run() {
		System.out.println("Connecting to " + this.server + "...");
		try (final Jedis redis = new Jedis(this.server, Protocol.DEFAULT_PORT, this.ssl)) {
			String imgsize = null;
			System.out.println("Fetching image size...");
			while (imgsize == null) {
				imgsize = redis.get(sizetopic);
			}
			final int width = Integer.parseInt(imgsize.substring(0, 3));
			final int height = Integer.parseInt(imgsize.substring(4, imgsize.length()));
			System.out.println("Got: " + width + "x" + height);

			this.stream.start();

			while (true) {
				final String frame = redis.get(frametopic);
				final int frameno = (frame == null) ? -1 : Integer.parseInt(frame);
				if (frameno == 0 || frameno > this.frame) {
					try {
						final byte[] img = redis.get(videotopic);
						this.stream.pushImage(get(img, width, height));
						this.frame = frameno;
					} catch (final Exception e) {
						e.printStackTrace(); // FIXME
					}
				} else {
					try {
						Thread.sleep(1);
					} catch (final InterruptedException ignore) {
					}
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
