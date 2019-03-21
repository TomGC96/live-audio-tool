from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5 import uic
import gettext
import json
import yaml

clipper_ui_file = 'ui_designs/LiveAudioTool.ui'
clipper_icon = 'live-audio-tool-icon.svg'
form, base = uic.loadUiType(clipper_ui_file)

gettext.translation(domain='LiveAudioTool', localedir='locale', languages=['en']).install()

# Status codes with text for each

STATUS_CODE_READY = 0
STATUS_CODE_WARNING = 1
STATUS_CODE_RECORDING = 2
STATUS_CODE_ERROR = 3

LAT_CONFIG_FILENAME = 'config_lat.json'
AVAILABLE_LANGUAGE_FILE = 'locale/available-languages.yaml'

class UI(base, form):
    def __init__(self, clpr, recr):
        super().__init__()
        self.setupUi(self)

        # Set Default Language
        self.language = 'en'

        # Read LAT config file
        self.read_config()

        # Hide settings box before setting labels
        self.SettingsBox.hide()

        # Read languages from file and set according to settings
        self.LanguageComboBox.clear()
        for key, lang in self.available_languages.items():
            self.LanguageComboBox.addItem(lang['native-name'], lang['language-code'])
        index = self.LanguageComboBox.findData(self.language)
        if index != -1:
            self.LanguageComboBox.setCurrentIndex(index)

        self.LanguageComboBox.activated.connect(lambda: self.select_language(clpr, recr))
        gettext.translation(domain='LiveAudioTool', localedir='locale', languages=[self.language]).install()

        # Strings used to represent statuses
        self.status_ready_string = _("Ready")
        self.status_warning_string = _("Warning")
        self.status_recording_string = _("Recording")
        self.status_error_string = _("Error")

        self.setWindowIcon(QIcon(clipper_icon))
        self.set_ui_labels(clpr, recr)

        self.ShowHideSettingsButton.clicked.connect(self.show_hide_settings)

        ''' --- Recorder - Assign handlers --- '''

        self.RecStartStop.clicked.connect(lambda: self.rec_start_stop_clip_click(recr, clpr))

        self.RecSetFilename.clicked.connect(lambda: self.rec_output_file_button_click(recr))
        self.RecDeviceCombo.activated.connect(lambda: self.rec_change_device_combo(recr))

        self.RecResetDefaultButton.clicked.connect(lambda: self.rec_set_default_click(recr))
        self.RecMessagesButton.clicked.connect(lambda: self.rec_messages_click(recr))
        self.RecHelpButton.clicked.connect(self.rec_help_click)

        # Load recording devices to combo box
        device_index = 0
        for device in recr.get_recording_devices():
            if device['max_input_channels'] > 0:
                self.RecDeviceCombo.addItem(device['name'], device_index)
            # Increment actual device index
            device_index += 1

        # Read help text from file
        try:
            recorder_help_file = open('help_recorder.lat', 'r')
            self.REC_HELP_TEXT = recorder_help_file.read()
            recorder_help_file.close()
        except FileNotFoundError:
            self.REC_HELP_TEXT = _("ERROR: RECORDER HELP FILE NOT FOUND")
            print(self.REC_HELP_TEXT)

        self.rec_update_ui(recr)

        ''' --- Clipper - Assign handlers --- '''
        self.ClipStartStop.clicked.connect(lambda: self.clip_start_stop_clip_click(clpr, recr))

        self.ClipRecordingFileButton.clicked.connect(lambda: self.clip_recording_file_button_click(clpr))
        self.ClipUseRecorderCheck.stateChanged.connect(lambda: self.clip_use_recorder_check(clpr, recr))
        self.ClipOutputFileButton.clicked.connect(lambda: self.clip_output_file_button_click(clpr))
        self.ClipPreBufferSpin.valueChanged.connect(lambda: self.clip_pre_buffer_spin_edit(clpr))
        self.ClipPostBufferSpin.valueChanged.connect(lambda: self.clip_post_buffer_spin_edit(clpr))

        self.ClipResetDefaultButton.clicked.connect(lambda: self.clip_set_default_click(clpr))
        self.ClipMessagesButton.clicked.connect(lambda: self.clip_messages_click(clpr))
        self.ClipHelpButton.clicked.connect(self.clip_help_click)

        # Read help text from file
        try:
            clipper_help_file = open('help_clipper.lat', 'r')
            self.CLIP_HELP_TEXT = clipper_help_file.read()
            clipper_help_file.close()
        except FileNotFoundError:
            self.CLIP_HELP_TEXT = _("ERROR: CLIPPER HELP FILE NOT FOUND")
            print(self.CLIP_HELP_TEXT)

        self.clip_update_ui(clpr)

    ''' --- Recorder Methods --- '''

    def rec_start_stop_clip_click(self, recr, clpr):
        recr.file_written = False
        if recr.status != STATUS_CODE_RECORDING:
            recr.start_stop_record(self)
            self.RecStartStop.setText(_("Stop Recording"))
            # Wait for file to be written to disk (ensures status checks will show file exists)
            while not recr.file_written:
                pass
        else:
            default_msg = _("Are you sure you want to stop the recording?")
            reply = QMessageBox.question(self, _('Are you sure?'), default_msg, QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.Yes:
                recr.start_stop_record(self)
                self.RecStartStop.setText(_("Start Recording"))
        self.rec_set_status(recr.status)
        self.clip_update_ui_clipper(clpr, recr)

    def rec_output_file_button_click(self, recr):
        options = QFileDialog.Options()
        filename, _x = QFileDialog().getSaveFileName(None, _("Enter Output Filename"), recr.out_filename_template,
                                                     "WAV (*.wav)", options=options)
        if filename != "":
            recr.out_filename_template = filename
            recr.write_config()
            self.rec_update_ui(recr)

    def rec_change_device_combo(self, recr):
        recr.device = self.RecDeviceCombo.currentData()
        recr.write_config()

    def rec_set_default_click(self, recr):
        default_msg = _("Are you sure you want to reset settings to default?")
        reply = QMessageBox.question(self, _('Are you sure?'), default_msg, QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            recr.out_filename_template = _("Recording-%d%m%Y-%H%M%S.wav")
            recr.device = 0
            recr.write_config()
            self.rec_update_ui(recr)

    def rec_messages_click(self, recr):
        recr.update_status()
        self.show_error_message(_("Messages"), recr.messages)

    def rec_help_click(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(_("Recorder - Help"))
        msg.setWindowTitle(_("Recorder - Help"))
        msg.setDetailedText(self.REC_HELP_TEXT)
        msg.setStandardButtons(QMessageBox.Close)
        msg.exec()

    def rec_update_ui(self, recr):
        self.RecOutputFileLab.setText(recr.out_filename_template)
        self.RecDeviceCombo.setCurrentIndex(self.RecDeviceCombo.findData(recr.device))
        self.rec_set_status(recr.status)
        recr.update_status()

    def rec_set_status(self, status):
        if status == STATUS_CODE_READY:
            self.RecStatusLabel.setStyleSheet("background: green")
            self.RecStatusLabel.setText(self.status_ready_string)
        elif status == STATUS_CODE_WARNING:
            self.RecStatusLabel.setStyleSheet("background: yellow")
            self.RecStatusLabel.setText(self.status_warning_string)
        elif status == STATUS_CODE_RECORDING:
            self.RecStatusLabel.setStyleSheet("background: red")
            self.RecStatusLabel.setText(self.status_recording_string)
        elif status == STATUS_CODE_ERROR:
            self.RecStatusLabel.setStyleSheet("background: orange")
            self.RecStatusLabel.setText(self.status_error_string)
        else:
            self.RecStatusLabel.setStyleSheet("background: red")
            self.RecStatusLabel.setText(_("Internal Error"))

    ''' --- Clipper Methods --- '''

    def clip_start_stop_clip_click(self, clpr, recr):
        clpr.start_stop_clip(self)
        self.clip_update_ui_clipper(clpr, recr)
        self.clip_set_status(clpr.status)
        if clpr.status == STATUS_CODE_RECORDING:
            self.ClipStartStop.setText(_("Stop Clip"))
        else:
            self.ClipStartStop.setText(_("Start Clip"))

    def clip_recording_file_button_click(self, clpr):
        options = QFileDialog.Options()
        filename, _x = QFileDialog().getOpenFileName(None, _("Select Recording File"), clpr.in_filename,
                                                     "Audio Files (*.wav *.mp3 *.flac *.ogg *.mp4)", options=options)
        if filename != "":
            clpr.in_filename = filename
            clpr.write_config()
            self.clip_update_ui(clpr)

    def clip_use_recorder_check(self, clpr, recr):
        clpr.use_recorder = self.ClipUseRecorderCheck.isChecked()
        clpr.write_config()
        self.clip_update_ui_clipper(clpr, recr)

    def clip_output_file_button_click(self, clpr):
        options = QFileDialog.Options()
        filename, _x = QFileDialog().getSaveFileName(None, _("Enter Output Filename"), clpr.out_filename,
                                                     "WAV (*.wav);;MP3 (*.mp3);;FLAC (*.flac)", options=options)
        if filename != "":
            clpr.out_filename = filename
            clpr.write_config()
            self.clip_update_ui(clpr)

    def clip_pre_buffer_spin_edit(self, clpr):
        clpr.pre_buffer = self.ClipPreBufferSpin.value()
        clpr.write_config()

    def clip_post_buffer_spin_edit(self, clpr):
        clpr.post_buffer = self.ClipPostBufferSpin.value()
        clpr.write_config()

    def clip_set_default_click(self, clpr):
        default_msg = _("Are you sure you want to reset settings to default?")
        reply = QMessageBox.question(self, _('Are you sure?'), default_msg, QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            clpr.in_filename = _("SelectInputRecording.wav")
            clpr.out_filename = _("AudioClip-%d%m%Y-%H%M%S.mp3")
            clpr.pre_buffer = 30
            clpr.post_buffer = 5
            clpr.write_config()
            self.clip_update_ui(clpr)

    def clip_messages_click(self, clpr):
        clpr.update_status()
        self.show_error_message(_("Messages"), clpr.messages)

    def clip_help_click(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(_("Clipper - Help"))
        msg.setWindowTitle(_("Clipper - Help"))
        msg.setDetailedText(self.CLIP_HELP_TEXT)
        msg.setStandardButtons(QMessageBox.Close)
        msg.exec()

    def clip_update_ui(self, clpr):
        self.ClipRecordingFileLab.setText(clpr.in_filename)
        self.ClipUseRecorderCheck.setChecked(clpr.use_recorder)
        self.ClipRecordingFileButton.setEnabled(not clpr.use_recorder)
        self.ClipRecordingFileLab.setEnabled(not clpr.use_recorder)

        if clpr.use_recorder:
            self.ClipRecordingFileLab.setText(_("Using Recorder File"))
        clpr.update_use_with_recorder("", False)

        self.ClipOutputFileLab.setText(clpr.out_filename)
        self.ClipPreBufferSpin.setValue(clpr.pre_buffer)
        self.ClipPostBufferSpin.setValue(clpr.post_buffer)

        clpr.update_status()
        self.clip_set_status(clpr.status)

    def clip_update_ui_clipper(self, clpr, recr):
        self.clip_update_ui(clpr)

        clpr.update_use_with_recorder(recr.current_recording_filename, recr.is_recording)

        clpr.update_status()
        self.clip_set_status(clpr.status)

    def clip_set_status(self, status):
        if status == STATUS_CODE_READY:
            self.ClipStatusLabel.setStyleSheet("background: green")
            self.ClipStatusLabel.setText(self.status_ready_string)
        elif status == STATUS_CODE_WARNING:
            self.ClipStatusLabel.setStyleSheet("background: yellow")
            self.ClipStatusLabel.setText(self.status_warning_string)
        elif status == STATUS_CODE_RECORDING:
            self.ClipStatusLabel.setStyleSheet("background: red")
            self.ClipStatusLabel.setText(self.status_recording_string)
        elif status == STATUS_CODE_ERROR:
            self.ClipStatusLabel.setStyleSheet("background: orange")
            self.ClipStatusLabel.setText(self.status_error_string)
        else:
            self.ClipStatusLabel.setStyleSheet("background: red")
            self.ClipStatusLabel.setText(_("Internal Error"))

    ''' --- Generic Methods --- '''

    def closeEvent(self, event):
        reply = QMessageBox.question(self, _('Quit'), _('Are you sure you want to quit? This will stop any recording '
                                                        'in progress.'), buttons=QMessageBox.No | QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def show_error_message(self, title, message):
        QMessageBox.about(self, title, message)

    def show_hide_settings(self):
        # Show and hide settings container
        self.SettingsBox.setHidden(not self.SettingsBox.isHidden())
        if not self.isFullScreen():
            # Resize window as settings shown and hidden
            height = self.height()
            if self.SettingsBox.isHidden():
                height -= self.SettingsBox.height() + self.SettingsBox.layout().getContentsMargins()[1]
                self.ShowHideSettingsButton.setText(_("Show Settings"))
            else:
                height += self.SettingsBox.height() + self.SettingsBox.layout().getContentsMargins()[1]
                self.ShowHideSettingsButton.setText(_("Hide Settings"))
            self.resize(self.width(), height)

    def select_language(self, clpr, recr):
        self.language = self.LanguageComboBox.currentData()
        gettext.translation(domain='LiveAudioTool', localedir='locale', languages=[self.language]).install()

        self.status_ready_string = _("Ready")
        self.status_warning_string = _("Warning")
        self.status_recording_string = _("Recording")
        self.status_error_string = _("Error")

        self.set_ui_labels(clpr, recr)
        self.write_config()

    def read_config(self):
        try:
            with open(LAT_CONFIG_FILENAME) as json_data_file:
                data = json.load(json_data_file)
                self.language = data["language"]
        except FileNotFoundError:
            self.language = 'en'
            self.write_config()
            print(_("Live Audio Tool config not found - using default"))

        try:
            langs_file = open(AVAILABLE_LANGUAGE_FILE, "r")
            self.available_languages = yaml.safe_load(langs_file)
        except FileNotFoundError:
            print(_("`Available Languages` file not found"))
            self.available_languages = {'english': {'native-name': 'English',
                                                    'english-name': 'English',
                                                    'language-code': 'en'}}

    def write_config(self):
        config = {"language": self.language}
        with open(LAT_CONFIG_FILENAME, 'w') as outfile:
            json.dump(config, outfile)

    def set_ui_labels(self, clpr, recr):
        self.RecTitleLabel.setText(_("Recorder"))
        if recr.status == STATUS_CODE_RECORDING:
            self.RecStartStop.setText(_("Stop Recording"))
        else:
            self.RecStartStop.setText(_("Start Recording"))
        self.RecOutputFileLab.setText(recr.out_filename_template)
        self.RecSetFilename.setText(_("Set Recording Filename"))
        self.RecDeviceLab.setText(_("Recording Device"))
        self.RecResetDefaultButton.setText(_("Reset To Default"))
        self.RecMessagesButton.setText(_("Messages"))
        self.RecHelpButton.setText(_("Help"))
        self.rec_set_status(recr.status)

        self.ClipTitleLabel.setText(_("Clipper"))
        if clpr.status == STATUS_CODE_RECORDING:
            self.ClipStartStop.setText(_("Stop Clip"))
        else:
            self.ClipStartStop.setText(_("Start Clip"))
        self.ClipRecordingFileLab.setText(clpr.in_filename)
        self.ClipUseRecorderCheck.setText(_("Use Recorder"))
        self.ClipRecordingFileButton.setText(_("Select Recording File"))
        self.ClipOutputFileLab.setText(clpr.out_filename)
        self.ClipOutputFileButton.setText(_("Select Output Filename"))
        self.ClipPreBufferLab.setText(_("Pre Buffer (Seconds)"))
        self.ClipPostBufferLab.setText(_("Post Buffer (Seconds)"))
        self.ClipResetDefaultButton.setText(_("Reset To Default"))
        self.ClipMessagesButton.setText(_("Messages"))
        self.ClipHelpButton.setText(_("Help"))
        self.clip_set_status(clpr.status)

        if self.SettingsBox.isHidden():
            self.ShowHideSettingsButton.setText(_("Show Settings"))
        else:
            self.ShowHideSettingsButton.setText(_("Hide Settings"))
        self.LanguageLabel.setText(_("Language:"))
