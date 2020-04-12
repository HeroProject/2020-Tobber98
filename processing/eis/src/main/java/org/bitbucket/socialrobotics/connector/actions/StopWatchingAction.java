package org.bitbucket.socialrobotics.connector.actions;

public class StopWatchingAction extends RobotAction {
	public final static String NAME = "stopWatching";

	public StopWatchingAction() {
		super(null);
	}

	@Override
	public boolean isValid() {
		return true;
	}

	@Override
	public String getTopic() {
		return "action_video";
	}

	@Override
	public String getData() {
		return "stop watching";
	}
}
