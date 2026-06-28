"""
signal_processor.py
-------------------
Extracts 12 FFT features from raw MPU6050 sensor data.
4 features per axis (Ax, Ay, Az) = 12 total.
This matches exactly what morpholock_model.pkl was trained on.

CRITICAL: Do not change SAMPLE_RATE or WINDOW_SIZE.
"""

import numpy as np
import logging

logger = logging.getLogger(__name__)

SAMPLE_RATE  = 100
WINDOW_SIZE  = 200
TREMOR_LOW   = 8.0
TREMOR_HIGH  = 12.0


def _extract_axis_features(signal: np.ndarray,
                            sample_rate: int = 100) -> np.ndarray:
    """
    Extracts 4 FFT features from a single axis signal.
    Returns: [tremor_power, peak_freq, total_power, low_power]
    """
    n        = len(signal)
    freqs    = np.fft.rfftfreq(n, d=1.0 / sample_rate)
    fft_vals = np.abs(np.fft.rfft(signal))

    band     = (freqs >= TREMOR_LOW)  & (freqs <= TREMOR_HIGH)
    low_band = (freqs >= 0.1)         & (freqs <= 4.0)

    # Feature 1 — power in 8-12Hz biological tremor band
    tremor_power = float(np.sum(fft_vals[band] ** 2))

    # Feature 2 — dominant frequency within the tremor band
    if np.any(band) and np.any(fft_vals[band]):
        peak_freq = float(freqs[band][np.argmax(fft_vals[band])])
    else:
        peak_freq = 0.0

    # Feature 3 — total spectral power across all frequencies
    total_power = float(np.sum(fft_vals ** 2))

    # Feature 4 — low frequency macro-movement power (0.1-4Hz)
    low_power = float(np.sum(fft_vals[low_band] ** 2))

    return np.array([tremor_power, peak_freq, total_power, low_power])


def extract_features(window, sample_rate: int = 100) -> np.ndarray:
    """
    Takes 200 rows of [Ax, Ay, Az, Gx, Gy, Gz].
    Extracts 4 features per axis for Ax, Ay, Az = 12 features total.
    This matches morpholock_model.pkl exactly.

    Returns: numpy array of shape (12,)
    Returns None if data is insufficient.
    """
    if window is None or len(window) < 10:
        logger.warning("Insufficient data for feature extraction")
        return None

    n    = min(len(window), WINDOW_SIZE)
    data = np.array(window[:n])

    # Extract each axis separately
    Ax = data[:, 0]
    Ay = data[:, 1]
    Az = data[:, 2]

    # 4 features per axis × 3 axes = 12 features
    feat_ax = _extract_axis_features(Ax, sample_rate)
    feat_ay = _extract_axis_features(Ay, sample_rate)
    feat_az = _extract_axis_features(Az, sample_rate)

    features = np.concatenate([feat_ax, feat_ay, feat_az])

    logger.debug(f"Features shape: {features.shape} — "
                 f"Ax tremor: {feat_ax[0]:.4f}, "
                 f"Ay tremor: {feat_ay[0]:.4f}, "
                 f"Az tremor: {feat_az[0]:.4f}")
    return features


if __name__ == "__main__":
    print("Testing signal_processor.py — 12 features...\n")

    # Simulate human hand tremor
    t = np.linspace(0, 2, 200)
    fake_human = [
        [
            0.08 * np.sin(2*np.pi*10*t[i]) + 0.01*np.random.randn(),
            0.06 * np.sin(2*np.pi*9.5*t[i]) + 0.01*np.random.randn(),
            0.98 + 0.04 * np.sin(2*np.pi*10.5*t[i]),
            1.1, -0.3, 0.1
        ]
        for i in range(200)
    ]

    # Simulate flat device
    fake_flat = [[0.001, 0.001, 0.001, 0.001, 0.001, 0.001]
                 for _ in range(200)]

    f1 = extract_features(fake_human)
    f2 = extract_features(fake_flat)

    print(f"Features shape: {f1.shape}  ← must be (12,)")
    print(f"Human features : {f1}")
    print(f"Flat features  : {f2}")
    print(f"\nAx tremor — Human: {f1[0]:.4f}  Flat: {f2[0]:.6f}")
    print(f"Ay tremor — Human: {f1[4]:.4f}  Flat: {f2[4]:.6f}")
    print(f"Az tremor — Human: {f1[8]:.4f}  Flat: {f2[8]:.6f}")
    print("\nHuman values should be significantly higher than flat.")
    print("\nTest complete.")