package org.bitbucket.socialrobotics.connector;

import redis.clients.jedis.Jedis;

public abstract class RedisRunner extends Thread {
	protected final CBSRenvironment parent;
	protected final String server;
	private Jedis redis;

	RedisRunner(final CBSRenvironment parent, final String server) {
		this.parent = parent;
		this.server = server;
	}

	@Override
	public abstract void run();

	protected Jedis getRedis() {
		if (this.redis == null) {
			this.redis = new Jedis(this.server);
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
