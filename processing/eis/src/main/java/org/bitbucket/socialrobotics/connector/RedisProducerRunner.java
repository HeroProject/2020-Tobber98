package org.bitbucket.socialrobotics.connector;

import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;

import org.bitbucket.socialrobotics.connector.actions.CloseAction;
import org.bitbucket.socialrobotics.connector.actions.RobotAction;
import org.bitbucket.socialrobotics.connector.actions.TabletCloseAction;
import org.bitbucket.socialrobotics.connector.actions.TabletOpenAction;

import redis.clients.jedis.Jedis;

class RedisProducerRunner extends RedisRunner {
	private final BlockingQueue<RobotAction> actionQueue;

	public RedisProducerRunner(final CBSRenvironment parent, final String server) {
		super(parent, server);
		this.actionQueue = new LinkedBlockingQueue<>();
	}

	@Override
	public void run() {
		final Jedis redis = getRedis();
		// process the action queue into outgoing messages
		while (isRunning()) {
			try {
				System.out.println("Waiting for action...");
				final RobotAction next = this.actionQueue.take();
				if (next instanceof CloseAction) {
					super.shutdown();
				} else {
					System.out.println("Got " + next.getData() + " on " + next.getTopic());
					redis.publish(next.getTopic(), next.getData());
				}
				if (next instanceof TabletCloseAction) {
					this.parent.setTabletDisconnected();
				}
			} catch (final Exception e) {
				if (isRunning()) {
					e.printStackTrace(); // FIXME
				}
			}
		}
	}

	public void queueAction(final RobotAction action) {
		this.actionQueue.add(action);
		if (action instanceof TabletOpenAction) { // block-all until established
			while (!this.parent.isTabletConnected()) {
				try {
					Thread.sleep(0);
				} catch (final InterruptedException e) {
					break;
				}
			}
		}
	}

	@Override
	public void shutdown() {
		queueAction(new CloseAction());
	}
}