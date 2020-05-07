package org.bitbucket.socialrobotics.connector.actions;

import eis.iilang.Identifier;
import eis.iilang.Parameter;

import java.util.List;

public class AddMemoryEntryAction extends RobotAction {
	public final static String NAME = "addMemoryEntry";

	/**
	 * @param parameters A list of 3 identifiers represent the user ID, the entry key and the entry data that
	 *                      needs to be stored.
	 */
	public AddMemoryEntryAction(final List<Parameter> parameters) {
		super(parameters);
	}

	@Override
	public boolean isValid() {
		return (getParameters().size() == 3) && (getParameters().get(0) instanceof Identifier)
				&& (getParameters().get(1) instanceof Identifier) &&  (getParameters().get(2) instanceof Identifier);
	}

	@Override
	public String getTopic() {
		return "memory_add_entry";
	}

	@Override
	public String getData() {
		String userID = ((Identifier) getParameters().get(0)).getValue();
		String key = ((Identifier) getParameters().get(1)).getValue();
		String data = ((Identifier) getParameters().get(2)).toProlog();

		return userID + ";" + key + ";" + data;
	}
}
