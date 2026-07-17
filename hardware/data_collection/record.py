import serial
import pandas as pd
import time
import os

ser = serial.Serial('COM4', 115200)
time.sleep(2)

TARGET_SAMPLES = 200
SAVE_FOLDER = "training_data"
os.makedirs(SAVE_FOLDER, exist_ok=True)

sample_num = int(input("Enter sample number (1-50): "))
filename = os.path.join(SAVE_FOLDER, f"sample_{sample_num:02d}.csv")

print("\nGet ready — hold the sensor naturally...")
print("3"); time.sleep(1)
print("2"); time.sleep(1)
print("1"); time.sleep(1)
print("Recording...")

ser.reset_input_buffer()
data = []

while len(data) < TARGET_SAMPLES:
    try:
        line = ser.readline().decode(errors='ignore').strip()
        
        # Skip status messages
        if not line or line.startswith("READY") or line.startswith("TOKEN") or line.startswith("STATUS"):
            continue
            
        values = line.split(",")
        if len(values) != 6:
            continue
            
        ax, ay, az, gx, gy, gz = values
        data.append([float(ax), float(ay), float(az), float(gx), float(gy), float(gz)])
    except:
        pass

df = pd.DataFrame(data, columns=["ax", "ay", "az", "gx", "gy", "gz"])
df.to_csv(filename, index=False)

print(f"\n✅ Saved {len(data)} readings → {filename}")
ser.close()