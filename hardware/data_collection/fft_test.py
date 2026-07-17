import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq

# ==========================
# Load Data
# ==========================
df = pd.read_csv("tremor.csv")

# ==========================
# Combine 3 Axes
# ==========================
signal = np.sqrt(
    df["ax"]**2 +
    df["ay"]**2 +
    df["az"]**2
)

# Remove DC component
signal = signal - np.mean(signal)

# ==========================
# Sampling Rate
# ==========================
fs = 138   # Your measured sample rate

# ==========================
# FFT
# ==========================
N = len(signal)

yf = fft(signal)
xf = fftfreq(N, 1/fs)

# Positive frequencies only
mask = xf > 0

freqs = xf[mask]
magnitudes = np.abs(yf[mask])

# ==========================
# Find Dominant Frequency
# ==========================
peak_index = np.argmax(magnitudes)

print(
    f"Dominant Frequency: "
    f"{freqs[peak_index]:.2f} Hz"
)

# ==========================
# Plot FFT
# ==========================
plt.figure(figsize=(12,6))

plt.plot(freqs, magnitudes)

plt.xlim(0,30)

plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude")
plt.title("MorphoLock Tremor Spectrum")
plt.axvspan(
    8,
    12,
    alpha=0.2
)
plt.grid(True)

plt.show()