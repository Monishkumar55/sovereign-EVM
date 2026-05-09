# 🗳️ Sovereign EVM — Zero-Trust Biometric Voting Machine

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%204-red?style=for-the-badge&logo=raspberry-pi)
![Security](https://img.shields.io/badge/Encryption-AES--256--GCM-green?style=for-the-badge&logo=shield)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)
![Network](https://img.shields.io/badge/Network-AIR--GAPPED-black?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)

**The world's first fully open-source, air-gapped, cryptographically private biometric EVM with Shamir threshold decryption.**

[Features](#-features) • [Architecture](#-architecture) • [Hardware](#-hardware-setup) • [Installation](#-installation) • [Usage](#-usage) • [Security](#-security-model) • [Research](#-research)

</div>

---

## 🔐 What Makes This Different

| Feature | India ECI EVM | GitHub Smart EVM | Dominion ICP2 | **Sovereign EVM** |
|---|---|---|---|---|
| Biometric Auth | ✗ | ✓ | ✗ | ✅ Dual (FP + Face) |
| Air-Gapped | ✓ | ✗ | ✗ | ✅ Zero network hardware |
| AES-256 Encrypted Storage | ✗ | ✗ | Partial | ✅ Full |
| SHA-512 Hash Chain | ✗ | ✗ | ✗ | ✅ Every event |
| Shamir Secret Sharing | ✗ | ✗ | ✗ | ✅ 3-of-5 threshold |
| Tamper-Evident Audit | ✗ | ✗ | ✗ | ✅ Cryptographic proof |
| Open Source | ✗ | ✓ | ✗ | ✅ Fully auditable |
| Cost per Unit | ~₹8,000 | ~₹800 | ~₹7,00,000 | ✅ ~₹5,000 |

---

## ✨ Features

### 🔒 Security Layer
- **AES-256-GCM Encryption** — All voter data, vote counters and audit logs encrypted at rest
- **SHA-512 Hash Chain** — Every event appended to a tamper-evident cryptographic chain
- **Shamir Secret Sharing (3-of-5)** — Vote results split across 5 officials. Any 3 required to decrypt. No single person can access results alone
- **Air-Gapped Hardware** — WiFi and Bluetooth physically disabled. USB ports epoxy-sealed post-enrollment
- **Time-Locked Session** — RTC module enforces polling hours. Machine auto-locks at session end

### 🖐️ Biometric Layer
- **R307 Fingerprint Sensor** — Hardware UART-based fingerprint matching stored locally in sensor flash
- **Duplicate Vote Blocking** — Every enrolled voter flagged immediately after voting. Second attempt blocked and logged
- **Unknown Fingerprint Rejection** — Unregistered fingerprints cannot proceed to voting screen

### 🧾 Audit Layer
- **Hash Chain Verifier** — Rebuilds entire chain from genesis and verifies every stored hash
- **Vote Count Cross-Check** — Compares voter records against party counters independently
- **Full Audit Report** — Generates signed text report with session statistics and integrity verdict
- **Fraud Event Logging** — Every blocked attempt, unknown scan and anomaly permanently logged

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SOVEREIGN EVM SYSTEM                      │
├──────────────────────┬──────────────────────────────────────┤
│   HARDWARE LAYER     │   SOFTWARE LAYER                      │
│                      │                                       │
│  Raspberry Pi 4      │   main.py ──── voting loop           │
│  R307 FP Sensor ─────┤   fingerprint.py ─ sensor control    │
│  DS3231 RTC ─────────┤   database.py ──── encrypted SQLite  │
│  7" Touchscreen ─────┤   crypto.py ───── AES-256 + SHA-512  │
│  Battery UPS ────────┤   shamir.py ───── 3-of-5 key split   │
│                      │   session.py ──── time lock          │
│  [NO WIFI]           │   audit_verifier.py ─ integrity check │
│  [NO BLUETOOTH]      │   results.py ───── result decryption  │
│  [NO USB]            │                                       │
└──────────────────────┴──────────────────────────────────────┘
```

### Vote Flow

```
VOTER ARRIVES
     │
     ▼
[Fingerprint Scan] ──── No Match ────► BLOCKED + LOGGED
     │
  Match Found
     │
     ▼
[Check has_voted] ──── Already Voted ─► DUPLICATE BLOCKED + LOGGED
     │
  First Time
     │
     ▼
[Party Selection] ──── Cancel ────────► Return to Idle
     │
  Confirmed
     │
     ▼
[Record Vote] → Mark voter → Encrypt counter → Append to hash chain
     │
     ▼
[Print Receipt] → SHA-512 hash on paper (optional)
     │
     ▼
[Reset Machine] → Ready for next voter
```

---

## 🔧 Hardware Setup

### Components Required

| Component | Model | Cost |
|---|---|---|
| Single Board Computer | Raspberry Pi 4 (2GB) | ₹3,500 |
| Fingerprint Sensor | R307 or R503 (UART) | ₹500 |
| Display | 7" HDMI Touchscreen | ₹800 |
| RTC Module | DS3231 (I2C) | ₹150 |
| Battery UPS | Waveshare UPS HAT | ₹600 |
| MicroSD | 32GB Class 10 | ₹300 |

### GPIO Wiring — R307 Fingerprint Sensor

```
Raspberry Pi 4          R307 Sensor
─────────────           ───────────
Pin 1  (3.3V) ────────► VCC  (Red)
Pin 6  (GND)  ────────► GND  (Black)
Pin 8  (TXD)  ────────► RXD  (White)     ← TX goes to RX
Pin 10 (RXD)  ────────► TXD  (Green)     ← RX goes to TX

⚠️  NEVER connect R307 to 5V — sensor will be permanently damaged
```

### GPIO Wiring — DS3231 RTC Module

```
Raspberry Pi 4          DS3231 RTC
─────────────           ──────────
Pin 3  (SDA)  ────────► SDA
Pin 5  (SCL)  ────────► SCL
Pin 4  (5V)   ────────► VCC
Pin 9  (GND)  ────────► GND
```

---

## 🚀 Installation

### Step 1 — Flash Raspberry Pi OS

Download and flash **Raspberry Pi OS Lite (64-bit)** using Raspberry Pi Imager.

### Step 2 — Enable UART and I2C

```bash
sudo raspi-config
# Interface Options → Serial Port → Disable shell, Enable hardware
# Interface Options → I2C → Enable
```

### Step 3 — Disable All Wireless Hardware

```bash
# Add to /boot/config.txt
echo "dtoverlay=disable-wifi" | sudo tee -a /boot/config.txt
echo "dtoverlay=disable-bt"   | sudo tee -a /boot/config.txt

# Disable at OS level
sudo systemctl disable bluetooth
sudo rfkill block all
```

### Step 4 — Clone and Install

```bash
git clone https://github.com/YOUR_USERNAME/sovereign-evm.git
cd sovereign-evm

python3 -m venv venv
source venv/bin/activate

pip install cryptography pyserial adafruit-circuitpython-fingerprint smbus2
```

### Step 5 — Generate Master Key

```bash
python3 -c "
import os
os.makedirs('keys', exist_ok=True)
open('keys/evm.key','wb').write(os.urandom(32))
print('Master key generated.')
"
```

### Step 6 — Initialize and Enroll Voters

```bash
python enroll.py
```

### Step 7 — Split Key Before Election Day

```bash
python results.py
# Choose option 1 — splits key into 5 shares
# Distribute one share to each of 5 officials
# Delete keys/evm.key after splitting
rm keys/evm.key
```

---

## 🗳️ Usage

### Run Voting Session

```bash
python main.py
```

### Admin Panel (During Voting)

Press `A` at the idle screen to access:
- Live vote counts
- Audit log viewer

### Decrypt Results (After Election)

Requires 3 of 5 officials with their share files:

```bash
python auto_results.py
# Enter: 1 2 3  (share numbers of present officials)
```

### Verify Integrity

```bash
python audit_verifier.py
```

Expected output:
```
VERDICT: ELECTION INTEGRITY CONFIRMED

1. HASH CHAIN INTEGRITY     [PASS]  — 47 events verified
2. VOTE COUNT VERIFICATION  [PASS]  — Records match counters
3. VOTER RECORD INTEGRITY   [PASS]  — Zero anomalies
```

---

## 🔐 Security Model

### Threat Model — What This System Defeats

| Attack Vector | How Sovereign EVM Defeats It |
|---|---|
| Impersonation (voting as someone else) | Fingerprint must match enrolled voter |
| Double voting | Voter flagged immediately after first vote |
| Network interception | Zero network hardware — nothing to intercept |
| Database tampering | SHA-512 hash chain detects any modification |
| Insider result manipulation | Shamir 3-of-5 — no single person has full key |
| Physical machine cloning | PUF identity (roadmap) rejects cloned hardware |
| USB attack | All ports epoxy-sealed after enrollment |
| Brute force storage access | AES-256-GCM — computationally infeasible to break |

### Cryptographic Specifications

```
Symmetric Encryption   : AES-256-GCM
Hash Function          : SHA-512
Key Derivation         : 256-bit random (os.urandom)
Secret Sharing         : Shamir (t=3, n=5) over Mersenne prime 2^521-1
Nonce                  : 96-bit random per encryption operation
Authentication Tag     : 128-bit GCM tag
```

---

## 📁 Project Structure

```
sovereign-evm/
│
├── main.py              ← Entry point — voting loop
├── enroll.py            ← Voter enrollment (run before election)
├── results.py           ← Result decryption (run after election)
├── auto_results.py      ← Automatic result decryption from share files
├── audit_verifier.py    ← Hash chain integrity verifier
│
├── crypto.py            ← AES-256-GCM + SHA-512 hash chain
├── database.py          ← Encrypted SQLite operations
├── fingerprint.py       ← R307 sensor control (sim + real Pi mode)
├── session.py           ← Time-locked session management
├── ui.py                ← Terminal voting interface
├── shamir.py            ← Shamir Secret Sharing implementation
│
├── data/
│   ├── voters.db        ← Encrypted SQLite database
│   └── audit_report.txt ← Generated integrity report
│
└── keys/
    ├── evm.key          ← AES master key (DELETE after Shamir split)
    └── shares/
        ├── share_1.txt  ← Returning Officer
        ├── share_2.txt  ← Election Observer
        ├── share_3.txt  ← Opposition Representative
        ├── share_4.txt  ← Presiding Officer
        └── share_5.txt  ← Court Representative
```

---

## 🔬 Research

This project implements and combines the following cryptographic concepts on embedded offline hardware — a combination that does not exist in any prior open-source implementation:

- **Shamir's Secret Sharing** — Blakley (1979), Shamir (1979)
- **AES-GCM Authenticated Encryption** — NIST SP 800-38D
- **Hash Chain Integrity** — Merkle (1979)
- **Air-Gapped System Design** — NSA TEMPEST guidelines

### Cite This Project

```bibtex
@misc{sovereign-evm-2025,
  author    = {Monish},
  title     = {Sovereign EVM: A Zero-Trust Air-Gapped Biometric
               Electronic Voting Machine with Threshold Cryptography},
  year      = {2025},
  publisher = {GitHub},
  url       = {https://github.com/YOUR_USERNAME/sovereign-evm}
}
```

---

## 📜 License

MIT License — free to use, modify and deploy with attribution.

---

## 🙏 Acknowledgements

- Adafruit CircuitPython Fingerprint library
- Python Cryptography library (pyca/cryptography)
- Adi Shamir — for the secret sharing scheme (1979)

---

<div align="center">
Built with purpose. Secured by mathematics. Open to the world.
</div>
