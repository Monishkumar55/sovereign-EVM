import os
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
    print("\n  STATUS  : READY")
    print("  NETWORK : DISABLED")
    print("  SENSOR  : ACTIVE\n")
    print("  Place finger on sensor to begin...\n")
    print("=" * 55)

def show_scanning():
    clear()
    header()
    print("\n  Scanning fingerprint...")
    print("  [||||||||||||||||    ] Please wait...\n")

def show_voter(voter: dict, time_left: str):
    clear()
    header()
    print(f"\n  VOTER IDENTIFIED")
    print(f"  -----------------------------------------------")
    print(f"  ID   : {voter['voter_id']}")
    print(f"  Name : {voter['name']}")
    print(f"  Time : {time_left}")
    print(f"  -----------------------------------------------\n")

def show_parties(parties: list) -> str:
    print("  SELECT YOUR PARTY:")
    print("  -----------------------------------------------")
    for i, (pid, pname) in enumerate(parties, 1):
        print(f"  {i}. {pname}")
    print("  -----------------------------------------------")
    print("  0. Cancel\n")
    while True:
        choice = input("  Enter number: ").strip()
        if choice == "0":
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(parties):
            return parties[int(choice) - 1][0]
        print("  Invalid. Try again.")

def show_confirm(party_name: str) -> bool:
    print(f"\n  You selected : {party_name}")
    print("  -----------------------------------------------")
    print("  1. CONFIRM and cast vote")
    print("  2. Go back\n")
    return input("  Enter choice: ").strip() == "1"

def show_success(voter_id: str, hash_val: str):
    clear()
    header()
    print("\n  VOTE CAST SUCCESSFULLY")
    print("  -----------------------------------------------")
    print(f"  Voter : {voter_id}")
    print(f"  Hash  : {hash_val[:32]}...")
    print("  -----------------------------------------------")
    print("  Your vote is securely recorded.\n")
    time.sleep(3)

def show_already_voted(voter_id: str):
    clear()
    header()
    print("\n  DUPLICATE VOTE BLOCKED")
    print("  -----------------------------------------------")
    print(f"  Voter {voter_id} has already voted.")
    print("  This attempt has been logged.")
    print("  -----------------------------------------------\n")
    time.sleep(3)

def show_unknown():
    clear()
    header()
    print("\n  FINGERPRINT NOT RECOGNIZED")
    print("  -----------------------------------------------")
    print("  This fingerprint is not enrolled.")
    print("  -----------------------------------------------\n")
    time.sleep(2)

def show_session_closed():
    clear()
    header()
    print("\n  VOTING SESSION CLOSED")
    print("  -----------------------------------------------")
    print("  Polling hours: 08:00 AM - 06:00 PM")
    print("  Machine is locked.")
    print("  -----------------------------------------------\n")

def show_results(results: dict, total: int, enrolled: int):
    clear()
    header()
    print("\n  FINAL RESULTS")
    print("  -----------------------------------------------")
    for pid, data in results.items():
        bar_len = int((data["votes"] / max(total, 1)) * 20)
        bar     = "=" * bar_len + "-" * (20 - bar_len)
        pct     = round(data["votes"] / max(total, 1) * 100, 1)
        print(f"  {data['name'][:20]:<20} [{bar}] {data['votes']} ({pct}%)")
    print("  -----------------------------------------------")
    print(f"  Total votes : {total}")
    print(f"  Enrolled    : {enrolled}")
    print(f"  Turnout     : {round(total / max(enrolled, 1) * 100, 1)}%")
    print("  -----------------------------------------------\n")
