package org.bitbucket.socialrobotics;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import org.json.JSONObject;

import fi.iki.elonen.NanoWSD;
import fi.iki.elonen.NanoWSD.WebSocketFrame.CloseCode;
import redis.clients.jedis.Jedis;

public class WebSocketServer extends NanoWSD {
	private final List<WebSocket> connections;
	private final Jedis redis;

	public WebSocketServer(final int port, final Jedis redis) throws Exception {
		super(port);
		this.redis = redis;
		this.connections = Collections.synchronizedList(new ArrayList<>());
	}

	@Override
	protected WebSocket openWebSocket(final IHTTPSession handshake) {
		final WebSocket connection = new MyWebSocket(handshake);
		synchronized (this.connections) {
			this.connections.add(connection);
		}
		return connection;
	}

	protected void closeWebSocket(final WebSocket connection) {
		synchronized (this.connections) {
			this.connections.remove(connection);
		}
	}

	protected synchronized void send(final String channel, final String message) throws IOException {
		final JSONObject json = new JSONObject();
		json.put("channel", channel);
		json.put("message", message);
		synchronized (this.connections) {
			for (final WebSocket connection : this.connections) {
				connection.send(json.toString());
			}
		}
	}

	private class MyWebSocket extends WebSocket {
		MyWebSocket(final IHTTPSession handshakeRequest) {
			super(handshakeRequest);
		}

		@Override
		protected void onOpen() {
			System.out.println("Socket opened!");
		}

		@Override
		protected void onMessage(final WebSocketFrame message) {
			final String answer = message.getTextPayload();
			if (answer.equals("*")) {
				WebSocketServer.this.redis.publish("tablet_connection", "1");
			} else {
				System.out.println("got: " + answer);
				final String[] split = answer.split("\\|");
				WebSocketServer.this.redis.publish(split[0], split[1]);
			}
		}

		@Override
		protected void onException(final IOException exception) {
			exception.printStackTrace(); // FIXME
		}

		@Override
		protected void onPong(final WebSocketFrame pong) {
		}

		@Override
		protected void onClose(final CloseCode code, final String reason, final boolean initiatedByRemote) {
			System.out.println("Socket closed!");
			closeWebSocket(this);
		}
	}
}
