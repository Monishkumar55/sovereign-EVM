import os

# Create folders
os.makedirs("data",  exist_ok=True)
os.makedirs("keys",  exist_ok=True)
print("Folders created.")

# ── crypto.py ─────────────────────────────────────────────
crypto_code = '''import os
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
'''

# ── database.py ───────────────────────────────────────────
database_code = '''import sqlite3
import os
from datetime import datetime
from crypto import encrypt, decrypt, chain_hash

DB_PATH = "data/voters.db"

def init_db():
    if not os.path.exists("data"):
        os.makedirs("data")
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS voters (
        slot_id   INTEGER PRIMARY KEY,
        voter_id  TEXT UNIQUE NOT NULL,
        name_enc  BLOB,
        has_voted INTEGER DEFAULT 0,
        voted_at  TEXT DEFAULT NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS vote_counts (
        party_id   TEXT PRIMARY KEY,
        party_name TEXT NOT NULL,
        count_enc  BLOB NOT NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS audit_log (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        event     TEXT NOT NULL,
        hash      TEXT NOT NULL
    )""")
    conn.commit()
    conn.close()
    print("Database initialized.")

def add_voter(slot_id: int, voter_id: str, name: str):
    conn     = sqlite3.connect(DB_PATH)
    c        = conn.cursor()
    name_enc = encrypt(name)
    c.execute(
        "INSERT OR IGNORE INTO voters (slot_id, voter_id, name_enc) VALUES (?,?,?)",
        (slot_id, voter_id, name_enc)
    )
    conn.commit()
    conn.close()
    log_event(f"ENROLLED:{voter_id}:slot{slot_id}")
    print(f"Voter {voter_id} enrolled at slot {slot_id}")

def get_voter(slot_id: int):
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute(
        "SELECT slot_id, voter_id, name_enc, has_voted FROM voters WHERE slot_id=?",
        (slot_id,)
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "slot_id":   row[0],
        "voter_id":  row[1],
        "name":      decrypt(row[2]),
        "has_voted": bool(row[3])
    }

def has_voted(slot_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute("SELECT has_voted FROM voters WHERE slot_id=?", (slot_id,))
    row  = c.fetchone()
    conn.close()
    return row is not None and row[0] == 1

def record_vote(slot_id: int, party_id: str):
    conn      = sqlite3.connect(DB_PATH)
    c         = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        "UPDATE voters SET has_voted=1, voted_at=? WHERE slot_id=?",
        (timestamp, slot_id)
    )
    c.execute("SELECT count_enc FROM vote_counts WHERE party_id=?", (party_id,))
    row = c.fetchone()
    if row:
        current   = int(decrypt(row[0]))
        new_count = encrypt(str(current + 1))
        c.execute(
            "UPDATE vote_counts SET count_enc=? WHERE party_id=?",
            (new_count, party_id)
        )
    conn.commit()
    conn.close()
    log_event(f"VOTE_CAST:slot{slot_id}:party{party_id}")
    print(f"Vote recorded — slot {slot_id} to party {party_id}")

def setup_parties(parties: list):
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    for party_id, party_name in parties:
        c.execute(
            "INSERT OR IGNORE INTO vote_counts (party_id, party_name, count_enc) VALUES (?,?,?)",
            (party_id, party_name, encrypt("0"))
        )
    conn.commit()
    conn.close()
    print("Parties initialized.")

def get_results() -> dict:
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute("SELECT party_id, party_name, count_enc FROM vote_counts")
    rows = c.fetchall()
    conn.close()
    results = {}
    for party_id, party_name, count_enc in rows:
        results[party_id] = {
            "name":  party_name,
            "votes": int(decrypt(count_enc))
        }
    return results

def log_event(event: str):
    conn      = sqlite3.connect(DB_PATH)
    c         = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    h         = chain_hash(f"{timestamp}:{event}")
    c.execute(
        "INSERT INTO audit_log (timestamp, event, hash) VALUES (?,?,?)",
        (timestamp, event, h)
    )
    conn.commit()
    conn.close()

def get_total_votes() -> int:
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute("SELECT COUNT(*) FROM voters WHERE has_voted=1")
    count = c.fetchone()[0]
    conn.close()
    return count

def get_total_enrolled() -> int:
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute("SELECT COUNT(*) FROM voters")
    count = c.fetchone()[0]
    conn.close()
    return count
'''

# ── fingerprint.py ────────────────────────────────────────
fingerprint_code = '''import random
import time
import os

IS_PI = os.path.exists("/dev/ttyS0")

if IS_PI:
    import serial
    import adafruit_fingerprint
    uart   = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)
    finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

_sim_enrolled = {}

def sim_enroll(slot_id: int) -> bool:
    print(f"[SIM] Enrolling fingerprint for slot {slot_id}...")
    time.sleep(1)
    _sim_enrolled[slot_id] = True
    print(f"[SIM] Fingerprint captured for slot {slot_id}")
    return True

def sim_scan() -> int:
    if not _sim_enrolled:
        print("[SIM] No fingerprints enrolled yet.")
        return -1
    print("[SIM] Scanning fingerprint...")
    time.sleep(1)
    slot = random.choice(list(_sim_enrolled.keys()))
    print(f"[SIM] Matched slot {slot}")
    return slot

def real_enroll(slot_id: int) -> bool:
    print("Place finger on sensor...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    finger.image_2_tz(1)
    print("Lift and place again...")
    time.sleep(1)
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    finger.image_2_tz(2)
    if finger.create_model() != adafruit_fingerprint.OK:
        return False
    return finger.store_model(slot_id) == adafruit_fingerprint.OK

def real_scan() -> int:
    if finger.get_image() != adafruit_fingerprint.OK:
        return -1
    finger.image_2_tz(1)
    if finger.finger_search() == adafruit_fingerprint.OK:
        return finger.finger_id
    return -1

def enroll_fingerprint(slot_id: int) -> bool:
    return real_enroll(slot_id) if IS_PI else sim_enroll(slot_id)

def scan_fingerprint() -> int:
    return real_scan() if IS_PI else sim_scan()
'''

# ── session.py ────────────────────────────────────────────
session_code = '''from datetime import datetime

POLL_START = 8
POLL_END   = 18

def is_session_active() -> bool:
    hour = datetime.now().hour
    return POLL_START <= hour < POLL_END

def current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def time_remaining() -> str:
    now  = datetime.now()
    end  = now.replace(hour=POLL_END, minute=0, second=0)
    diff = end - now
    if diff.total_seconds() <= 0:
        return "Session Ended"
    hours, rem = divmod(int(diff.total_seconds()), 3600)
    mins = rem // 60
    return f"{hours}h {mins}m remaining"
'''

# ── ui.py ─────────────────────────────────────────────────
ui_code = '''import os
import time

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def header():
    print("=" * 55)
    print("       SOVEREIGN EVM - SECURE VOTING MACHINE")
    print("       Air-Gapped | AES-256 | Biometric Auth")
    print("=" * 55)

def show_welcome():
    clear()
    header()
    print("\\n  STATUS  : READY")
    print("  NETWORK : DISABLED")
    print("  SENSOR  : ACTIVE\\n")
    print("  Place finger on sensor to begin...\\n")
    print("=" * 55)

def show_scanning():
    clear()
    header()
    print("\\n  Scanning fingerprint...")
    print("  [||||||||||||||||    ] Please wait...\\n")

def show_voter(voter: dict, time_left: str):
    clear()
    header()
    print(f"\\n  VOTER IDENTIFIED")
    print(f"  -----------------------------------------------")
    print(f"  ID   : {voter[\'voter_id\']}")
    print(f"  Name : {voter[\'name\']}")
    print(f"  Time : {time_left}")
    print(f"  -----------------------------------------------\\n")

def show_parties(parties: list) -> str:
    print("  SELECT YOUR PARTY:")
    print("  -----------------------------------------------")
    for i, (pid, pname) in enumerate(parties, 1):
        print(f"  {i}. {pname}")
    print("  -----------------------------------------------")
    print("  0. Cancel\\n")
    while True:
        choice = input("  Enter number: ").strip()
        if choice == "0":
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(parties):
            return parties[int(choice) - 1][0]
        print("  Invalid. Try again.")

def show_confirm(party_name: str) -> bool:
    print(f"\\n  You selected : {party_name}")
    print("  -----------------------------------------------")
    print("  1. CONFIRM and cast vote")
    print("  2. Go back\\n")
    return input("  Enter choice: ").strip() == "1"

def show_success(voter_id: str, hash_val: str):
    clear()
    header()
    print("\\n  VOTE CAST SUCCESSFULLY")
    print("  -----------------------------------------------")
    print(f"  Voter : {voter_id}")
    print(f"  Hash  : {hash_val[:32]}...")
    print("  -----------------------------------------------")
    print("  Your vote is securely recorded.\\n")
    time.sleep(3)

def show_already_voted(voter_id: str):
    clear()
    header()
    print("\\n  DUPLICATE VOTE BLOCKED")
    print("  -----------------------------------------------")
    print(f"  Voter {voter_id} has already voted.")
    print("  This attempt has been logged.")
    print("  -----------------------------------------------\\n")
    time.sleep(3)

def show_unknown():
    clear()
    header()
    print("\\n  FINGERPRINT NOT RECOGNIZED")
    print("  -----------------------------------------------")
    print("  This fingerprint is not enrolled.")
    print("  -----------------------------------------------\\n")
    time.sleep(2)

def show_session_closed():
    clear()
    header()
    print("\\n  VOTING SESSION CLOSED")
    print("  -----------------------------------------------")
    print("  Polling hours: 08:00 AM - 06:00 PM")
    print("  Machine is locked.")
    print("  -----------------------------------------------\\n")

def show_results(results: dict, total: int, enrolled: int):
    clear()
    header()
    print("\\n  FINAL RESULTS")
    print("  -----------------------------------------------")
    for pid, data in results.items():
        bar_len = int((data["votes"] / max(total, 1)) * 20)
        bar     = "=" * bar_len + "-" * (20 - bar_len)
        pct     = round(data["votes"] / max(total, 1) * 100, 1)
        print(f"  {data[\'name\'][:20]:<20} [{bar}] {data[\'votes\']} ({pct}%)")
    print("  -----------------------------------------------")
    print(f"  Total votes : {total}")
    print(f"  Enrolled    : {enrolled}")
    print(f"  Turnout     : {round(total / max(enrolled, 1) * 100, 1)}%")
    print("  -----------------------------------------------\\n")
'''

# ── enroll.py ─────────────────────────────────────────────
enroll_code = '''from database    import init_db, add_voter, setup_parties
from fingerprint import enroll_fingerprint

PARTIES = [
    ("P1", "National Alliance"),
    ("P2", "Democratic Front"),
    ("P3", "Peoples Party"),
    ("P4", "United Progress"),
    ("P5", "Reform Coalition"),
]

def enroll_voter():
    print("\\n" + "=" * 40)
    voter_id = input("Enter Voter ID (e.g. VTR-0001): ").strip()
    name     = input("Enter Voter Name              : ").strip()
    slot_id  = int(input("Enter Fingerprint Slot (1-100): ").strip())
    success  = enroll_fingerprint(slot_id)
    if success:
        add_voter(slot_id, voter_id, name)
        print(f"SUCCESS - {name} enrolled at slot {slot_id}")
    else:
        print("FAILED - Try again.")

if __name__ == "__main__":
    init_db()
    setup_parties(PARTIES)
    while True:
        print("\\n1. Enroll new voter")
        print("2. Exit")
        choice = input("Choice: ").strip()
        if choice == "1":
            enroll_voter()
        elif choice == "2":
            print("Enrollment complete.")
            break
'''

# ── main.py ───────────────────────────────────────────────
main_code = '''from fingerprint import scan_fingerprint
from database    import (init_db, setup_parties, get_voter,
                          has_voted, record_vote, log_event,
                          get_results, get_total_votes,
                          get_total_enrolled)
from session     import is_session_active, time_remaining
from crypto      import chain_hash
from ui          import (show_welcome, show_scanning, show_voter,
                          show_parties, show_confirm, show_success,
                          show_already_voted, show_unknown,
                          show_session_closed, show_results,
                          clear, header)
import time
import sqlite3

PARTIES = [
    ("P1", "National Alliance"),
    ("P2", "Democratic Front"),
    ("P3", "Peoples Party"),
    ("P4", "United Progress"),
    ("P5", "Reform Coalition"),
]

def admin_menu():
    clear()
    header()
    print("\\n  ADMIN PANEL")
    print("  1. View live results")
    print("  2. View audit log")
    print("  3. Back\\n")
    choice = input("  Choice: ").strip()
    if choice == "1":
        results  = get_results()
        total    = get_total_votes()
        enrolled = get_total_enrolled()
        show_results(results, total, enrolled)
        input("  Press Enter to continue...")
    elif choice == "2":
        conn = sqlite3.connect("data/voters.db")
        c    = conn.cursor()
        c.execute("SELECT timestamp, event, hash FROM audit_log ORDER BY id DESC LIMIT 10")
        rows = c.fetchall()
        conn.close()
        clear()
        header()
        print("\\n  LAST 10 AUDIT EVENTS")
        print("  -----------------------------------------------")
        for ts, ev, h in rows:
            print(f"  {ts} | {ev}")
            print(f"  {h[:45]}...")
            print()
        input("  Press Enter to continue...")

def voting_loop():
    print("\\n  EVM is running. Press Ctrl+C to stop.")
    log_event("SESSION_START")
    while True:
        if not is_session_active():
            show_session_closed()
            break
        show_welcome()
        cmd = input("  Press ENTER to scan | A for admin: ").strip().lower()
        if cmd == "a":
            admin_menu()
            continue
        show_scanning()
        slot_id = scan_fingerprint()
        if slot_id == -1:
            log_event("UNKNOWN_FP_SCAN")
            show_unknown()
            continue
        voter = get_voter(slot_id)
        if not voter:
            log_event(f"VOTER_NOT_FOUND:slot{slot_id}")
            show_unknown()
            continue
        if has_voted(slot_id):
            log_event(f"DUPLICATE_BLOCKED:{voter[\'voter_id\']}")
            show_already_voted(voter["voter_id"])
            continue
        show_voter(voter, time_remaining())
        party_id = show_parties(PARTIES)
        if not party_id:
            log_event(f"VOTE_CANCELLED:{voter[\'voter_id\']}")
            print("\\n  Vote cancelled.")
            time.sleep(2)
            continue
        party_name = dict(PARTIES)[party_id]
        confirmed  = show_confirm(party_name)
        if not confirmed:
            print("\\n  Returning to party selection...")
            time.sleep(1)
            continue
        record_vote(slot_id, party_id)
        h = chain_hash(f"{voter[\'voter_id\']}:{party_id}")
        show_success(voter["voter_id"], h)
    log_event("SESSION_END")
    show_results(get_results(), get_total_votes(), get_total_enrolled())

if __name__ == "__main__":
    init_db()
    setup_parties(PARTIES)
    voting_loop()
'''

# ── Write all files ───────────────────────────────────────
files = {
    "crypto.py":      crypto_code,
    "database.py":    database_code,
    "fingerprint.py": fingerprint_code,
    "session.py":     session_code,
    "ui.py":          ui_code,
    "enroll.py":      enroll_code,
    "main.py":        main_code,
}

for filename, code in files.items():
    with open(filename, "w") as f:
        f.write(code)
    print(f"Created: {filename}")

print("\nAll files created successfully!")
print("Now run: python enroll.py")
