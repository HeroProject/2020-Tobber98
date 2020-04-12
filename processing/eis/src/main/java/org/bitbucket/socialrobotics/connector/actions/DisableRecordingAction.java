package org.bitbucket.socialrobotics.connector.actions;

public class DisableRecordingAction extends RobotAction {
	public final static String NAME = "disableRecording";

	public DisableRecordingAction() {
		super(null);
	}

	@Override
	public boolean isValid() {
		return true;
	}

	@Override
	public String getTopic() {
		return "dialogflow_record";
	}

	@Override
	public String getData() {
		return "0";
	}
}
