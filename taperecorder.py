import logging
import time
import os
import shutil
from typing import Optional

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.logger import Logger
from kivy.config import Config
from kivy.clock import Clock

from datarecorder import DataRecorder
from dataplayer import DataPlayer
import sounddevice as sd

class MainWindow(Widget):

    def __init__(self):
        Logger.info(f"MainWindow: __init__()")
        super().__init__()
        self.input_device = 1
        self.output_device = 1
        self.set_2400 = False
        self.play_filepath:Optional[str] = None
        self.rec_filepath:Optional[str] = None
        self.is_playing = False
        self.is_recording = False
        self.dataplayer:Optional[DataPlayer] = None
        self.datarecorder:Optional[DataRecorder] = None
        self.query_devices()
        Logger.info(f"MainWindow: {os.path.realpath(__file__)}")
        self.app_folder = os.path.dirname(os.path.realpath(__file__))
        self.cas2wav = os.path.join(self.app_folder, "bin", "cas2wav")
        self.wav2cas = os.path.join(self.app_folder, "bin", "wav2cas")
        Clock.schedule_interval(self.ids.filechooser._update_files, 1.0)
        Clock.schedule_interval(self.check_dataplayer_status, 0.3)

    def __del__(self):
        Logger.info(f"MainWindow: __del__()")
        self.stop_dataplayer()
        self.stop_datarecorder()

    def selected(self, filepath_list):
        try:
            filename = os.path.basename(filepath_list[0])
            self.play_filepath = filepath_list[0]
            # self.ids.status_label.text = filename
            Logger.info(f"MainWindow: {filename}")
        except:
            pass

    def on_press_record(self):
        Logger.info(f"MainWindow: on_press_record()")
        time.sleep(0.2)
        self.stop_dataplayer()
        self.stop_datarecorder()
        self.rec_filepath = os.path.join(self.ids.filechooser.path, f"rec_{str(int(time.time()))}.wav")
        self.ids.button_rec.state = "down"
        self.datarecorder = DataRecorder(device=self.input_device, samplerate=None, n_channels=1, filename=self.rec_filepath)
        self.datarecorder.start()
        self.ids.filechooser._update_files()

    def on_press_record_(self):
        Logger.info(f"MainWindow: on_press_record()")
        self.rec_filepath = self.play_filepath
        if self.rec_filepath is None:
            return
        self.rename_to_msx_filename(self.rec_filepath)
        self.rec_filepath = None
        self.ids.filechooser._update_files()

    def on_press_play(self):
        Logger.info(f"MainWindow: on_press_play()")
        if self.play_filepath is None:
            self.ids.status_label.text = "No file selected."
            return
        self.convert_cas_to_wav(self.play_filepath)
        self.stop_dataplayer()
        self.stop_datarecorder()
        self.ids.button_play.state = "down"
        self.dataplayer = DataPlayer(device=self.output_device, filename=self.play_filepath, logger=Logger)
        self.dataplayer.start()

    def on_press_stop(self):
        Logger.info(f"MainWindow: on_press_stop()")
        self.stop_dataplayer()
        self.ids.button_play.state = "normal"
        self.stop_datarecorder()
        self.ids.button_rec.state = "normal"
        self.ids.filechooser._update_files()

    def stop_dataplayer(self):
        if self.dataplayer is not None:
            self.dataplayer.stop()
            self.dataplayer = None
    
    def stop_datarecorder(self):
        if self.datarecorder is not None:
            self.datarecorder.stop()
            self.datarecorder = None
            if self.rec_filepath is not None:
                self.rename_to_msx_filename(self.rec_filepath)
            self.rec_filepath = None
        self.ids.filechooser._update_files()

    def check_dataplayer_status(self, a):
        if self.dataplayer is not None and self.dataplayer.is_running:
            self.ids.button_play.state = "down"
        else:
            self.ids.button_play.state = "normal"



    def query_devices(self):
        Logger.info(f"DataRecorder: \nAll devices\n{sd.query_devices()}")

    def convert_cas_to_wav(self, cas_filepath):
        if cas_filepath is None:
            raise RuntimeError(f"File path is None.")
        src_filename = os.path.basename(cas_filepath)
        src_folder = os.path.dirname(cas_filepath)
        src_filename_noext, ext = os.path.splitext(src_filename)
        if ext == ".wav":
            # File is already a wav, ready for the msx to read.
            return cas_filepath
        elif ext == ".cas":
            # Convert cas to wav and return the new filepath
            wav_filepath = os.path.join(src_folder, f"{src_filename_noext}.wav")
            if self.set_2400:
                os.system(f"{self.cas2wav} -2 {cas_filepath} {wav_filepath}")
            else:
                os.system(f"{self.cas2wav} {cas_filepath} {wav_filepath}")
            Logger.info(f"MainWindow: Converted {cas_filepath} to {wav_filepath}.")
            return wav_filepath
        else:
            Logger.error(f"MainWindow: Unsupported file type. Expected wav or cas file, actual: {cas_filepath}.")
            raise RuntimeError("Unsupported file type.")

    def convert_wav_to_cas(self, wav_filepath):
        wav_filename = os.path.basename(wav_filepath)
        wav_folder = os.path.dirname(wav_filepath)
        wav_filename_noext, ext = os.path.splitext(wav_filename)
        if ext == ".cas":
            # Already a cas file, do nothing.
            return wav_filepath
        elif ext == ".wav":
            cas_filepath = os.path.join(wav_folder, f"{wav_filename_noext}.cas")
            os.system(f"{self.wav2cas} -p {wav_filepath} {cas_filepath}")
            Logger.info(f"MainWindow: Converted {wav_filepath} to {cas_filepath}.")
            return cas_filepath
        else:
            Logger.error(f"MainWindow: Unsupported file type. Expected wav or cas file, actual: {wav_filepath}.")
            raise RuntimeError("Unsupported file type.")

    def get_msx_filename_from_cas(self, cas_filepath):
        cas_header = b'\x1f\xa6\xde\xba\xcc\x13}t'
        data = None
        with open(cas_filepath, "rb") as fp:
            data = fp.read()
        if data is not None:
            idx = data.find(cas_header)
            if idx == -1:
                message = f"No CAS header found in {os.path.basename(cas_filepath)}"
                self.ids.status_label.text = message
                Logger.error(f"MainWindow: {message}.")
                return None
            else:
                msx_filename = None
                try:
                    msx_filename = data[idx+18:idx+24].decode("ascii")
                    msx_filename = msx_filename.strip()
                    if msx_filename == "":
                        msx_filename = None
                        Logger.info(f"MainWindow: msx filename is empty. Keeping tmp filename.")
                    else:
                        Logger.info(f"MainWindow: Found msx filename: {msx_filename}")
                except:
                    Logger.error(f"MainWindow: Invalid or unknown CAS format.")
                return msx_filename

    def rename_to_msx_filename(self, wav_filepath, delete_cas_file=True):
        folder = os.path.dirname(wav_filepath)
        cas_filepath = self.convert_wav_to_cas(wav_filepath)
        msx_filename = self.get_msx_filename_from_cas(cas_filepath)
        if msx_filename is None:
            if os.path.exists(cas_filepath):
                os.remove(cas_filepath)
            self.ids.filechooser._update_files()
            return wav_filepath
        msx_filepath = os.path.join(folder, f"{msx_filename}.wav")
        os.rename(wav_filepath, msx_filepath)
        Logger.info(f"MainWindow: Renamed: {wav_filepath} -> {msx_filepath}")
        if delete_cas_file:
            os.remove(cas_filepath)
        self.ids.filechooser._update_files()
        return msx_filepath

    def callback_dataplayer(self):
        self.stop_dataplayer()

class TapeRecorderApp(App):
    def build(self):
        # Window.clearcolor = (1.0, 1.0, 1.0, 1.0)
        return MainWindow()

if __name__ == "__main__":
    # Config.set('graphics', 'width', '800')
    # Config.set('graphics', 'height', '480')
    Config.set('graphics', 'fullscreen', 'auto')
    TapeRecorderApp().run()

