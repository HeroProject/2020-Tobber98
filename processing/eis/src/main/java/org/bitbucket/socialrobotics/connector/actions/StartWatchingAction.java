package org.bitbucket.socialrobotics.connector.actions;

public class StartWatchingAction extends RobotAction {
	public final static String NAME = "startWatching";

	public StartWatchingAction() {
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
		return "start watching";
	}
}
