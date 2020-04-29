package org.bitbucket.socialrobotics;

import java.util.prefs.Preferences;

import javax.net.ssl.HostnameVerifier;
import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.SSLSession;
import javax.swing.JFrame;
import javax.swing.JOptionPane;

import com.sun.javafx.webkit.WebConsoleListener;

import javafx.application.Platform;
import javafx.embed.swing.JFXPanel;
import javafx.scene.Scene;
import javafx.scene.web.WebEngine;
import javafx.scene.web.WebView;
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPubSub;
import redis.clients.jedis.Protocol;

public class DebugBrowser extends JFrame {
	private static final long serialVersionUID = 1L;
	private static final String[] topics = new String[] { "tablet_control", "tablet_audio", "tablet_image",
			"tablet_video", "tablet_web" };
	private final String server;
	private final boolean ssl;
	private WebEngine engine;

	public static void main(final String... args) {
		final Preferences prefs = Preferences.userRoot().node("cbsr");
		final String server = (args.length > 0) ? args[0]
				: JOptionPane.showInputDialog("Server IP", prefs.get("server", ""));
		prefs.put("server", server);

		System.setProperty("javax.net.ssl.trustStore", "../truststore.jks");
		System.setProperty("javax.net.ssl.trustStorePassword", "changeit");
		System.setProperty("sun.net.http.allowRestrictedHeaders", "true");

		try {
			final DebugBrowser browser = new DebugBrowser(server);
			browser.run();
		} catch (final Exception e) {
			e.printStackTrace();
			System.exit(-1);
		}
	}

	public DebugBrowser(final String server) {
		super("CBSR Browser");
		this.server = server;
		this.ssl = !this.server.equals("192.168.99.100");

		HttpsURLConnection.setDefaultHostnameVerifier(new HostnameVerifier() {
			@Override
			public boolean verify(final String hostname, final SSLSession session) {
				return true;
			}
		});

		final JFXPanel jfxPanel = new JFXPanel();
		WebConsoleListener.setDefaultListener(new WebConsoleListener() {
			@Override
			public void messageAdded(final WebView webView, final String message, final int lineNumber,
					final String sourceId) {
				System.err.println("[" + sourceId + ":" + lineNumber + "] " + message);
			}
		});
		Platform.runLater(new Runnable() {
			@Override
			public void run() {
				final WebView view = new WebView();
				DebugBrowser.this.engine = view.getEngine();
				DebugBrowser.this.engine.setOnError(event -> System.err.println(event.getMessage()));
				DebugBrowser.this.engine.setOnAlert(event -> System.out.println(event.getData()));
				final Scene scene = new Scene(view);
				jfxPanel.setScene(scene);
			}
		});
		add(jfxPanel);

		setSize(1280, 800);
		setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		setVisible(true);
	}

	public void run() {
		try (final Jedis redis = new Jedis(this.server, Protocol.DEFAULT_PORT, this.ssl)) {
			redis.ping();
			System.out.println("Subscribing to " + this.server);
			redis.subscribe(new JedisPubSub() {
				@Override
				public void onMessage(final String channel, final String message) {
					switch (channel) {
					case "tablet_control":
						if (message.equals("show")) {
							load(getURL("index.html", null));
						} else if (message.equals("hide")) {
							load("");
						} else if (message.equals("reload")) {
							load(null);
						}
						break;
					case "tablet_audio":
						load(getURL("audio", message));
						break;
					case "tablet_image":
						load(getURL("img", message));
						break;
					case "tablet_video":
						load(getURL("video", message));
						break;
					case "tablet_web":
						load(message);
						break;
					}
				}
			}, topics);
		}
	}

	private void load(final String url) {
		Platform.runLater(new Runnable() {
			@Override
			public void run() {
				if (url == null) {
					System.out.println("Reloading...");
					DebugBrowser.this.engine.reload();
				} else {
					System.out.println("Loading " + url);
					DebugBrowser.this.engine.load(url);
				}
			}
		});
	}

	private String getURL(final String type, final String content) {
		final String base = "https://" + this.server + ":8000/" + type;
		return (content == null) ? base : (base + "/" + content);
	}
}
