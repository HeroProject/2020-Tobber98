package org.bitbucket.socialrobotics.connector.actions;

import eis.iilang.Identifier;
import eis.iilang.Parameter;

import java.util.List;

public class GetUserDataAction extends RobotAction {
	public final static String NAME = "getUserData";

	/**
	 * @param parameters A list of 2 identifiers: a (string) user id and a (string) user data key.
	 */
	public GetUserDataAction(final List<Parameter> parameters) {
		super(parameters);
	}

	@Override
	public boolean isValid() {
		return (getParameters().size() == 2) && (getParameters().get(0) instanceof Identifier) &&
				(getParameters().get(1) instanceof Identifier);
	}

	@Override
	public String getTopic() {
		return "memory_get_user_data";
	}

	@Override
	public String getData() {
		return ((Identifier) getParameters().get(0)).getValue() + ";" +
				((Identifier) getParameters().get(1)).getValue();
	}
}
