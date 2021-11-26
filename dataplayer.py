import threading
import logging

import sounddevice as sd
import soundfile as sf
import numpy as np  # Make sure NumPy is loaded before it is used in the callback
import time
assert np           # avoid "imported but unused" message (W0611)

log = logging.getLogger(__name__)
current_frame = 0

class DataPlayer(threading.Thread):
    def __init__(self, device: int, filename: str):
        super().__init__()
        self.filename = filename
        self.device = device
        self.is_running = False
        self.data = np.empty(shape=(0, 2))

    def start(self):
        self.is_running = True
        super().start()

    def stop(self):
        self.is_running = False

    def run(self):
        global current_frame
        current_frame = 0
        self.data, fs = sf.read(self.filename, always_2d=True, dtype="float32")
        with sd.OutputStream(samplerate=fs, device=self.device, channels=self.data.shape[1], callback=self.callback):

            while self.is_running:
                time.sleep(1.0)
                # log.info(".")
        self.is_running = False

    def callback(self, outdata, frames, time, status):
        global current_frame
        if status:
            log.info(status)
        chunksize = min(len(self.data) - current_frame, frames)
        outdata[:chunksize] = self.data[current_frame:current_frame + chunksize]
        if chunksize < frames:
            outdata[chunksize:] = 0
            raise sd.CallbackStop()
        current_frame += chunksize

