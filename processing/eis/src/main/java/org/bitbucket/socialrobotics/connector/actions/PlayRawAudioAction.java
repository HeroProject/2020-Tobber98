package org.bitbucket.socialrobotics.connector.actions;

import eis.iilang.Parameter;

import java.util.List;

public class PlayRawAudioAction extends PlayAudioAction {
	public final static String NAME = "playAudio"; //playAudio instead of playRawAudio is used for backwards compatibility

	/**
	 * @param parameters A list of 1 identifier, the URL for the audio file(stream)
	 */
	public PlayRawAudioAction(final List<Parameter> parameters) {
		super(parameters, "raw");
	}
}