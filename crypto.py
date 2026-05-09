import os
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_PATH = "keys/evm.key"

def generate_key():
    if not os.path.exists("keys"):
        os.makedirs("keys")
    key = os.urandom(32)
    with open(KEY_PATH, "wb") as f:
        f.write(key)
    print("Master key generated.")

def load_key():
    if not os.path.exists(KEY_PATH):
        generate_key()
    with open(KEY_PATH, "rb") as f:
        return f.read()

def encrypt(data: str) -> bytes:
    key    = load_key()
    aesgcm = AESGCM(key)
    nonce  = os.urandom(12)
    ct     = aesgcm.encrypt(nonce, data.encode(), None)
    return nonce + ct

def decrypt(token: bytes) -> str:
    key    = load_key()
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(token[:12], token[12:], None).decode()

_prev_hash = "GENESIS_BLOCK"

def chain_hash(event: str) -> str:
    global _prev_hash
    raw      = f"{_prev_hash}|{event}".encode()
    new_hash = hashlib.sha512(raw).hexdigest()
    _prev_hash = new_hash
    return new_hash
