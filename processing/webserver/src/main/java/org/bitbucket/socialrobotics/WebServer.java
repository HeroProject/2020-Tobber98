package org.bitbucket.socialrobotics;

import javax.swing.JOptionPane;

import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPubSub;

public class WebServer {
	private static final String[] topics = new String[] { "render_html", "action_audio", "text_speech",
			"text_transcript" };
	private static final int httpServerPort = 8000;
	private static final int socketServerPort = 8001;
	private final String redisServer;
	private WebSocketServer webSocketServer;
	private WebHttpServer webHttpServer;

	public static void main(final String... args) {
		final String server = (args.length > 0) ? args[0] : JOptionPane.showInputDialog("Server IP");
		final WebServer webserver = new WebServer(server);
		new Thread(new Runnable() {
			@Override
			public void run() {
				webserver.listen();
			}
		}).start();
	}

	public WebServer(final String redisServer) {
		this.redisServer = redisServer;
		try {
			this.webHttpServer = new WebHttpServer(httpServerPort);
			this.webHttpServer.start(0);
			this.webSocketServer = new WebSocketServer(socketServerPort, redisServer);
			this.webSocketServer.start(0);
		} catch (final Exception e) {
			e.printStackTrace(); // FIXME
		}
	}

	public void listen() {
		try (final Jedis redis = new Jedis(this.redisServer)) {
			System.out.println("Subscribing to " + this.redisServer);
			redis.subscribe(new JedisPubSub() {
				@Override
				public void onMessage(final String channel, final String message) {
					try {
						if (WebServer.this.webSocketServer.isAlive()) {
							WebServer.this.webSocketServer.send(channel, message);
						}
					} catch (final Exception e) {
						e.printStackTrace(); // FIXME
					}
				}
			}, topics);
		}
	}
}
