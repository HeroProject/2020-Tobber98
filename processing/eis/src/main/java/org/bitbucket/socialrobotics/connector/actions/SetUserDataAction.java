package org.bitbucket.socialrobotics.connector.actions;

import eis.iilang.Identifier;
import eis.iilang.Parameter;

import java.util.List;

public class SetUserDataAction extends RobotAction {
	public final static String NAME = "setUserData";

	/**
	 * @param parameters A list of 3 identifiers: a (string) user id, a (string) user data key and a corresponding
	 * 	 *                   (string) user data value.
	 */
	public SetUserDataAction(final List<Parameter> parameters) {
		super(parameters);
	}

	@Override
	public boolean isValid() {
		return (getParameters().size() == 3) && (getParameters().get(0) instanceof Identifier) &&
				(getParameters().get(1) instanceof Identifier) && (getParameters().get(2) instanceof Identifier);
	}

	@Override
	public String getTopic() {
		return "memory_set_user_data";
	}

	@Override
	public String getData() {
		return ((Identifier) getParameters().get(0)).getValue() + ";" +
				((Identifier) getParameters().get(1)).getValue() + ';' +
				((Identifier) getParameters().get(2)).getValue();
	}
}
