from fingerprint import scan_fingerprint
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
    print("\n  ADMIN PANEL")
    print("  1. View live results")
    print("  2. View audit log")
    print("  3. Back\n")
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
        print("\n  LAST 10 AUDIT EVENTS")
        print("  -----------------------------------------------")
        for ts, ev, h in rows:
            print(f"  {ts} | {ev}")
            print(f"  {h[:45]}...")
            print()
        input("  Press Enter to continue...")

def voting_loop():
    print("\n  EVM is running. Press Ctrl+C to stop.")
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
            log_event(f"DUPLICATE_BLOCKED:{voter['voter_id']}")
            show_already_voted(voter["voter_id"])
            continue
        show_voter(voter, time_remaining())
        party_id = show_parties(PARTIES)
        if not party_id:
            log_event(f"VOTE_CANCELLED:{voter['voter_id']}")
            print("\n  Vote cancelled.")
            time.sleep(2)
            continue
        party_name = dict(PARTIES)[party_id]
        confirmed  = show_confirm(party_name)
        if not confirmed:
            print("\n  Returning to party selection...")
            time.sleep(1)
            continue
        record_vote(slot_id, party_id)
        h = chain_hash(f"{voter['voter_id']}:{party_id}")
        show_success(voter["voter_id"], h)
    log_event("SESSION_END")
    show_results(get_results(), get_total_votes(), get_total_enrolled())

if __name__ == "__main__":
    init_db()
    setup_parties(PARTIES)
    voting_loop()
