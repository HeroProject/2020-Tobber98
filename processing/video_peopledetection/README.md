# Video People Detection
This Python script takes a video input stream from the CBSR system (e.g. from a [robot](https://bitbucket.org/socialroboticshub/input/src/master/robot_camera/) or your [computer](https://bitbucket.org/socialroboticshub/input/src/master/computer_camera/)), runs a people detection on it (as often as it can), and feeds a signal back into the CBSR system as soon as it detected one or more persons.

The script is not meant to be executed stand-alone, but is integrated in the CBSR server system. The RGB color system is assumed. The detection is implemented by combining two cascade classifiers (head-shoulder and frontal-face), only triggering if both classifiers apply to an overlapping area.

This project requires the input resolution to be set, which is automatically done through the CBSR system.