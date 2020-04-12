package org.bitbucket.socialrobotics.connector.actions;

import java.util.List;

import eis.iilang.Identifier;
import eis.iilang.Parameter;

public class SetIdleAction extends RobotAction {
	public final static String NAME = "setIdle";

	public SetIdleAction(final List<Parameter> parameters) {
		super(parameters);
	}

	@Override
	public boolean isValid() {
		return getParameters().isEmpty()
				|| (getParameters().size() == 1 && getParameters().get(0) instanceof Identifier);
	}

	@Override
	public String getTopic() {
		return "action_idle";
	}

	@Override
	public String getData() {
		return getParameters().isEmpty() ? "true" : ((Identifier) getParameters().get(0)).getValue();
	}
}
