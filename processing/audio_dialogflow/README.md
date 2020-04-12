# Audio Dialogflow
This Java project takes an audio input stream from the CBSR system (e.g. from a [robot](https://bitbucket.org/socialroboticshub/input/src/master/robot_microphone/) or your [computer](https://bitbucket.org/socialroboticshub/input/src/master/computer_microphone/)), streams it into Google's [Dialogflow](https://cloud.google.com/dialogflow/), and feeds the resulting recognised text and intent (if any) back into the CBSR system.

The JAR file is not meant to be executed stand-alone, but is integrated in the CBSR server system. A bitrate of 16kHz (linear 16-bit encoding) is assumed for the (single channel) audio input. The input audio can optionally be recorded to WAV files as well, which are normalized (i.e. boosted).

This project requires a Dialogflow agent (string ID), key (path to JSON file) and language (e.g. nl-NL or en-US) to be set, which can all be done through the CBSR system. Contexts can optionally be used as well.  