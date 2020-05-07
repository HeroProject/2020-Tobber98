package org.bitbucket.socialrobotics.connector.actions;

public class RestAction extends RobotAction {
	public final static String NAME = "rest";

	public RestAction() {
		super(null);
	}

	@Override
	public boolean isValid() {
		return true;
	}

	@Override
	public String getTopic() {
		return "action_" + NAME;
	}

	@Override
	public String getData() {
		return "";
	}
}
