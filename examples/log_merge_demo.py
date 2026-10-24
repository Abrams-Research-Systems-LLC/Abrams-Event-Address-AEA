#!/usr/bin/env python3
"""
examples/log_merge_demo.py
Demonstrates multi-platform 4D spacetime log merge, time-scale offset detection,
and memory corruption (SEU / bit-rot) detection.

Physical scenarios:
1. Ground Radar and UAV-Alpha log state in Earth-fixed ITRF2020 on atomic TAI scale.
2. UAV-Bravo mistakenly logs using civil UTC (37 leap seconds behind TAI in 2026).
   - At tactical UAV velocity (25 m/s):  25 m/s * 37 s = 925.0 meters coordinate offset.
   - At orbital spacecraft velocity (7,668.56 m/s): 7,668.56 m/s * 37 s = 283.74 kilometers coordinate offset.
   Downstream sensor fusion without explicit time scale labels misaligns tracks by hundreds of meters to kilometers.
3. A single-event upset (SEU) flips 1 bit in flash memory. AEA-STATE/1 detects corruption immediately.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import aea

def main():
    print("=========================================================================")
    print("  AEA-STATE/1 v1.0.0 — Multi-Platform Log Merge & Corruption Demo        ")
    print("=========================================================================\n")

    print("1. SIMULATING PLATFORM STATE LOGS:")
    # Base instant: 2026-01-01 00:00:00 UTC
    # POSIX UTC seconds = 1,767,225,600
    # In 2026, TAI - UTC = 37 seconds.
    # By ICD rule: seconds since 1970 TAI = POSIX + (TAI - UTC) - 8 = 1,767,225,600 + 37 - 8 = 1,767,225,629
    t_tai = 1767225629
    t_utc_raw = 1767225600

    rec_alpha = {
        "version": 1,
        "body_naif": 399,       # Earth geocenter
        "time_sec": t_tai,
        "time_nsec": 0,
        "frame": 1,             # ITRF2020
        "time_scale": 1,        # TAI
        "pos_m": [3916909.52, 8057.75, 5016918.65],
        "vel_mps": [25.0, 0.0, 0.0],
        "quat_xyzw": [0.0, 0.0, 0.0, 1.0],
    }
    raw_alpha = aea.seal_record(rec_alpha)
    valid_alpha, _, hash_alpha = aea.verify_record(raw_alpha)
    print(f"  [+] UAV-Alpha Record: Sealed {len(raw_alpha)} B | Frame: ITRF2020 | Scale: TAI | SHA-256: {hash_alpha[:16]}... Valid: {valid_alpha}")

    # 2. Time-scale disparity calculation
    print("\n2. TIME-SCALE DISPARITY & FUSION IMPACT:")
    tai_utc_offset = 37  # seconds in 2026
    uav_vel = 25.0       # m/s (tactical drone)
    leo_vel = 7668.558   # m/s (circular LEO 400 km)

    uav_pos_error = uav_vel * tai_utc_offset
    leo_pos_error = leo_vel * tai_utc_offset

    print(f"  [*] Leap second disparity between atomic TAI and civil UTC: {tai_utc_offset} seconds.")
    print(f"      - Position error on tactical UAV cruise (25 m/s):      {uav_pos_error:,.1f} meters")
    print(f"      - Position error on orbital LEO vehicle (7,668.6 m/s): {leo_pos_error/1000:,.2f} kilometers")
    print("  [+] AEA Solution: `time_scale` is an explicit uint16 tag (1=TAI, 2=TT, 3=TCB, 4=TDB).")
    print("      Downstream fusion systems can detect the scale mismatch before merging sensor tracks.\n")

    # 3. Accidental memory corruption detection (Bit-Flip / SEU)
    print("3. ACCIDENTAL CORRUPTION / BIT-FLIP DETECTION:")
    corrupted_data = bytearray(raw_alpha)
    corrupted_data[52] ^= 0x01  # Invert 1 bit in vel_mps[0] double

    valid_c, exp_h, stor_h = aea.verify_record(bytes(corrupted_data))
    print(f"  [*] Injected 1-bit flip at byte offset 52 (vel_mps field)...")
    if not valid_c:
        print(f"  [PASS] AEA verification detected accidental corruption.")
        print(f"         Stored Seal:   {stor_h}")
        print(f"         Computed Hash: {exp_h}")
        print(f"         Result: Corrupted record flagged before consumption by downstream log processing.\n")
    else:
        print(f"  [FAIL] Failed to detect bit flip!\n")

    print("=========================================================================")
    print("  Summary: AEA-STATE/1 provides explicit coordinate and clock tags with   ")
    print("  deterministic corruption detection across heterogeneous systems.        ")
    print("=========================================================================")

if __name__ == "__main__":
    main()
