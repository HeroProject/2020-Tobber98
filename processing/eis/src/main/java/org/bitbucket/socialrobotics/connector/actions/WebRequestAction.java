package org.bitbucket.socialrobotics.connector.actions;

import java.util.List;

import eis.iilang.Identifier;
import eis.iilang.Parameter;

public class WebRequestAction extends RobotAction {
	public enum WebRequest {
		MUSIC_ARTIST, MUSIC_GENRE, MOVIE_ACTOR, MOVIE_DIRECTOR, MOVIE_GENRE, MOVIE_FAV_MOVIE, TRAVEL_HAS_VISITED,
		TRAVEL_WANTS_TO_VISIT, SPORTS_FAV_SPORT
	}

	public final static String NAME = "webRequest";

	/**
	 * @param parameters A list of two identifiers. The first must be one of:
	 *                   [music_artist, music_genre, movie_actor, movie_director,
	 *                   movie_genre, movie_fav_movie, travel_has_visited,
	 *                   travel_wants_to_visit, indiv_sport, team_sport]. The second
	 *                   can be an arbitrary input string. Can also be an empty
	 *                   list, which will result in a random response.
	 */
	public WebRequestAction(final List<Parameter> parameters) {
		super(parameters);
	}

	@Override
	public boolean isValid() {
		return getParameters().isEmpty() || ((getParameters().size() == 2)
				&& (getParameters().get(0) instanceof Identifier) && (getParameters().get(1) instanceof Identifier));
	}

	@Override
	public String getTopic() {
		return "action_webrequest";
	}

	@Override
	public String getData() {
		return getParameters().isEmpty() ? ""
				: (((Identifier) getParameters().get(0)).getValue() + "|"
						+ ((Identifier) getParameters().get(1)).getValue());
	}
}
