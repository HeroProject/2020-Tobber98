package org.bitbucket.socialrobotics.connector.actions;

import eis.iilang.Identifier;
import eis.iilang.Parameter;

import java.util.List;

public class GetUserSession extends RobotAction {
	public final static String NAME = "getUserSession";

	/**
	 * @param parameters id of user.
	 */
	public GetUserSession(final List<Parameter> parameters) {
		super(parameters);
	}

	@Override
	public boolean isValid() {
		return (getParameters().size() == 1) && (getParameters().get(0) instanceof Identifier);
	}

	@Override
	public String getTopic() {
		return "memory_user_session";
	}

	@Override
	public String getData() {
		return ((Identifier) getParameters().get(0)).getValue();
	}
}
