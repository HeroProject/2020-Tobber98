package org.bitbucket.socialrobotics.connector.actions;

import java.util.List;

import eis.iilang.Identifier;
import eis.iilang.Parameter;

public class SetLanguageAction extends RobotAction {
	public final static String NAME = "setLanguage";

	/**
	 * @param parameters A list of 1 identifier: the language identifier to be used
	 *                   in DialogFlow. This action is used internally AND passed to
	 *                   Kafka, but probably not used yet (by the speech recogn).
	 */
	public SetLanguageAction(final List<Parameter> parameters) {
		super(parameters);
	}

	@Override
	public boolean isValid() {
		return (getParameters().size() == 1) && (getParameters().get(0) instanceof Identifier);
	}

	@Override
	public String getTopic() {
		return "audio_language"; // for speech recognition & talking
	}

	@Override
	public String getData() {
		return ((Identifier) getParameters().get(0)).getValue();
	}
}
