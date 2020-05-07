package org.bitbucket.socialrobotics.connector.actions;

import eis.iilang.Parameter;

import java.util.List;

public class PlayLoadedAudioAction extends PlayAudioAction {
	public final static String NAME = "playLoadedAudio";

	/**
	 * @param parameters A list of 1 identifier, the URL for the audio file(stream)
	 */
	public PlayLoadedAudioAction(final List<Parameter> parameters) {
		super(parameters, "loaded");
	}

}
