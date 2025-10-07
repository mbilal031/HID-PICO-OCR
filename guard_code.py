# guard_code.py — Handles Steam Guard code generation + test mode
import time, hmac, base64, struct, hashlib, os

# ---------------- CONFIG ----------------
SHARED_SECRET = os.getenv("STEAM_SHARED_SECRET", "7OYHtULTC65q6omCzxshKsqZc2c=") # 1 id 

# Switch to kolearujo665 shared_secret
#SHARED_SECRET = os.getenv(
   # "STEAM_SHARED_SECRET",
   # "mqdrEwcF+lXSQwnANfbPy6xvcGY="   # default fallback
#)

TEST_WRONG_GUARD = False # Set True for testing invalid guard popup
# ----------------------------------------

def generate_steam_guard_code(shared_secret_base64):
    shared_secret = base64.b64decode(shared_secret_base64)
    timestamp = int(time.time()) // 30
    time_bytes = struct.pack('>Q', timestamp)
    hmac_hash = hmac.new(shared_secret, time_bytes, hashlib.sha1).digest()
    offset = hmac_hash[-1] & 0x0F
    truncated_hash = hmac_hash[offset:offset+4]
    code_int = struct.unpack('>I', truncated_hash)[0] & 0x7FFFFFFF
    steam_chars = '23456789BCDFGHJKMNPQRTVWXY'
    code = ''
    for _ in range(5):
        code += steam_chars[code_int % len(steam_chars)]
        code_int //= len(steam_chars)
    return code

def get_guard_code():
    """Return either correct or dummy code depending on test flag"""
    if TEST_WRONG_GUARD:
        return "AAAAA"   # Always invalid (for testing OCR detection)
    return generate_steam_guard_code(SHARED_SECRET)
