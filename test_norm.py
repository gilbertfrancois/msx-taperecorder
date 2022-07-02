import soundfile as sf
import numpy as np
import os

import matplotlib.pyplot as plt

import pdb; pdb.set_trace()

filename = "assets/rec/hello3.wav"
data1, samplerate = sf.read(filename, always_2d=True, dtype="float32")
print(np.min(data1), np.max(data1), np.mean(data1), np.std(data1))

data_min = np.min(data1)
data_mu = np.mean(data1)
data_max = np.max(data1)

h_amp = min(abs(data_mu - data_min), abs(data_max - data_mu))
h_amp = np.std(data1)*1.58979
factor = 0.50 / h_amp
data11 = data1 * factor

print(f"{np.min(data11):0.3f}", np.max(data11), np.mean(data11), np.std(data11))

if os.path.exists("assets/rec/hello3n.wav"):
    os.remove("assets/rec/hello3n.wav")

sf.write("assets/rec/hello3n.wav", data11, samplerate, subtype="PCM_24")

fig, axs = plt.subplots(1, 2, figsize=(12, 6))
axs[0].plot(data1)
axs[1].plot(data11)
axs[0].set_ylim([-1,1])
axs[1].set_ylim([-1,1])
plt.show()

