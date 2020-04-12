# Computer Speakers
This executable JAR file will feed audio (TTS and sound effects) from the CBSR system into your computer's speakers.

```
java -jar computer-speakers.jar localhost C:\Program Files (x86)\eSpeak\command_line ../../processing/webserver
```

The first argument sets the IP address of the CBSR server (localhost by default).
The second argument sets the path to [eSpeak](http://espeak.sourceforge.net/download.html) (see above for the default) which is the library that is used for (Dutch and English) TTS. The third argument sets the path to the webserver (see above for the default) which is required for playing sound effects.