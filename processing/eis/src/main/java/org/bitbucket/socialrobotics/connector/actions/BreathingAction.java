package org.bitbucket.socialrobotics.connector.actions;

import eis.iilang.Identifier;
import eis.iilang.Parameter;

import java.util.List;

public abstract class BreathingAction extends RobotAction {

	protected String enable;

	/**
	 *
	 * @param parameters A list of 1 optional identifier, the body part that should be affected by the breathing behavior
	 * @param enable boolean that signals to enable or disable the breathing behavior
	 */
	public BreathingAction(final List<Parameter> parameters, boolean enable) {
		super(parameters);
		this.enable = enable ? "1" : "0";
	}

	@Override
	public boolean isValid() {
		return getParameters().isEmpty()
				|| (getParameters().size() == 1 && getParameters().get(0) instanceof Identifier);
	}

	@Override
	public String getTopic() {
		return "action_set_breathing";
	}

	@Override
	public String getData() {
		return getParameters().isEmpty() ? "Body;" + enable :
				((Identifier) getParameters().get(0)).getValue() + ";" + enable;
	}
}
