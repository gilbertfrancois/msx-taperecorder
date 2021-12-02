import threading
import tempfile
import logging
from typing import Optional

import sounddevice as sd
import soundfile as sf
import numpy as np  # Make sure NumPy is loaded before it is used in the callback
assert np           # avoid "imported but unused" message (W0611)
from queue import Queue


class DataRecorder(threading.Thread):
    def __init__(self, device: int, samplerate: Optional[int], n_channels: int, filename: Optional[str], logger=None):
        super().__init__()
        self.is_running = False
        self.device = device
        self.samplerate = samplerate
        self.n_channels = n_channels
        self.buffersize = 20
        self.blocksize = 2048
        self.filename = filename
        self.subtype = "PCM_24"
        self.q_rec = Queue(self.buffersize)
        if logger is not None:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)

    def __del__(self):
        self.stop()

    def start(self):
        self.logger.info(f"DataRecorder: Start recording.")
        self.is_running = True
        super().start()

    def stop(self):
        self.logger.info(f"DataRecorder: Stop recording.")
        self.is_running = False
        if self.is_alive():
            self.join()
        
    def run(self):
        if self.samplerate is None:
            self.get_default_samplerate()
        if self.filename is None:
            self.filename = tempfile.mktemp(prefix='delete_me_', suffix='.wav', dir='')

        with sf.SoundFile(self.filename, mode='x', samplerate=self.samplerate, channels=self.n_channels, subtype=self.subtype) as file:
            with sd.InputStream(samplerate=self.samplerate, blocksize=self.blocksize, device=self.device, callback=self.callback_rec):
                self.logger.info(f"DataRecorder: Using filename {self.filename}.")
                while self.is_running:
                    file.write(self.q_rec.get())

    def callback_rec(self, indata: np.ndarray, frames: int, time, status: sd.CallbackFlags) -> None:
        print(frames)
        if status:
            self.logger.warning(status)
        self.q_rec.put(indata.copy())

    def query_devices(self):
        self.logger.info(f"DataRecorder: \nAll devices\n{sd.query_devices()}")
        self.logger.info(f"DataRecorder: \nInput devices:\n{sd.query_devices(0, kind='input')}")

    def get_default_samplerate(self):
        device_info = sd.query_devices(self.device, "input")
        self.samplerate = device_info.get("default_samplerate")
        if self.samplerate is not None:
            self.samplerate = int(self.samplerate)
        else:
            raise RuntimeError(f"Could not determine sample rate from device {self.device}.")
