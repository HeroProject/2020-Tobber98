package org.bitbucket.socialrobotics.connector;

import redis.clients.jedis.Jedis;
import redis.clients.jedis.Protocol;

public abstract class RedisRunner extends Thread {
	protected final CBSRenvironment parent;
	protected final String server;
	protected final boolean ssl;
	private Jedis redis;

	RedisRunner(final CBSRenvironment parent, final String server, final boolean ssl) {
		this.parent = parent;
		this.server = server;
		this.ssl = ssl;
	}

	@Override
	public abstract void run();

	protected Jedis getRedis() {
		if (this.redis == null) {
			this.redis = new Jedis(this.server, Protocol.DEFAULT_PORT, this.ssl);
			this.redis.connect();
		}
		return this.redis;
	}

	protected boolean isRunning() {
		return (this.redis != null);
	}

	public void shutdown() {
		if (this.redis != null) {
			this.redis.close();
			this.redis = null;
		}
	}
}
