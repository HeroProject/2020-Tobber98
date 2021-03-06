package org.bitbucket.socialrobotics.connector.actions;

import eis.iilang.Identifier;
import eis.iilang.Parameter;

import java.util.List;

public abstract class PlayAudioAction extends RobotAction {

	protected String audioType;

	/**
	 * @param parameters A list of 1 identifier, the URL for the audio file(stream)
	 * @param audioType type of audio to be played (raw or loaded)
	 */
	public PlayAudioAction(final List<Parameter> parameters, String audioType) {
		super(parameters);
		this.audioType = audioType;
	}

	@Override
	public boolean isValid() {
		return (getParameters().size() == 1) && (getParameters().get(0) instanceof Identifier);
	}

	@Override
	public String getTopic() {
		return "action_play_audio";
	}

	@Override
	public String getData() {
		return ((Identifier) getParameters().get(0)).getValue() + ";" + audioType;
	}
}
