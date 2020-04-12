package org.bitbucket.socialrobotics.connector.actions;

import java.util.List;

import eis.iilang.Identifier;
import eis.iilang.Parameter;

public class TabletShowImageAction extends RobotAction {
	public final static String NAME = "showImage";

	/**
	 * @param parameters A list of 1 identifier: an image URL
	 */
	public TabletShowImageAction(final List<Parameter> parameters) {
		super(parameters);
	}

	@Override
	public boolean isValid() {
		return (getParameters().size() == 1) && (getParameters().get(0) instanceof Identifier);
	}

	@Override
	public String getTopic() {
		return "tablet_image";
	}

	@Override
	public String getData() {
		return ((Identifier) getParameters().get(0)).getValue();
	}
}
