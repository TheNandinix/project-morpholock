import requests
import hmac
import hashlib
import time

SECRET_KEY = b"MorphoLockSecretKey2026"
SERVER = "http://127.0.0.1:8001"

def make_token(nonce: str) -> str:
    return hmac.new(SECRET_KEY, nonce.encode(), hashlib.sha256).hexdigest()

# --- TEST 1: Valid token (should return APPROVED) ---
print("\n[TEST 1] Valid token")
timestamp = int(time.time() * 1000)
nonce = f"TXN001:500INR:{timestamp}"
token = make_token(nonce)
resp = requests.post(f"{SERVER}/verify", json={"nonce": nonce, "token": token, "timestamp": timestamp})
print(f"Response: {resp.json()}")

# --- TEST 2: Replay attack (same token again — should be BLOCKED) ---
print("\n[TEST 2] Replay attack — same token reused")
resp2 = requests.post(f"{SERVER}/verify", json={"nonce": nonce, "token": token, "timestamp": timestamp})
print(f"Response: {resp2.json()}")

# --- TEST 3: Expired token (timestamp 10 seconds in the past) ---
print("\n[TEST 3] Expired token")
old_ts = int(time.time() * 1000) - 10000
old_nonce = f"TXN002:200INR:{old_ts}"
old_token = make_token(old_nonce)
resp3 = requests.post(f"{SERVER}/verify", json={"nonce": old_nonce, "token": old_token, "timestamp": old_ts})
print(f"Response: {resp3.json()}")

# --- TEST 4: Tampered token (should be INVALID) ---
print("\n[TEST 4] Tampered/fake token")
fake_ts = int(time.time() * 1000)
fake_nonce = f"TXN003:9999INR:{fake_ts}"
resp4 = requests.post(f"{SERVER}/verify", json={"nonce": fake_nonce, "token": "aabbccddeeff00112233445566778899aabbccddeeff001122334455667788", "timestamp": fake_ts})
print(f"Response: {resp4.json()}")