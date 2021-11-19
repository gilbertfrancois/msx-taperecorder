import threading

class DataRecorder(threading.Thread):
    def __init__(self):
        super().__init__()
        self.is_running = False

    def start(self):
        self.is_running = True

    def stop(self):
        self.is_running = False
        

    def run(self):
        while self.is_running:
            pass
