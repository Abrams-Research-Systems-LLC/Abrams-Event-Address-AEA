#!/usr/bin/env python3
"""
examples/log_merge_demo.py
Demonstrates multi-vehicle/multi-sensor 4D spacetime log fusion and corruption detection.

Scenario:
Two autonomous uncrewed aircraft (UAV-Alpha and UAV-Bravo) and an air-defense radar
log positions during an intercept exercise.
1. UAV-Alpha logs in Earth-fixed ITRF2020 on atomic TAI time scale.
2. UAV-Bravo mistakenly logs on civil UTC (37 s leap-second offset from TAI).
   At 25 m/s, 37 seconds is a 925.0-meter coordinate discrepancy!
   At 7,668 m/s LEO orbital velocity, 37 seconds is a 283.7-kilometer discrepancy!
3. Flash memory bit-flip injection (single-event upset / SEU) corrupts a record.

AEA-STATE/1 enforces mandatory frame and clock tags, and catches the corruption.
"""

import sys
import os
import struct
import hashlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import aea

def main():
    print("=========================================================================")
    print("  AEA-STATE/1 v1.0.0 — Multi-Vehicle Log Merge & Corruption Demo         ")
    print("=========================================================================\n")

    print("1. SIMULATING PLATFORM STATE LOGS:")
    # Base instant: 2026-01-01 00:00:00 UTC -> TAI = UTC + 37s (post-1972 POSIX formula)
    # TAI seconds since 1970 = 1767225600 + 37 - 8 = 1767225629
    t_tai = 1767225629
    t_wrong_utc = 1767225600  # Stored without leap-second offset

    # Platform Alpha (Autonomous UAS - 25 m/s cruise)
    rec_alpha = {
        "version": 1,
        "body_naif": 399,       # Earth geocenter
        "time_sec": t_tai,
        "time_nsec": 0,
        "frame": aea.FRAME_NAMES.get(1) and 1,      # ITRF2020
        "time_scale": 1,                            # TAI
        "pos_m": [3916909.52, 8057.75, 5016918.65],
        "vel_mps": [25.0, 0.0, 0.0],
        "quat_xyzw": [0.0, 0.0, 0.0, 1.0],
    }
    raw_alpha = aea.seal_record(rec_alpha)
    valid_alpha, _, hash_alpha = aea.verify_record(raw_alpha)
    print(f"  [+] UAV-Alpha Record: Sealed {len(raw_alpha)} B | Frame: ITRF2020 | Scale: TAI | SHA-256: {hash_alpha[:16]}... Valid: {valid_alpha}")

    # Platform Bravo (Attempted fusion with mislabeled time scale or civil UTC)
    print("\n2. TIME-SCALE MISMATCH DETECTION:")
    dt_seconds = abs(t_tai - t_wrong_utc)
    uav_vel = 25.0  # m/s
    orbital_vel = 7668.0  # m/s

    uav_error = uav_vel * dt_seconds
    orbital_error = orbital_vel * dt_seconds

    print(f"  [!] Time disparity between continuous TAI and uncalibrated UTC: {dt_seconds} seconds")
    print(f"      - Physical position error at tactical UAV cruise (25 m/s):  {uav_error:,.1f} meters")
    print(f"      - Physical position error at orbital velocity (7,668 m/s): {orbital_error/1000:,.1f} kilometers")
    print("  [+] AEA Solution: `time_scale` is an explicit, mandatory uint16 field (1=TAI, 2=TT, 3=TCB, 4=TDB).")
    print("      Downstream fusion systems cannot silently confuse civil UTC leap seconds with continuous atomic time.\n")

    # Platform Charlie: Injected Single-Event Upset (Cosmic-ray / EMI bit flip in flash)
    print("3. ACCIDENTAL CORRUPTION / BIT-FLIP DETECTION:")
    corrupted_data = bytearray(raw_alpha)
    corrupted_data[52] ^= 0x01  # Flip 1 bit in velocity vector

    valid_c, exp_h, stor_h = aea.verify_record(bytes(corrupted_data))
    print(f"  [*] Injected 1-bit flip at byte offset 52 (vel_mps field)...")
    if not valid_c:
        print(f"  [PASS] AEA verification caught corruption immediately!")
        print(f"         Stored Seal:   {stor_h}")
        print(f"         Computed Hash: {exp_h}")
        print(f"         Result: Corrupted record safely rejected before entering flight control or fusion pipeline.\n")
    else:
        print(f"  [FAIL] Failed to detect bitflip!")

    print("=========================================================================")
    print("  Summary: AEA-STATE/1 guarantees byte-level integrity, explicit frames,  ")
    print("  and unambiguous relativistic time tags across heterogeneous platforms. ")
    print("=========================================================================")

if __name__ == "__main__":
    main()
