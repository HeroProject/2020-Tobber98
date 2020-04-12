
package org.bitbucket.socialrobotics;

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

public class DebugBrowser extends JFrame {
	private static final long serialVersionUID = 1L;
	private static final String[] topics = new String[] { "tablet_control", "tablet_audio", "tablet_image",
			"tablet_video", "tablet_web" };
	private final String server;
	private WebEngine engine;

	public static void main(final String... args) {
		System.setProperty("sun.net.http.allowRestrictedHeaders", "true");
		final String server = (args.length > 0) ? args[0] : JOptionPane.showInputDialog("Server IP");
		final DebugBrowser browser = new DebugBrowser(server);
		browser.run();
	}

	public DebugBrowser(final String server) {
		super("CBSR Browser");
		this.server = server;

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
		try (final Jedis redis = new Jedis(this.server)) {
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
		final String base = "http://" + this.server + ":8000/" + type;
		return (content == null) ? base : (base + "/" + content);
	}
}
