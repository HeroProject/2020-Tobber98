package org.bitbucket.socialrobotics.connector.actions;

public class TabletOpenAction extends RobotAction {
	public final static String NAME = "tabletOpen";

	public TabletOpenAction() {
		super(null);
	}

	@Override
	public boolean isValid() {
		return true;
	}

	@Override
	public String getTopic() {
		return "tablet_control";
	}

	@Override
	public String getData() {
		return "show";
	}
}
