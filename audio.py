import threading
import tempfile
import sys
import logging
from typing import Optional

import sounddevice as sd
import soundfile as sf
import numpy as np  # Make sure NumPy is loaded before it is used in the callback
assert np           # avoid "imported but unused" message (W0611)
from queue import Queue

log = logging.getLogger(__name__)

q = Queue()

def callback(indata: np.ndarray, frames: int, time, status: sd.CallbackFlags) -> None:
    """ This is called (from a separate thread) for each audio block.

    """
    if status:
        log.info(status, file=sys.stderr)
    q.put(indata.copy())


class DataRecorder(threading.Thread):
    def __init__(self, device: int, samplerate: Optional[int], n_channels: int, filename: Optional[str]):
        super().__init__()
        self.is_running = False
        self.device = device
        self.samplerate = samplerate
        self.n_channels = n_channels
        self.filename = filename
        self.subtype = "PCM_24"

    def start(self):
        log.info(f"Start recording.")
        self.is_running = True
        super().start()

    def stop(self):
        log.info(f"Stop recording.")
        self.is_running = False
        
    def run(self):
        if self.samplerate is None:
            self.get_default_samplerate()
        if self.filename is None:
            self.filename = tempfile.mktemp(prefix='delete_me_', suffix='.wav', dir='')

        with sf.SoundFile(self.filename, mode='x', samplerate=self.samplerate, channels=self.n_channels, subtype=self.subtype) as file:
            with sd.InputStream(samplerate=self.samplerate, device=self.device, channels=self.n_channels, callback=callback):
                log.info(f"Using filename {self.filename}.")
                while self.is_running:
                    file.write(q.get())


    def query_devices(self):
        log.info(sd.query_devices())
        log.info(sd.query_devices(0, kind="input"))

    def get_default_samplerate(self):
        device_info = sd.query_devices(self.device, "input")
        self.samplerate = device_info.get("default_samplerate")
        if self.samplerate is not None:
            self.samplerate = int(self.samplerate)
        else:
            raise RuntimeError(f"Could not determine sample rate from device {self.device}.")
