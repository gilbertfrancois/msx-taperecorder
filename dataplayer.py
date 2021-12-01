import threading
import logging
import os

import sounddevice as sd
import soundfile as sf
import numpy as np  # Make sure NumPy is loaded before it is used in the callback
import time
assert np           # avoid "imported but unused" message (W0611)

current_frame = 0

class DataPlayer(threading.Thread):
    def __init__(self, device: int, filename: str, logger):
        super().__init__()
        if not os.path.exists(filename):
            raise FileNotFoundError(f"{filename} does not exist.")
        self.filename = filename
        self.device = device
        self.is_running = False
        self.data = np.empty(shape=(0, 2))
        if logger is not None:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)

    def __del__(self):
        self.stop()

    def start(self):
        self.is_running = True
        super().start()

    def stop(self):
        self.is_running = False
        if self.is_alive():
            self.join()

    def run(self):
        global current_frame
        current_frame = 0
        self.data, fs = sf.read(self.filename, always_2d=True, dtype="float32")
        try:
            # Set blocksize to a large value for Raspberry Pi, to prevent 
            with sd.OutputStream(samplerate=fs, device=self.device, channels=self.data.shape[1], blocksize=4096,
                    callback=self.callback, finished_callback=self.finished_callback):
                while self.is_running:
                    time.sleep(0.1)
        except sd.PortAudioError as e:
            self.logger.error(f"{e}")
        self.is_running = False

    def callback(self, outdata, frames, time, status):
        global current_frame
        print(outdata.shape, frames, time, status)
        if status:
            self.logger.info(status)
        chunksize = min(len(self.data) - current_frame, frames)
        outdata[:chunksize] = self.data[current_frame:current_frame + chunksize]
        if chunksize < frames:
            outdata[chunksize:] = 0
            raise sd.CallbackStop()
        current_frame += chunksize

    def finished_callback(self):
        self.is_running = False

