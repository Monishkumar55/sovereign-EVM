import os

fix = '''import sqlite3
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

def add_voter(slot_id, voter_id, name):
    conn     = sqlite3.connect(DB_PATH)
    c        = conn.cursor()
    name_enc = encrypt(name)
    c.execute(
        "INSERT OR IGNORE INTO voters (slot_id, voter_id, name_enc) VALUES (?,?,?)",
        (slot_id, voter_id, name_enc)
    )
    conn.commit()
    conn.close()
    log_event("ENROLLED:" + voter_id + ":slot" + str(slot_id))
    print("Voter " + voter_id + " enrolled at slot " + str(slot_id))

def get_voter(slot_id):
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

def has_voted(slot_id):
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute("SELECT has_voted FROM voters WHERE slot_id=?", (slot_id,))
    row  = c.fetchone()
    conn.close()
    return row is not None and row[0] == 1

def record_vote(slot_id, party_id):
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
    log_event("VOTE_CAST:slot" + str(slot_id) + ":party" + party_id)
    print("Vote recorded - slot " + str(slot_id) + " to party " + party_id)

def setup_parties(parties):
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

def get_results():
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

def log_event(event):
    conn      = sqlite3.connect(DB_PATH)
    c         = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    h         = chain_hash(timestamp + ":" + event)
    c.execute(
        "INSERT INTO audit_log (timestamp, event, hash) VALUES (?,?,?)",
        (timestamp, event, h)
    )
    conn.commit()
    conn.close()

def get_total_votes():
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute("SELECT COUNT(*) FROM voters WHERE has_voted=1")
    count = c.fetchone()[0]
    conn.close()
    return count

def get_total_enrolled():
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute("SELECT COUNT(*) FROM voters")
    count = c.fetchone()[0]
    conn.close()
    return count
'''

with open("database.py", "w", encoding="utf-8") as f:
    f.write(fix)

print("database.py fixed successfully!")
print("Now run: python enroll.py")
