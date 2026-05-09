import random
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
