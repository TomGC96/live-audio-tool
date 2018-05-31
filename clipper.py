import ffmpeg
import time
import datetime
import json

from threading import Thread
from pathlib import Path


STATUS_CODE_READY = 0
STATUS_CODE_WARNING = 1
STATUS_CODE_RECORDING = 2
STATUS_CODE_ERROR = 3

CLIPPER_CONFIG_FILENAME = 'config_clipper.json'


class Clipper:

    def __init__(self):
        self.is_recording = False
        self.in_filename = ""
        self.out_filename = ""
        self.pre_buffer = 0
        self.post_buffer = 0
        self.status = STATUS_CODE_ERROR
        self.start_clip_time = 0
        self.end_clip_time = 0
        self.messages = ""
        self.use_recorder = True
        self.clipped_in_filename = ""

    def write_config(self):
        config = {"in_filename": self.in_filename, "out_filename": self.out_filename, "pre_buffer": self.pre_buffer,
                  "post_buffer": self.post_buffer, "use_recorder": self.use_recorder}
        with open(CLIPPER_CONFIG_FILENAME, 'w') as outfile:
            json.dump(config, outfile)

    def read_config(self):
        try:
            with open(CLIPPER_CONFIG_FILENAME) as json_data_file:
                data = json.load(json_data_file)
                self.in_filename = data["in_filename"]
                self.out_filename = data["out_filename"]
                self.pre_buffer = data["pre_buffer"]
                self.post_buffer = data["post_buffer"]
                self.use_recorder = data["use_recorder"]
        except FileNotFoundError:
            self.in_filename = _("SelectInputRecording.wav")
            self.out_filename = _("AudioClip-%d%m%Y-%H%M%S.mp3")
            self.pre_buffer = 30
            self.post_buffer = 5
            self.use_recorder = True

            self.write_config()

            print(_("Clipper config not found - using default"))

    def export_clip(self, exp_start_time, exp_end_time, exp_in_filename, exp_out_filename):
        time.sleep(self.post_buffer)

        exp_out_filename_formatted = datetime.datetime.today().strftime(exp_out_filename)

        # Start from beginning of clip if buffer has not built up yet
        if exp_start_time < 0:
            exp_start_time = 0

        (ffmpeg
            .input(exp_in_filename, ss=exp_start_time, t=exp_end_time)
            .output(exp_out_filename_formatted)
            .overwrite_output()
            .run()
        )

        return

    @staticmethod
    def get_duration(filename):
        return float(ffmpeg.probe(filename)['format']['duration'])

    def start_stop_clip(self, ui):
        self.update_status()

        if self.status == STATUS_CODE_ERROR:
            ui.show_error_message(_("Error"), _("You cannot start clipping audio as you have an error in your setup.")
                                  + "\n\n" + _("Check the messages for a more detailed error log."))
        else:
            if not self.is_recording:
                self.start_clip_time = self.get_duration(self.clipped_in_filename) - self.pre_buffer
                self.is_recording = True
            else:
                self.end_clip_time = self.get_duration(self.clipped_in_filename) + self.post_buffer

                export_thread = Thread(target=self.export_clip, args=(self.start_clip_time, self.end_clip_time,
                                                                      self.clipped_in_filename, self.out_filename))
                export_thread.daemon = True
                export_thread.start()

                self.is_recording = False
                self.start_clip_time = 0
                self.end_clip_time = 0

        self.update_status()

    def update_use_with_recorder(self, recording_file_name, is_recording):
        if self.use_recorder and not is_recording:
            # Will cause file not to be found and disallow clipping
            self.clipped_in_filename = ""
        elif self.use_recorder and is_recording:
            # Use "clipped_in_filename" as it can be set when using with recorder
            self.clipped_in_filename = recording_file_name
        else:
            self.clipped_in_filename = self.in_filename

    def update_status(self):
        self.messages = ""
        test_in_file = Path(self.in_filename)
        test_rec_file = Path(self.clipped_in_filename)
        if not self.use_recorder and not test_in_file.is_file():
            self.status = STATUS_CODE_ERROR
            self.messages += _("Input file does not exist") + "\n"
        elif self.use_recorder and not test_rec_file.is_file():
            self.status = STATUS_CODE_ERROR
            self.messages += _("Recorder not started") + "\n"
        elif self.is_recording:
            self.messages += _("Recording Clip") + "\n"
            self.status = STATUS_CODE_RECORDING
        else:
            self.messages += _("Clipper Ready") + "\n"
            self.status = STATUS_CODE_READY
