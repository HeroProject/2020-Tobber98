package org.bitbucket.socialrobotics.connector.actions;

import eis.iilang.Parameter;

import java.util.List;

public class EnableBreathingAction extends BreathingAction {
	public final static String NAME = "enableBreathing";

	/**
	 *
	 * @param parameters A list of 1 optional identifier, the body part that should be affected by the breathing behavior
	 */
	public EnableBreathingAction(final List<Parameter> parameters) {
		super(parameters, true);
	}

}
