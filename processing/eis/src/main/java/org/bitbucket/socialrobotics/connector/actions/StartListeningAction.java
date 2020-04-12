package org.bitbucket.socialrobotics.connector.actions;

import java.util.List;

import eis.iilang.Identifier;
import eis.iilang.Parameter;

public class StartListeningAction extends RobotAction {
	public final static String NAME = "startListening";

	/**
	 * @param parameters A list of 1 identifier indicating the context (optional)
	 */
	public StartListeningAction(final List<Parameter> parameters) {
		super(parameters);
	}

	@Override
	public boolean isValid() {
		return (getParameters().isEmpty())
				|| (getParameters().size() == 1 && getParameters().get(0) instanceof Identifier);
	}

	public String getContext() {
		return getParameters().isEmpty() ? "" : ((Identifier) getParameters().get(0)).toProlog();
	}

	@Override
	public String getTopic() {
		return "action_audio";
	}

	@Override
	public String getData() {
		return "start listening";
	}
}
