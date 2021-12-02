import threading
import logging
import os

import sounddevice as sd
import soundfile as sf
import numpy as np  # Make sure NumPy is loaded before it is used in the callback
assert np           # avoid "imported but unused" message (W0611)

class DataPlayer(threading.Thread):
    def __init__(self, device: int, filename: str, logger):
        super().__init__()
        if not os.path.exists(filename):
            raise FileNotFoundError(f"{filename} does not exist.")
        self.filename = filename
        self.device = device
        self.blocksize = 4096
        self.data = np.empty(shape=(0, 2))
        self.current_frame = 0
        self.progress = 0
        self.event = threading.Event()
        if logger is not None:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)

    def __del__(self):
        self.stop()

    def start(self):
        super().start()

    def stop(self):
        self.event.set()
        if self.is_alive():
            self.join()

    def run(self):
        self.current_frame = 0
        self.data, samplerate = sf.read(self.filename, always_2d=True, dtype="float32")
        logmsg = f"DataPlayer: filename: {self.filename}, channels: {self.data.shape[1]}, samplerate: {samplerate}, "
        logmsg += f"data len: {len(self.data)}"
        self.logger.info(logmsg)
        try:
            with sd.OutputStream(samplerate=samplerate, 
                                 device=self.device, 
                                 channels=self.data.shape[1],
                                 blocksize=self.blocksize,
                                 callback=self.callback, 
                                 finished_callback=self.finished_callback):
                self.event.wait()
        except sd.PortAudioError as e:
            self.logger.error(f"{e}")

    def callback(self, outdata, frames, time, status):
        self.progress = int(100*(self.current_frame / len(self.data))) + 1
        if status.output_underflow:
            self.logger.warning("Output underflow. Try increasing the blocksize.")
        chunksize = min(len(self.data) - self.current_frame, frames)
        outdata[:chunksize] = self.data[self.current_frame:self.current_frame + chunksize]
        if chunksize < frames:
            outdata[chunksize:] = 0
            raise sd.CallbackStop()
        self.current_frame += chunksize

    def finished_callback(self):
        self.event.set()

