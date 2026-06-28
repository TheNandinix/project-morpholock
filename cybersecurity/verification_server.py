import hmac
import hashlib
import time
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="MorphoLock Verification Server")

# This secret key must match exactly what the Arduino uses to sign tokens
# In a real deployment this would be stored in a hardware secure element
SECRET_KEY = b"MORPHOLOCK_SECRET_2026"

# How long a token stays valid (2 seconds — tight window defeats replay attacks)
TOKEN_VALIDITY_MS = 2000

# In-memory store of used tokens — prevents the same token being accepted twice
# In production this would be a Redis cache or database
used_tokens = set()


class VerifyRequest(BaseModel):
    """
    What the Arduino (or Python bridge) sends to this server.
    nonce    = transaction ID + amount + timestamp joined as a string
    token    = HMAC-SHA256 hex of that nonce, signed with SECRET_KEY
    timestamp = when the token was created (Unix ms)
    """
    nonce: str = Field(..., min_length=10, max_length=200)
    token: str = Field(..., min_length=64, max_length=64)
    timestamp: int = Field(..., gt=0)


def compute_expected_hmac(nonce: str) -> str:
    """Recompute what the HMAC should be, using our secret key."""
    return hmac.new(SECRET_KEY, nonce.encode(), hashlib.sha256).hexdigest()


@app.post("/verify")
def verify_token(req: VerifyRequest):

    # --- CHECK 1: Replay attack --- #
    # If we've seen this token before, it's being reused → block immediately
    if req.token in used_tokens:
        logger.critical(f"REPLAY ATTACK BLOCKED: token {req.token[:16]}... already used")
        raise HTTPException(status_code=401, detail="REPLAY_ATTACK_DETECTED")

    # --- CHECK 2: Expiry --- #
    # Token must arrive within 2 seconds of being created
    now_ms = int(time.time() * 1000)
    age_ms = now_ms - req.timestamp
    if age_ms > TOKEN_VALIDITY_MS:
        logger.warning(f"TOKEN EXPIRED: age={age_ms}ms (limit={TOKEN_VALIDITY_MS}ms)")
        raise HTTPException(status_code=401, detail="TOKEN_EXPIRED")

    # --- CHECK 3: Authenticity --- #
    # Recompute HMAC and compare — hmac.compare_digest() prevents timing attacks
    # (a normal == comparison leaks info via how long it takes to fail)
    expected = compute_expected_hmac(req.nonce)
    if not hmac.compare_digest(expected, req.token.lower()):
        logger.critical(f"INVALID TOKEN: expected {expected[:16]}..., got {req.token[:16]}...")
        raise HTTPException(status_code=401, detail="INVALID_TOKEN")

    # --- ALL CHECKS PASSED --- #
    used_tokens.add(req.token)   # Mark as used so it can't be replayed
    logger.info(f"TOKEN APPROVED: nonce={req.nonce}, age={age_ms}ms")
    return {
        "status": "APPROVED",
        "nonce": req.nonce,
        "age_ms": age_ms
    }


@app.get("/health")
def health_check():
    """Quick ping to confirm server is alive."""
    return {"status": "running", "tokens_used": len(used_tokens)}