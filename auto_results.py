# auto_results.py
# Automatically reads share files and decrypts results
# No manual copy-paste needed

from shamir import decrypt_results_with_shares
import os

SHARES_DIR = "keys/shares"

def read_share_value(filename):
    """Read the VALUE line from a share file"""
    with open(filename, "r") as f:
        for line in f:
            if line.startswith("VALUE"):
                return line.split(":", 1)[1].strip()
    return None

def main():
    print("=" * 55)
    print("   SOVEREIGN EVM - AUTO RESULT DECRYPTION")
    print("=" * 55)

    # Check shares folder exists
    if not os.path.exists(SHARES_DIR):
        print("\n  ERROR: No shares found.")
        print("  Run: python results.py → choose 1 first.")
        return

    # List available share files
    share_files = sorted([
        f for f in os.listdir(SHARES_DIR)
        if f.endswith(".txt")
    ])

    if len(share_files) < 3:
        print(f"\n  ERROR: Need at least 3 share files.")
        print(f"  Found only {len(share_files)} share(s).")
        return

    print(f"\n  Found {len(share_files)} share files:")
    for i, fname in enumerate(share_files):
        print(f"  {i+1}. {fname}")

    print("\n  Which 3 shares to use?")
    print("  Enter 3 numbers separated by space (e.g: 1 2 3): ")
    choice = input("  > ").strip().split()

    if len(choice) != 3:
        print("  ERROR: Enter exactly 3 numbers.")
        return

    selected_files = []
    for c in choice:
        if not c.isdigit() or int(c) < 1 or int(c) > len(share_files):
            print(f"  ERROR: Invalid choice {c}")
            return
        selected_files.append(share_files[int(c) - 1])

    # Read share values
    share_strings = []
    print()
    for fname in selected_files:
        fpath = os.path.join(SHARES_DIR, fname)
        value = read_share_value(fpath)
        if not value:
            print(f"  ERROR: Could not read value from {fname}")
            return
        share_strings.append(value)
        print(f"  Read: {fname} -> {value[:30]}...")

    # Decrypt results
    print("\n  Decrypting results...")
    try:
        decrypt_results_with_shares(share_strings)
    except Exception as e:
        print(f"\n  DECRYPTION FAILED: {e}")
        print("  Make sure you voted using the SAME key that was split.")

if __name__ == "__main__":
    main()
