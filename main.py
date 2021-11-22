import gf_logging
gf_logging.setup_logging()

import time
import gf_lib
from audio import DataRecorder


if __name__ == "__main__":
    # gf_lib.get_cas_filename("hellow.cas")
    dr = DataRecorder(0, None, 1, None)
    dr.query_devices()
    dr.start()
    time.sleep(5)
    dr.stop()

