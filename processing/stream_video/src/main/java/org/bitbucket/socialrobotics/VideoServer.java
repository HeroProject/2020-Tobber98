package org.bitbucket.socialrobotics;

import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.OutputStream;
import java.net.ServerSocket;
import java.net.Socket;

import javax.imageio.ImageIO;

public class VideoServer extends Thread {
	private final static String boundary = "stream";
	private final static String nl = "\r\n";
	private final ServerSocket serverSocket;
	private Socket socket;
	private volatile boolean connected = false;

	VideoServer() throws Exception {
		this.serverSocket = new ServerSocket(8001);
	}

	@Override
	public void run() {
		while (!VideoServer.this.serverSocket.isClosed()) {
			try {
				System.out.println("Waiting for connection...");
				VideoServer.this.socket = VideoServer.this.serverSocket.accept();
				VideoServer.this.connected = true;
				System.out.println("Connected! " + VideoServer.this.socket.getRemoteSocketAddress());

				writeHeader();

				while (VideoServer.this.connected) {
					Thread.sleep(1);
				}
				if (VideoServer.this.socket != null) {
					VideoServer.this.socket.close();
				}
			} catch (final Exception e) {
				e.printStackTrace(); // FIXME
			}
		}
	}

	private void writeHeader() throws Exception {
		final StringBuilder header = new StringBuilder();
		header.append("HTTP/1.1 200 OK").append(nl).append("Content-Type: multipart/x-mixed-replace; boundary=")
				.append(boundary).append(nl).append(nl);
		this.socket.getOutputStream().write(header.toString().getBytes());
	}

	public void pushImage(final BufferedImage img) throws Exception {
		if (this.connected) {
			try {
				final ByteArrayOutputStream baos = new ByteArrayOutputStream();
				ImageIO.write(img, "jpg", baos);

				final StringBuilder start = new StringBuilder();
				start.append("--").append(boundary).append(nl).append("Content-Type: image/jpeg").append(nl)
						.append("Content-Length: ").append(baos.size()).append(nl).append(nl);

				final OutputStream outputStream = this.socket.getOutputStream();
				outputStream.write(start.toString().getBytes());
				baos.writeTo(outputStream);
				outputStream.write((nl + nl).getBytes());
			} catch (final Exception e) {
				stopStreamingServer();
				throw e;
			}
		}
	}

	public void stopStreamingServer() {
		this.connected = false;
		try {
			this.serverSocket.close();
		} catch (final Exception ignore) {
		}
	}
}
