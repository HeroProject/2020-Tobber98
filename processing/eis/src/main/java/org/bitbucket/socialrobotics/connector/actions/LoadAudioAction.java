package org.bitbucket.socialrobotics.connector.actions;

import eis.iilang.Identifier;
import eis.iilang.Parameter;

import java.util.List;

public class LoadAudioAction extends RobotAction {
	public final static String NAME = "loadAudio";

	/**
	 * @param parameters A list of 1 identifier, the URL for the audio file(stream)
	 */
	public LoadAudioAction(final List<Parameter> parameters) {
		super(parameters);
	}

	@Override
	public boolean isValid() {
		return (getParameters().size() == 1) && (getParameters().get(0) instanceof Identifier);
	}

	@Override
	public String getTopic() {
		return "action_load_audio";
	}

	@Override
	public String getData() {
		return ((Identifier) getParameters().get(0)).getValue();
	}
}
