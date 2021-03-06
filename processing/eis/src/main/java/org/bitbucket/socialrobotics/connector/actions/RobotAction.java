package org.bitbucket.socialrobotics.connector.actions;

import java.util.List;

import eis.iilang.Action;
import eis.iilang.Parameter;

public abstract class RobotAction {
	private final List<Parameter> parameters;

	protected RobotAction(final List<Parameter> parameters) {
		this.parameters = parameters;
	}

	protected List<Parameter> getParameters() {
		return this.parameters;
	}

	public abstract boolean isValid();

	public abstract String getTopic();

	public abstract String getData();

	public static RobotAction getRobotAction(final Action action) {
		final List<Parameter> parameters = action.getParameters();
		switch (action.getName()) {
		// ROBOT ACTIONS
		case SayAction.NAME:
			return new SayAction(parameters);
		case SayAnimatedAction.NAME:
			return new SayAnimatedAction(parameters);
		case StartListeningAction.NAME:
			return new StartListeningAction(parameters);
		case StopListeningAction.NAME:
			return new StopListeningAction();
		case EnableRecordingAction.NAME:
			return new EnableRecordingAction();
		case DisableRecordingAction.NAME:
			return new DisableRecordingAction();
		case GestureAction.NAME:
			return new GestureAction(parameters);
		case SetEyeColourAction.NAME:
			return new SetEyeColourAction(parameters);
		case SetIdleAction.NAME:
			return new SetIdleAction(parameters);
		case SetNonIdleAction.NAME:
			return new SetNonIdleAction();
		case StartWatchingAction.NAME:
			return new StartWatchingAction();
		case StopWatchingAction.NAME:
			return new StopWatchingAction();
		case LoadAudioAction.NAME:
			return new LoadAudioAction(parameters);
		case PlayRawAudioAction.NAME:
			return new PlayRawAudioAction(parameters);
		case PlayLoadedAudioAction.NAME:
			return new PlayLoadedAudioAction(parameters);
		case ClearLoadedAudioAction.NAME:
			return new ClearLoadedAudioAction();
		case SetLanguageAction.NAME:
			return new SetLanguageAction(parameters);
		case SetSpeechParamAction.NAME:
			return new SetSpeechParamAction(parameters);
		case TakePictureAction.NAME:
			return new TakePictureAction();
		case TurnLeftAction.NAME:
			return new TurnLeftAction();
		case TurnRightAction.NAME:
			return new TurnRightAction();
		case WakeUpAction.NAME:
			return new WakeUpAction();
		case RestAction.NAME:
			return new RestAction();
		case EnableBreathingAction.NAME:
			return new EnableBreathingAction(parameters);
		case DisableBreathingAction.NAME:
			return new DisableBreathingAction(parameters);
		// TABLET ACTIONS
		case TabletOpenAction.NAME:
			return new TabletOpenAction();
		case TabletCloseAction.NAME:
			return new TabletCloseAction();
		case TabletShowImageAction.NAME:
			return new TabletShowImageAction(parameters);
		case TabletShowVideoAction.NAME:
			return new TabletShowVideoAction(parameters);
		case TabletShowWebpageAction.NAME:
			return new TabletShowWebpageAction(parameters);
		case TabletRenderAction.NAME:
			return new TabletRenderAction(parameters);
		// MEMORY ACTIONS
		case GetUserSession.NAME:
			return new GetUserSession(parameters);
		case AddMemoryEntryAction.NAME:
			return new AddMemoryEntryAction(parameters);
		case GetUserDataAction.NAME:
			return new GetUserDataAction(parameters);
		case SetUserDataAction.NAME:
			return new SetUserDataAction(parameters);
		// OTHER
		case WebRequestAction.NAME:
			return new WebRequestAction(parameters);
		default:
			return null;
		}
	}
}
