package org.bitbucket.socialrobotics.connector.actions;

import java.util.List;

import eis.iilang.Identifier;
import eis.iilang.Parameter;

public class TabletShowVideoAction extends RobotAction {
	public final static String NAME = "showVideo";

	/**
	 * @param parameters A list of 1 identifier: a video URL
	 */
	public TabletShowVideoAction(final List<Parameter> parameters) {
		super(parameters);
	}

	@Override
	public boolean isValid() {
		return (getParameters().size() == 1) && (getParameters().get(0) instanceof Identifier);
	}

	@Override
	public String getTopic() {
		return "tablet_video";
	}

	@Override
	public String getData() {
		return ((Identifier) getParameters().get(0)).getValue();
	}
}
