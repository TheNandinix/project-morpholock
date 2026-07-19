import serial
import numpy as np
import time

ser = serial.Serial('COM4', 115200, timeout=3)
time.sleep(2)
ser.reset_input_buffer()

print("Collecting 200 readings... hold sensor naturally")

data = []
while len(data) < 200:
    try:
        line = ser.readline().decode(errors='ignore').strip()
        if not line or line.startswith("READY") or line.startswith("TOKEN"):
            continue
        parts = line.split(",")
        if len(parts) == 6:
            data.append([float(x) for x in parts])
    except:
        pass

ser.close()
raw_signals = np.array(data)

# ── Check 1: Stale Data ──
print("\n── Check 1: Variance (Stale Data Test) ──")
print(np.var(raw_signals))
print("If same number every time → serial is frozen")

# ── Check 2: Gravity Trap ──
print("\n── Check 2: Z-axis Mean (Gravity Trap Test) ──")
print(np.mean(raw_signals[:, 2]))
print("If ~1.0 → gravity DC offset present, FFT will be crushed")

# ── Check 3: Physical Energy ──
print("\n── Check 3: RMS Energy (Flat vs Hand Test) ──")
ac_signals = raw_signals - np.mean(raw_signals, axis=0)
print("Energy:", np.sqrt(np.mean(ac_signals**2)))
print("Near-zero when flat = model cannot distinguish flat table from hand")