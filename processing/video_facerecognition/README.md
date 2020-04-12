# Video Face Recognition
This Python script takes a video input stream from the CBSR system (e.g. from a [robot](https://bitbucket.org/socialroboticshub/input/src/master/robot_camera/) or your [computer](https://bitbucket.org/socialroboticshub/input/src/master/computer_camera/)), runs a [face recognition algorithm](https://github.com/ageitgey/face_recognition) on it (as often as it can), and feeds the resulting unique identifiers of faces (if any) back into the CBSR system.

The script is not meant to be executed stand-alone, but is integrated in the CBSR server system. The RGB color system is assumed. A file (face_encodings.p) is used to store the identifiers of faces.

This project requires the input resolution to be set, which is automatically done through the CBSR system.