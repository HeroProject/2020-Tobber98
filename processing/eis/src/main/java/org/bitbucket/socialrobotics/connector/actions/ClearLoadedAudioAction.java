package org.bitbucket.socialrobotics.connector.actions;

public class ClearLoadedAudioAction extends RobotAction {
	public final static String NAME = "clearLoadedAudio";

	public ClearLoadedAudioAction() {
		super(null);
	}

	@Override
	public boolean isValid() {
		return true;
	}

	@Override
	public String getTopic() {
		return "action_clear_loaded_audio";
	}

	@Override
	public String getData() {
		return "";
	}
}
