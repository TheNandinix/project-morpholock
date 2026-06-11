import psutil
import logging

# This sets up a log so every event is printed with a timestamp
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Dictionary of dangerous processes → (display name, risk score out of 100)
# AnyDesk/TeamViewer/RustDesk are HIGH risk (they give full remote control)
# Zoom/Teams are MEDIUM risk (screen sharing possible but not always malicious)
# Discord/Skype are LOW risk (voice/chat but can share screen)
THREAT_PROCESSES = {
    "anydesk.exe":                      ("AnyDesk",                  100),
    "teamviewer.exe":                   ("TeamViewer",               100),
    "rustdesk.exe":                     ("RustDesk",                 100),
    "chrome_remote_desktop_host.exe":   ("Chrome Remote Desktop",    100),
    "vnc.exe":                          ("VNC Viewer",                90),
    "logmein.exe":                      ("LogMeIn",                   90),
    "zoom.exe":                         ("Zoom",                      60),
    "teams.exe":                        ("Microsoft Teams",           50),
    "skype.exe":                        ("Skype",                     40),
    "discord.exe":                      ("Discord",                   25),
}

def scan_environment() -> dict:
    """
    Scans all running processes and returns a risk integer (0-100).
    0   = completely clean, safe to proceed
    1-49 = low/medium risk, soft-block or warn
    50-79 = high risk, block transaction
    80-100 = critical, immediate block + flag
    """
    detected = []
    max_risk = 0   # We take the HIGHEST risk from all detected threats

    # Get all running process names in one shot, lowercased for comparison
    try:
        running_processes = {p.name().lower() for p in psutil.process_iter(['name'])}
    except Exception as e:
        logger.error(f"Process scan failed: {e}")
        # If we can't scan, we don't know — return a medium risk to be safe
        return {"risk_score": 50, "threats": [], "status": "SCAN_ERROR"}

    # Check each threat process against what's running
    for proc_name, (display_name, risk) in THREAT_PROCESSES.items():
        if proc_name.lower() in running_processes:
            detected.append(display_name)
            max_risk = max(max_risk, risk)   # Keep the worst score found
            logger.warning(f"THREAT DETECTED: {display_name} is running (risk +{risk})")

    # Decide status label
    if max_risk == 0:
        status = "CLEAR"
    elif max_risk < 50:
        status = "LOW_RISK"
    elif max_risk < 80:
        status = "HIGH_RISK"
    else:
        status = "CRITICAL_THREAT"

    result = {
        "risk_score": max_risk,    # Integer 0-100 — this is what Phase 2 & 3 will consume
        "threats": detected,        # List of app names found
        "status": status            # Human-readable label
    }
    logger.info(f"Scan complete → {result}")
    return result


# This block only runs when you run the file directly (not when imported)
if __name__ == "__main__":
    print("\n=== MorphoLock Context Scanner ===")
    result = scan_environment()
    print(f"\nRisk Score : {result['risk_score']}/100")
    print(f"Status     : {result['status']}")
    if result['threats']:
        print(f"Threats    : {', '.join(result['threats'])}")
    else:
        print("Threats    : None detected")
    print("==================================\n")