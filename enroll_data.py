import serial, csv, time, logging, os

def collect_one_session(ser, session_id, out_folder):
    rows = []
    while len(rows) < 200:
        line = ser.readline().decode('utf-8').strip()
        parts = line.split(',')
        if len(parts) == 6:
            try:
                rows.append([float(x) for x in parts])
            except:
                pass

    os.makedirs(out_folder, exist_ok=True)
    path = os.path.join(out_folder, f'session_{session_id:03d}.csv')
    with open(path, 'w', newline='') as f:
        csv.writer(f).writerows(rows)
    return path