# results.py
# Run this AFTER voting session ends
# Requires 3 of 5 officials to enter their shares
# No single person can read results alone

from shamir import (split_master_key, decrypt_results_with_shares,
                    string_to_share, hash_share)
import os

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def header():
    print("=" * 55)
    print("   SOVEREIGN EVM - RESULT DECRYPTION TERMINAL")
    print("   Requires 3 of 5 official shares to proceed")
    print("=" * 55)

def collect_shares(required=3):
    """Collect share strings from officials one by one"""
    print(f"\n  {required} officials must enter their share.")
    print("  Each share is in format:  1:123456789...\n")

    shares = []
    for i in range(required):
        while True:
            print(f"  Official {i+1} of {required}:")
            share_str = input("  Enter your share value: ").strip()
            try:
                share  = string_to_share(share_str)
                verify = hash_share(share)
                print(f"  Verification code: {verify}")
                confirm = input("  Does this match your card? (y/n): ").strip().lower()
                if confirm == "y":
                    shares.append(share_str)
                    print(f"  Share {i+1} accepted.\n")
                    break
                else:
                    print("  Please re-enter your share.\n")
            except Exception:
                print("  Invalid share format. Try again.\n")

    return shares

def main():
    clear()
    header()
    print("\n  1. Split master key into shares (do this before election)")
    print("  2. Decrypt results using 3 shares (do this after election)")
    print("  3. Exit\n")

    choice = input("  Choice: ").strip()

    if choice == "1":
        print("\n  WARNING: This will split the master key.")
        print("  Do this ONLY before election day.")
        confirm = input("  Are you sure? (yes/no): ").strip().lower()
        if confirm == "yes":
            split_master_key(total=5, threshold=3)
        else:
            print("  Cancelled.")

    elif choice == "2":
        clear()
        header()
        print("\n  RESULT DECRYPTION")
        print("  -" * 27)
        print("  Collect shares from 3 officials.\n")
        shares = collect_shares(required=3)
        print("\n  All shares collected. Decrypting results...")
        try:
            decrypt_results_with_shares(shares)
        except Exception as e:
            print(f"\n  DECRYPTION FAILED: {e}")
            print("  Wrong shares or corrupted data.")

    elif choice == "3":
        print("  Exiting.")

if __name__ == "__main__":
    main()
