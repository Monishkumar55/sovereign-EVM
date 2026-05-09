# shamir.py
# Shamir's Secret Sharing — Pure Python, No External Libraries
# Splits the AES master key into 5 shares
# Any 3 of 5 shares can reconstruct the key
# No single person can read results alone

import random
import hashlib
import os

# ── PRIME NUMBER ──────────────────────────────────────────
# Must be larger than any possible secret value (256-bit key = max 2^256)
# We use a well-known large prime for security
PRIME = 2**521 - 1  # Mersenne prime — cryptographically safe

# ── CORE MATH ─────────────────────────────────────────────

def _eval_polynomial(coefficients, x, prime):
    """
    Evaluate polynomial at point x under prime field.
    coefficients[0] is the secret (constant term).
    coefficients[1..] are random coefficients.
    """
    result = 0
    for coeff in reversed(coefficients):
        result = (result * x + coeff) % prime
    return result

def _extended_gcd(a, b):
    """Extended Euclidean Algorithm — needed for modular inverse"""
    if a == 0:
        return b, 0, 1
    gcd, x1, y1 = _extended_gcd(b % a, a)
    return gcd, y1 - (b // a) * x1, x1

def _mod_inverse(a, prime):
    """Modular multiplicative inverse using extended GCD"""
    _, x, _ = _extended_gcd(a % prime, prime)
    return x % prime

def _lagrange_interpolate(x, x_s, y_s, prime):
    """
    Lagrange interpolation to recover secret at x=0.
    x_s = list of x coordinates (share indices)
    y_s = list of y coordinates (share values)
    """
    k      = len(x_s)
    result = 0
    for i in range(k):
        numerator   = 1
        denominator = 1
        for j in range(k):
            if i != j:
                numerator   = (numerator * (x - x_s[j])) % prime
                denominator = (denominator * (x_s[i] - x_s[j])) % prime
        lagrange_poly = (numerator * _mod_inverse(denominator, prime)) % prime
        result        = (result + y_s[i] * lagrange_poly) % prime
    return result

# ── PUBLIC API ────────────────────────────────────────────

def split_secret(secret_bytes, total_shares=5, threshold=3):
    """
    Split a secret (bytes) into `total_shares` shares.
    Any `threshold` shares can reconstruct it.

    Returns list of (index, value) tuples — one per official.
    """
    # Convert bytes to integer
    secret_int = int.from_bytes(secret_bytes, "big")

    # Build polynomial: f(x) = secret + a1*x + a2*x^2 + ...
    # degree = threshold - 1
    coefficients = [secret_int] + [
        random.randrange(1, PRIME) for _ in range(threshold - 1)
    ]

    # Generate shares — evaluate polynomial at x = 1, 2, 3, ..., total_shares
    shares = []
    for i in range(1, total_shares + 1):
        x     = i
        y     = _eval_polynomial(coefficients, x, PRIME)
        shares.append((x, y))

    return shares

def reconstruct_secret(shares, secret_length_bytes=32):
    """
    Reconstruct the secret from any `threshold` shares.

    shares: list of (index, value) tuples
    secret_length_bytes: length of original secret in bytes (32 for AES-256)

    Returns the original secret as bytes.
    """
    x_s = [s[0] for s in shares]
    y_s = [s[1] for s in shares]

    secret_int = _lagrange_interpolate(0, x_s, y_s, PRIME)
    return secret_int.to_bytes(secret_length_bytes, "big")

def share_to_string(share):
    """Convert a share to a readable string for printing/saving"""
    index, value = share
    return f"{index}:{value}"

def string_to_share(s):
    """Convert string back to share tuple"""
    parts = s.strip().split(":")
    return (int(parts[0]), int(parts[1]))

def hash_share(share):
    """Generate a verification hash for a share"""
    data = f"{share[0]}:{share[1]}".encode()
    return hashlib.sha256(data).hexdigest()[:16].upper()

# ── KEY MANAGEMENT ────────────────────────────────────────

SHARES_DIR = "keys/shares"

def split_master_key(total=5, threshold=3):
    """
    Read the AES master key and split it into shares.
    Save each share to a separate file.
    Print each share for distribution to officials.
    """
    KEY_PATH = "keys/evm.key"

    if not os.path.exists(KEY_PATH):
        print("ERROR: Master key not found. Run enroll.py first.")
        return

    os.makedirs(SHARES_DIR, exist_ok=True)

    with open(KEY_PATH, "rb") as f:
        master_key = f.read()

    shares = split_secret(master_key, total, threshold)

    print("\n" + "=" * 60)
    print("   SHAMIR SECRET SHARING — KEY DISTRIBUTION")
    print(f"   Split: {total} shares | Threshold: any {threshold} to decrypt")
    print("=" * 60)

    officials = [
        "Returning Officer",
        "Election Observer",
        "Opposition Rep",
        "Presiding Officer",
        "Court Representative"
    ]

    for i, share in enumerate(shares):
        share_str  = share_to_string(share)
        verify     = hash_share(share)
        filename   = f"{SHARES_DIR}/share_{i+1}.txt"

        with open(filename, "w") as f:
            f.write(f"OFFICIAL : {officials[i]}\n")
            f.write(f"SHARE_ID : {i+1}\n")
            f.write(f"VALUE    : {share_str}\n")
            f.write(f"VERIFY   : {verify}\n")

        print(f"\n  SHARE {i+1} — {officials[i]}")
        print(f"  Value  : {share_str[:40]}...")
        print(f"  Verify : {verify}")
        print(f"  Saved  : {filename}")

    print("\n" + "=" * 60)
    print("  IMPORTANT: Delete keys/evm.key after distributing shares.")
    print("  Results can only be decrypted with any 3 of these 5 shares.")
    print("=" * 60 + "\n")

    return shares

def reconstruct_master_key(share_strings):
    """
    Reconstruct master key from share strings.
    share_strings: list of 3+ share strings entered by officials.

    Returns reconstructed key bytes.
    """
    shares     = [string_to_share(s) for s in share_strings]
    master_key = reconstruct_secret(shares, secret_length_bytes=32)
    return master_key

def decrypt_results_with_shares(share_strings):
    """
    Full flow: collect shares, reconstruct key, decrypt vote results.
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import sqlite3

    print("\n  Reconstructing master key from shares...")
    master_key = reconstruct_master_key(share_strings)

    # Test key by decrypting one vote count
    aesgcm = AESGCM(master_key)

    conn = sqlite3.connect("data/voters.db")
    c    = conn.cursor()
    c.execute("SELECT party_id, party_name, count_enc FROM vote_counts")
    rows = c.fetchall()
    conn.close()

    print("\n" + "=" * 55)
    print("   DECRYPTED FINAL RESULTS")
    print("=" * 55)

    total = 0
    party_results = []

    for party_id, party_name, count_enc in rows:
        try:
            count = int(aesgcm.decrypt(count_enc[:12], count_enc[12:], None).decode())
            party_results.append((party_name, count))
            total += count
        except Exception:
            print(f"  ERROR decrypting {party_name} — wrong key?")
            return

    for name, count in party_results:
        bar = "=" * int((count / max(total, 1)) * 20)
        pct = round(count / max(total, 1) * 100, 1)
        print(f"  {name:<22} [{bar:<20}] {count} ({pct}%)")

    print("=" * 55)
    print(f"  Total votes cast: {total}")
    print("=" * 55 + "\n")
