Live Audio Tool
===============

Live Audio Tool can be used during audio/radio broadcasting as an audio recorder and clipper.

During events such as radio sports commentary, the clipper allows you to easily and quickly export clips from an audio input in real time, for immediate use in highlights or replay.

## Usage

### Recorder

The Recorder can be used alone to record for long periods of time, as well as being used with the Clipper. This recorder exports audio directly to a WAV file only.

You should choose where you want to store all recordings. This is your "Recording Filename". Enter the file name that will be stored. Here you can use the following format directives to format your file name, which will be replaced with the current date and time when the recording is started. If you choose a file name which will be the same every time and the file already exists, you must change the filename before you are able to start a new recording.

Day - %d
Month - %m
Year - %Y
Hour - %H
Minute - %M
Second - %S

Any recording device available on your system can be selected from the drop down menu. You cannot change recording device while recording.

All settings are automatically saved as changes are made. You can revert to the default settings at any point.

### Clipper

The Clipper can work together with, or independently of the built in recorder.

To use the clipper with the recorder, check the "Use Recorder" box. This will automatically use the recorder's audio file to produce clips. You must start the recorder before you can use the clipper.

OPTIONAL: If you want to use an external recorder, it must export the audio directly to a file. This file can be any format, however WAV will work best if you want accurate start and end times. Once you have started the external recorder, you must select the recording file before you can use the clipper.

You should choose where you want to store all clips as they are exported. These are your "Output files". Enter the file name that will be stored. Here you can use the following format directives to format your file name, which will be replaced with the current date and time when the clip is stored. If you choose a file name which will be the same every time, the previous file will be overwritten when the clip is stored.

Day - %d
Month - %m
Year - %Y
Hour - %H
Minute - %M
Second - %S

The pre buffer is the length of time (in seconds) before a clip is started, that will be included in the clip. This can be any value between 0 and 99 seconds. This avoids losing any desired part of a clip which has happened before the clip was started.

The post buffer is the length of time (in seconds) after a clip is stopped, that will be included in the clip. This can be any value between 0 and 99 seconds. This avoids losing any desired part of a clip which has happened after the clip was ended.

All settings are automatically saved as changes are made. You can revert to the default settings at any point.

### Settings

As well as being able to change the settings for each tool, you are able to change the language of the program. In order to do this, simply click show settings, and select your desired language from the dropdown menu.

## Development

### Getting Started

First, clone the repository:

    $ git clone https://github.com/TomGC96/live-audio-tool.git

You should now create a Python virtual environment to work in, ensuring it uses Python 3:

    $ virtualenv env -p python3

Then activate the environment:

    $ source env/bin/activate

You now need to install all the dependencies Live Audio Tool uses:

    $ pip3 install -r requirements.txt

You must also install ffmpeg and ffprobe on your system in order to use the clipper.

You can then run the app with:

    $ python3 main.py

### Translation

In order to use and create your own translations, you need to generate a ".pot" translation template file. Once generated, you can create a .po file with a text editor, or by using the "Poedit" tool. You will need to compile your .po files to ".mo" in order to use the translations in Live Audio Tool. The .mo file should be included in the same folder as the .po file for each language. You also need to add information about each new language to "available-languages.yaml" in the same way as the previous languages have been added, so that Live Audio Tool knows which languages are available to it. Ensure that the "language-code" is the same as the file name of your translation.
