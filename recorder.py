import sounddevice as sd
import soundfile as sf
import time
import datetime
import json

from queue import Queue
from threading import Thread
from pathlib import Path


STATUS_CODE_READY = 0
STATUS_CODE_WARNING = 1
STATUS_CODE_RECORDING = 2
STATUS_CODE_ERROR = 3

RECORDER_CONFIG_FILENAME = 'config_recorder.json'


class Recorder:
    def __init__(self):
        self.is_recording = False
        self.out_filename_template = _("Recording-%d%m%Y-%H%M%S.wav")
        self.status = STATUS_CODE_ERROR
        self.messages = ""
        self.current_recording_filename = ""

        self.record_thread = None
        self.file_written = False

        self.device = 0
        self.channels = 0
        self.subtype = None
        self.split_after = 2 ** 63

        self.queue = Queue()
        self.get_recording_devices()

    def start_stop_record(self, ui):
        self.update_status()

        if self.status == STATUS_CODE_ERROR:
            ui.show_error_message(_("Error"), _("You cannot start clipping audio as you have an error in your setup.")
                                  + "\n\n" + _("Check the messages for a more detailed error log."))
        else:
            if not self.is_recording:
                self.record_thread = Thread(target=self.record, args=(self.get_out_filename(), self.device))
                self.record_thread.start()
                self.is_recording = True
            else:
                self.is_recording = False
                self.record_thread.join()

        self.update_status()

    def callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, flush=True)
        self.queue.put(indata.copy())

    def record(self, filename, device):
        self.samplerate = int(sd.query_devices(device, 'input')['default_samplerate'])
        self.channels = int(sd.query_devices(device, 'input')['max_input_channels'])

        with sd.InputStream(samplerate=self.samplerate, device=device,
                            channels=self.channels, callback=self.callback):
            counter = 0
            start_time = time.time()

            with sf.SoundFile(filename, mode='x', samplerate=self.samplerate,
                              channels=self.channels, subtype=self.subtype) as file:
                self.current_recording_filename = filename
                print(_("Recording to: ") + repr(filename))
                while self.is_recording:
                    if time.time() - start_time > self.split_after:
                        start_time += self.split_after
                        counter += 1
                        break
                    file.write(self.queue.get())
                    self.file_written = True

    def get_out_filename(self):
        return datetime.datetime.today().strftime(self.out_filename_template)

    def update_status(self):
        self.messages = ""
        test_out_file = Path(self.get_out_filename())
        if test_out_file.is_file() and not self.is_recording:
            self.status = STATUS_CODE_ERROR
            self.messages += _("Output file name already exists") + "\n"
        elif self.is_recording:
            self.messages += _("Recording") + "\n"
            self.status = STATUS_CODE_RECORDING
        else:
            self.messages += _("Recorder Ready") + "\n"
            self.status = STATUS_CODE_READY

    def write_config(self):
        config = {"out_filename_template": self.out_filename_template, "recording_device": self.device}
        with open(RECORDER_CONFIG_FILENAME, 'w') as outfile:
            json.dump(config, outfile)

    def read_config(self):
        try:
            with open(RECORDER_CONFIG_FILENAME) as json_data_file:
                data = json.load(json_data_file)
                self.out_filename_template = data["out_filename_template"]
                self.device = data["recording_device"]
        except FileNotFoundError:
            self.out_filename_template = _("Recording-%d%m%Y-%H%M%S.wav")
            self.device = 0

            self.write_config()

            print(_("Recorder config not found - using default"))

    @staticmethod
    def get_recording_devices():
        return sd.query_devices()
