package org.bitbucket.socialrobotics.connector.actions;

public class SetNonIdleAction extends RobotAction {
	public final static String NAME = "setNonIdle";

	public SetNonIdleAction() {
		super(null);
	}

	@Override
	public boolean isValid() {
		return true;
	}

	@Override
	public String getTopic() {
		return "action_idle";
	}

	@Override
	public String getData() {
		return "false";
	}
}
