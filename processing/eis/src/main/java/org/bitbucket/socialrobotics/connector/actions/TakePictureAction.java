package org.bitbucket.socialrobotics.connector.actions;

public class TakePictureAction extends RobotAction {
	public final static String NAME = "takePicture";

	public TakePictureAction() {
		super(null);
	}

	@Override
	public boolean isValid() {
		return true;
	}

	@Override
	public String getTopic() {
		return "action_take_picture";
	}

	@Override
	public String getData() {
		return "";
	}
}
