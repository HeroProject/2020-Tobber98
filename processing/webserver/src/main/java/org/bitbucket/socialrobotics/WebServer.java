package org.bitbucket.socialrobotics;

import java.io.FileInputStream;
import java.security.KeyStore;
import java.security.cert.Certificate;
import java.security.cert.CertificateException;
import java.security.cert.X509Certificate;
import java.util.prefs.Preferences;

import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLServerSocketFactory;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;
import javax.swing.JOptionPane;

import fi.iki.elonen.NanoHTTPD;
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPubSub;
import redis.clients.jedis.Protocol;

public class WebServer {
	private static final String[] topics = new String[] { "render_html", "action_audio", "text_speech",
			"text_transcript" };
	private static final int httpServerPort = 8000;
	private static final int socketServerPort = 8001;
	private final String redisServer;
	private final boolean redisSSL;
	private final WebSocketServer webSocketServer;
	private final WebHttpServer webHttpServer;

	public static void main(final String... args) {
		final Preferences prefs = Preferences.userRoot().node("cbsr");
		final String server = (args.length > 0) ? args[0]
				: JOptionPane.showInputDialog("Server IP", prefs.get("server", ""));
		prefs.put("server", server);
		final boolean ssl = (args.length <= 1); // any text as second arg disables ssl

		try {
			final WebServer webserver = new WebServer(server, ssl);
			webserver.listen();
		} catch (final Exception e) {
			e.printStackTrace();
			System.exit(-1);
		}
	}

	public WebServer(final String redisServer, final boolean redisSSL) throws Exception {
		this.redisServer = redisServer;
		this.redisSSL = redisSSL;

		final SSLServerSocketFactory ssl = NanoHTTPD.makeSSLSocketFactory("/keystore.jks", "changeit".toCharArray());
		this.webHttpServer = new WebHttpServer(httpServerPort);
		this.webHttpServer.makeSecure(ssl, null);
		this.webHttpServer.start(0);
		this.webSocketServer = new WebSocketServer(socketServerPort, connect());
		this.webSocketServer.makeSecure(ssl, null);
		this.webSocketServer.start(0);
	}

	public void listen() throws Exception {
		try (final Jedis redis = connect()) {
			redis.ping();
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

	private Jedis connect() throws Exception {
		if (this.redisSSL) {
			final KeyStore keyStore = KeyStore.getInstance("JKS");
			keyStore.load(new FileInputStream("../truststore.jks"), "changeit".toCharArray());
			final Certificate original = ((KeyStore.TrustedCertificateEntry) keyStore.getEntry("cbsr", null))
					.getTrustedCertificate();
			final TrustManager bypass = new X509TrustManager() {
				@Override
				public X509Certificate[] getAcceptedIssuers() {
					return new X509Certificate[] { (X509Certificate) original };
				}

				@Override
				public void checkClientTrusted(final X509Certificate[] chain, final String authType)
						throws CertificateException {
					checkServerTrusted(chain, authType);
				}

				@Override
				public void checkServerTrusted(final X509Certificate[] chain, final String authType)
						throws CertificateException {
					if (chain.length != 1 || !chain[0].equals(original)) {
						throw new CertificateException("Invalid certificate provided");
					}
				}
			};
			final SSLContext sslContext = SSLContext.getInstance("TLS");
			sslContext.init(null, new TrustManager[] { bypass }, null);
			return new Jedis(this.redisServer, Protocol.DEFAULT_PORT, true, sslContext.getSocketFactory(), null, null);
		} else {
			return new Jedis(this.redisServer);
		}
	}
}
