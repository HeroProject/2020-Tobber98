# Robot Actions
This Python script is meant to be copied to a Nao/Pepper robot, where it will feed action requests from the CBSR system into the robot (in parallel).
These actions are: say, say_animated, gesture, eyecolour, audio_language, idle, play_audio, and speech_param.
Most of these actions also create an event to signify their start and end.