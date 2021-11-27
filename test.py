import gf_logging
gf_logging.setup_logging()

import time
import gf_lib
from datarecorder import DataRecorder
from dataplayer import DataPlayer


if __name__ == "__main__":
    # gf_lib.get_cas_filename("hellow.cas")
    dr = DataRecorder(0, None, 1, None)
    dr.query_devices()
    dr.start()
    time.sleep(5)
    dr.stop()
    
    # dp = DataPlayer(device=1, filename="sample0.wav")
    # dp.start()
    # time.sleep(3)
    # dp.stop()
    # del dp
    # time.sleep(1)

#     dp = DataPlayer(device=1, filename="sample2.wav")
#     dp.start()
#     time.sleep(2)
#     dp.stop()
#     del dp
