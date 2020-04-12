# Audio Google STT
This Python script takes an audio input stream from the CBSR system (e.g. from a [robot](https://bitbucket.org/socialroboticshub/input/src/master/robot_microphone/) or your [computer](https://bitbucket.org/socialroboticshub/input/src/master/computer_microphone/)), streams it into Google's [Speech-to-Text](https://cloud.google.com/speech-to-text/), and feeds the resulting recognised text back into the CBSR system.

The script not meant to be executed stand-alone, but is integrated in the CBSR server system. A bitrate of 16kHz (linear 16-bit encoding) is assumed for the (single channel) audio input.

This project requires a language (e.g. nl-NL or en-US) to be set, which can be done through the CBSR system. A credentials file is included (don't share!).

**All projects run on DialogFlow currently, and this project is thus not maintained.**