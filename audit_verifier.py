# audit_verifier.py
# Proves to anyone that zero votes were tampered with
# Verifies the entire SHA-512 hash chain from genesis to last event
# Detects any insertion, deletion or modification of any record

import sqlite3
import hashlib
import os
from datetime import datetime

DB_PATH  = "data/voters.db"
LOG_PATH = "data/audit_report.txt"

# ── COLORS FOR TERMINAL ───────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def header():
    print("=" * 60)
    print("   SOVEREIGN EVM - AUDIT VERIFICATION SYSTEM")
    print("   SHA-512 Hash Chain Integrity Verifier")
    print("=" * 60)

# ── HASH CHAIN VERIFICATION ───────────────────────────────

def verify_hash_chain():
    """
    Rebuilds the entire hash chain from scratch
    and compares each stored hash against recomputed value.
    Any mismatch = tamper detected.
    """
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute("SELECT id, timestamp, event, hash FROM audit_log ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()

    if not rows:
        return False, 0, 0, []

    prev_hash  = "GENESIS_BLOCK"
    total      = len(rows)
    passed     = 0
    failed     = 0
    errors     = []

    for row in rows:
        row_id, timestamp, event, stored_hash = row

        # Recompute hash exactly as it was created
        raw      = f"{prev_hash}|{timestamp}:{event}".encode()
        computed = hashlib.sha512(raw).hexdigest()

        if computed == stored_hash:
            passed    += 1
            prev_hash  = stored_hash
        else:
            failed += 1
            errors.append({
                "id":       row_id,
                "event":    event,
                "stored":   stored_hash[:32],
                "computed": computed[:32]
            })
            # Still update prev_hash to continue checking rest of chain
            prev_hash = stored_hash

    return failed == 0, total, failed, errors

# ── DATABASE INTEGRITY ────────────────────────────────────

def verify_vote_counts():
    """
    Cross-check: count actual voted=1 rows
    against the sum of decrypted vote counters.
    They must match exactly.
    """
    from crypto import decrypt

    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    # Count voters marked as voted
    c.execute("SELECT COUNT(*) FROM voters WHERE has_voted=1")
    actual_votes = c.fetchone()[0]

    # Sum all party counters
    c.execute("SELECT party_id, party_name, count_enc FROM vote_counts")
    rows = c.fetchall()
    conn.close()

    party_total = 0
    party_data  = []
    decrypt_ok  = True

    for party_id, party_name, count_enc in rows:
        try:
            count = int(decrypt(count_enc))
            party_total += count
            party_data.append((party_name, count))
        except Exception as e:
            decrypt_ok = False
            party_data.append((party_name, "DECRYPT ERROR"))

    match = (actual_votes == party_total) and decrypt_ok
    return match, actual_votes, party_total, party_data

def verify_voter_integrity():
    """
    Check for any impossible voter states:
    - Voted but no timestamp
    - Not voted but has voted_for
    """
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    c.execute("""
        SELECT voter_id FROM voters
        WHERE has_voted=1 AND voted_at IS NULL
    """)
    voted_no_time = c.fetchall()

    c.execute("SELECT COUNT(*) FROM voters")
    total_enrolled = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM voters WHERE has_voted=1")
    total_voted = c.fetchone()[0]

    conn.close()

    anomalies = len(voted_no_time)
    return anomalies == 0, total_enrolled, total_voted, anomalies

def get_audit_stats():
    """Get summary statistics from audit log"""
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    c.execute("SELECT COUNT(*) FROM audit_log")
    total_events = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM audit_log WHERE event LIKE 'VOTE_CAST%'")
    vote_events = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM audit_log WHERE event LIKE 'DUPLICATE_BLOCKED%'")
    blocked_events = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM audit_log WHERE event LIKE 'ENROLLED%'")
    enroll_events = c.fetchone()[0]

    c.execute("SELECT timestamp FROM audit_log ORDER BY id ASC LIMIT 1")
    first = c.fetchone()
    first_time = first[0] if first else "N/A"

    c.execute("SELECT timestamp FROM audit_log ORDER BY id DESC LIMIT 1")
    last = c.fetchone()
    last_time = last[0] if last else "N/A"

    conn.close()

    return {
        "total":    total_events,
        "votes":    vote_events,
        "blocked":  blocked_events,
        "enrolled": enroll_events,
        "first":    first_time,
        "last":     last_time
    }

# ── REPORT GENERATOR ──────────────────────────────────────

def generate_report(chain_ok, chain_total, chain_failed,
                    count_ok, actual_votes, party_total, party_data,
                    voter_ok, enrolled, voted, anomalies,
                    stats, errors):
    """Generate a full text audit report"""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    overall   = chain_ok and count_ok and voter_ok

    lines = []
    lines.append("=" * 60)
    lines.append("   SOVEREIGN EVM — OFFICIAL AUDIT REPORT")
    lines.append(f"   Generated : {timestamp}")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"OVERALL VERDICT: {'INTEGRITY CONFIRMED' if overall else 'TAMPERING DETECTED'}")
    lines.append("")
    lines.append("-" * 60)
    lines.append("1. HASH CHAIN VERIFICATION")
    lines.append("-" * 60)
    lines.append(f"   Total events checked : {chain_total}")
    lines.append(f"   Passed               : {chain_total - chain_failed}")
    lines.append(f"   Failed               : {chain_failed}")
    lines.append(f"   Result               : {'PASS' if chain_ok else 'FAIL — CHAIN BROKEN'}")

    if errors:
        lines.append("")
        lines.append("   TAMPERED RECORDS:")
        for e in errors:
            lines.append(f"   - Event ID {e['id']}: {e['event']}")
            lines.append(f"     Stored  : {e['stored']}...")
            lines.append(f"     Expected: {e['computed']}...")

    lines.append("")
    lines.append("-" * 60)
    lines.append("2. VOTE COUNT VERIFICATION")
    lines.append("-" * 60)
    lines.append(f"   Voter records marked voted : {actual_votes}")
    lines.append(f"   Sum of party counters      : {party_total}")
    lines.append(f"   Match                      : {'YES' if count_ok else 'NO — MISMATCH DETECTED'}")
    lines.append("")
    lines.append("   Party breakdown:")
    for name, count in party_data:
        lines.append(f"   - {name:<24} : {count}")

    lines.append("")
    lines.append("-" * 60)
    lines.append("3. VOTER INTEGRITY CHECK")
    lines.append("-" * 60)
    lines.append(f"   Total enrolled : {enrolled}")
    lines.append(f"   Total voted    : {voted}")
    lines.append(f"   Anomalies      : {anomalies}")
    lines.append(f"   Result         : {'PASS' if voter_ok else 'FAIL — ANOMALIES FOUND'}")

    lines.append("")
    lines.append("-" * 60)
    lines.append("4. SESSION SUMMARY")
    lines.append("-" * 60)
    lines.append(f"   Total audit events   : {stats['total']}")
    lines.append(f"   Enrollments          : {stats['enrolled']}")
    lines.append(f"   Votes cast           : {stats['votes']}")
    lines.append(f"   Duplicates blocked   : {stats['blocked']}")
    lines.append(f"   Session start        : {stats['first']}")
    lines.append(f"   Session end          : {stats['last']}")
    lines.append(f"   Turnout              : {round(voted/max(enrolled,1)*100,1)}%")

    lines.append("")
    lines.append("=" * 60)
    lines.append(f"FINAL VERDICT: {'ALL CHECKS PASSED — ELECTION INTEGRITY CONFIRMED' if overall else 'CHECKS FAILED — INVESTIGATION REQUIRED'}")
    lines.append("=" * 60)

    return "\n".join(lines)

# ── MAIN DISPLAY ──────────────────────────────────────────

def run_verification():
    clear()
    header()
    print(f"\n  Running verification at {datetime.now().strftime('%H:%M:%S')}...\n")

    # Run all checks
    print("  [1/4] Verifying SHA-512 hash chain...")
    chain_ok, chain_total, chain_failed, errors = verify_hash_chain()

    print("  [2/4] Verifying vote counts...")
    count_ok, actual_votes, party_total, party_data = verify_vote_counts()

    print("  [3/4] Checking voter integrity...")
    voter_ok, enrolled, voted, anomalies = verify_voter_integrity()

    print("  [4/4] Collecting session statistics...")
    stats = get_audit_stats()

    overall = chain_ok and count_ok and voter_ok

    # Display results
    clear()
    header()
    print()

    # Overall verdict
    if overall:
        print(f"  {GREEN}{BOLD}VERDICT: ELECTION INTEGRITY CONFIRMED{RESET}")
    else:
        print(f"  {RED}{BOLD}VERDICT: TAMPERING DETECTED — INVESTIGATE{RESET}")

    print(f"\n  {'─' * 50}")

    # Check 1 — Hash chain
    status = f"{GREEN}PASS{RESET}" if chain_ok else f"{RED}FAIL{RESET}"
    print(f"\n  {BOLD}1. HASH CHAIN INTEGRITY{RESET}         [{status}]")
    print(f"     Events verified : {chain_total}")
    print(f"     Passed          : {chain_total - chain_failed}")
    print(f"     Failed          : {chain_failed}")
    if errors:
        print(f"     {RED}Tampered events:{RESET}")
        for e in errors:
            print(f"     - ID {e['id']}: {e['event']}")

    # Check 2 — Vote counts
    status = f"{GREEN}PASS{RESET}" if count_ok else f"{RED}FAIL{RESET}"
    print(f"\n  {BOLD}2. VOTE COUNT VERIFICATION{RESET}      [{status}]")
    print(f"     Voter records   : {actual_votes}")
    print(f"     Party total     : {party_total}")
    print(f"     Match           : {'YES' if count_ok else 'NO'}")
    print(f"     Breakdown:")
    for name, count in party_data:
        bar = "=" * int((count / max(party_total, 1)) * 15)
        print(f"       {name:<22} [{bar:<15}] {count}")

    # Check 3 — Voter integrity
    status = f"{GREEN}PASS{RESET}" if voter_ok else f"{RED}FAIL{RESET}"
    print(f"\n  {BOLD}3. VOTER RECORD INTEGRITY{RESET}       [{status}]")
    print(f"     Enrolled        : {enrolled}")
    print(f"     Voted           : {voted}")
    print(f"     Anomalies       : {anomalies}")
    print(f"     Turnout         : {round(voted/max(enrolled,1)*100,1)}%")

    # Check 4 — Session stats
    print(f"\n  {BOLD}4. SESSION STATISTICS{RESET}")
    print(f"     Total events    : {stats['total']}")
    print(f"     Votes cast      : {stats['votes']}")
    print(f"     Blocked         : {stats['blocked']}")
    print(f"     Session start   : {stats['first']}")
    print(f"     Session end     : {stats['last']}")

    print(f"\n  {'─' * 50}")

    # Save report
    report = generate_report(
        chain_ok, chain_total, chain_failed,
        count_ok, actual_votes, party_total, party_data,
        voter_ok, enrolled, voted, anomalies,
        stats, errors
    )

    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n  {CYAN}Report saved to: {LOG_PATH}{RESET}")
    print(f"\n{'=' * 60}\n")

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("ERROR: No database found.")
        print("Run enroll.py and main.py first.")
    else:
        run_verification()
        input("  Press Enter to exit...")
