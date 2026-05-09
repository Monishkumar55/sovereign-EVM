from database    import init_db, add_voter, setup_parties
from fingerprint import enroll_fingerprint

PARTIES = [
    ("P1", "National Alliance"),
    ("P2", "Democratic Front"),
    ("P3", "Peoples Party"),
    ("P4", "United Progress"),
    ("P5", "Reform Coalition"),
]

def enroll_voter():
    print("\n" + "=" * 40)
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
        print("\n1. Enroll new voter")
        print("2. Exit")
        choice = input("Choice: ").strip()
        if choice == "1":
            enroll_voter()
        elif choice == "2":
            print("Enrollment complete.")
            break
