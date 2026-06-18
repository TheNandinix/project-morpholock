import numpy as np
from scipy.fftpack import fft, fftfreq
import logging

logger = logging.getLogger(__name__)

SAMPLE_RATE = 100  # Do not change
WINDOW_SIZE = 200  # Do not change
TREMOR_LOW = 8.0   # Hz
TREMOR_HIGH = 12.0 # Hz

def extract_features(window, sample_rate=100):
    n = min(len(window), WINDOW_SIZE)
    data = np.array(window[:n])

    mag = np.sqrt(data[:,0]**2 + data[:,1]**2 + data[:,2]**2)
    freqs = fftfreq(n, d=1.0/sample_rate)
    fft_vals = np.abs(fft(mag))

    band = (freqs>=TREMOR_LOW)&(freqs<=TREMOR_HIGH)
    t_power = np.sum(fft_vals[band]**2)
    peak_f = freqs[band][np.argmax(fft_vals[band])] if np.any(band) else 0.0

    total_p = np.sum(fft_vals**2)

    low_band = (freqs>=0.1)&(freqs<=4.0)
    low_p = np.sum(fft_vals[low_band]**2)

    return np.array([t_power, peak_f, total_p, low_p])


if __name__ == '__main__':
    fake = [[0.01,0.98,0.02,1.1,-0.3,0.1]] * 200
    feat = extract_features(fake)
    print('Features:', feat)
    print('Shape:', feat.shape)