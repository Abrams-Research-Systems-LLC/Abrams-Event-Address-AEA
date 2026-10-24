#!/usr/bin/env python3
"""
examples/mission_timeline_demo.py
Demonstrates 4D spacetime event tagging across a multi-stage mission timeline:
Launch Pad (ITRF2020) -> Earth Orbit (GCRS) -> Interplanetary (BCRS) -> Mars Touchdown (BODY/499)

Clarification: AEA does NOT perform frame transformations internally (the host navigation
stack performs orbital mechanics and coordinate transformations). AEA provides the unambiguous,
standardized 136-byte record format that binds body, time scale, reference frame, kinematic state,
and SHA-256 seal together into an unbroken, cross-verifiable mission timeline.

Vectors 1, 2, 3, 4 match the committed Known-Answer Test suite in tests/kat/vectors.json.
NASA/JPL published Perseverance landing coordinates at Jezero Crater are cited for Stage 4.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import aea

def main():
    print("=========================================================================")
    print("  AEA-STATE/1 v1.0.0 — Multi-Regime 4D Spacetime Timeline Demonstration  ")
    print("=========================================================================\n")

    events = [
        {
            "stage": "1. Launch Pad (Cambridge / Hawking 2009 KAT Benchmark)",
            "body_naif": 399,
            "body_name": "Earth Geocenter",
            "frame": 1,
            "frame_name": "ITRF2020 (Earth-fixed)",
            "time_scale": 1,
            "time_scale_name": "TAI",
            "time_sec": 1246190426,
            "pos_m": [3916909.5232774816, 8057.749278632174, 5016918.648210711],
            "vel_mps": [0.0, 0.0, 0.0],
            "quat_xyzw": [0.0, 0.0, 0.0, 1.0],
            "expected_hash": "9f6cc1096562729a902167fd622e66a264a239f3e9a9d804414659e3ab97800e",
            "note": "Fixed to Earth crust; WGS84 ECEF coordinates tagged ITRF2020."
        },
        {
            "stage": "2. Low Earth Orbit Insertion (400 km circular)",
            "body_naif": 399,
            "body_name": "Earth Geocenter",
            "frame": 2,
            "frame_name": "GCRS (Geocentric Celestial Reference System)",
            "time_scale": 1,
            "time_scale_name": "TAI",
            "time_sec": 1767225629,
            "pos_m": [6778137.0, 0.0, 0.0],
            "vel_mps": [0.0, 7668.558, 0.0],
            "quat_xyzw": [0.0, 0.0, 0.0, 1.0],
            "expected_hash": "92a189cfc2965c11b2ba720dcf5943db59b6f595e76307d1a10203d44fce083e",
            "note": "Geocentric inertial frame; circular orbital speed 7.67 km/s."
        },
        {
            "stage": "3. Solar System Transit (Earth BCRS state at J2000 epoch)",
            "body_naif": 0,
            "body_name": "None (Solar System Barycentric Frame)",
            "frame": 3,
            "frame_name": "BCRS (Barycentric Celestial Reference System)",
            "time_scale": 4,
            "time_scale_name": "TDB (Barycentric Dynamical Time)",
            "time_sec": 946728024,
            "pos_m": [-2.60e10, 1.33e11, 5.77e10],
            "vel_mps": [-29800.0, -4900.0, -2100.0],
            "quat_xyzw": [0.0, 0.0, 0.0, 1.0],
            "expected_hash": "93abf455b19b19f5ee13165788866284c10630d22f92372fbf5ffd9e3f3e78f9",
            "note": "Illustrative Earth barycentric position at J2000 TDB; body_naif 0 = none."
        },
        {
            "stage": "4. Mars Touchdown (NASA/JPL Perseverance Site at Jezero Crater)",
            "body_naif": 499,
            "body_name": "Mars Center of Mass",
            "frame": 4,
            "frame_name": "BODY (Mars Body-Fixed Frame)",
            "time_scale": 1,
            "time_scale_name": "TAI",
            "time_sec": 1613681729,
            "pos_m": [699891.6562040435, 3144227.5362901785, 1061717.149665193],
            "vel_mps": [0.0, 0.0, 0.0],
            "quat_xyzw": [0.0, 0.0, 0.0, 1.0],
            "expected_hash": "fbf55d85008816a7eb51f627b1472a66d94a965bd0eca630c26513ff4da2f5a7",
            "note": "Jezero Crater 18.4447 N, 77.4508 E, h=-2570 m on IAU2000 Mars ellipsoid (NASA/JPL)."
        }
    ]

    for ev in events:
        rec = {
            "version": 1,
            "body_naif": ev["body_naif"],
            "time_sec": ev["time_sec"],
            "time_nsec": 0,
            "frame": ev["frame"],
            "time_scale": ev["time_scale"],
            "pos_m": ev["pos_m"],
            "vel_mps": ev["vel_mps"],
            "quat_xyzw": ev["quat_xyzw"]
        }
        sealed = aea.seal_record(rec)
        valid, exp_h, stor_h = aea.verify_record(sealed)

        match_expected = (stor_h == ev["expected_hash"])
        status = "[SEAL VERIFIED & KAT MATCH]" if (valid and match_expected) else "[FAIL]"

        print(f"EVENT: {ev['stage']}")
        print(f"  Body:       NAIF ID {ev['body_naif']} ({ev['body_name']})")
        print(f"  Frame:      Enum {ev['frame']} -> {ev['frame_name']}")
        print(f"  Clock:      Enum {ev['time_scale']} -> {ev['time_scale_name']} (t={ev['time_sec']} s)")
        print(f"  Position:   [{ev['pos_m'][0]:,.2f}, {ev['pos_m'][1]:,.2f}, {ev['pos_m'][2]:,.2f}] m")
        print(f"  Velocity:   [{ev['vel_mps'][0]:.2f}, {ev['vel_mps'][1]:.2f}, {ev['vel_mps'][2]:.2f}] m/s")
        print(f"  SHA-256:    {stor_h}")
        print(f"  Status:     {status}")
        print(f"  Context:    {ev['note']}\n")

    print("=========================================================================")
    print("  Conclusion: A unified 136-byte event format providing explicit         ")
    print("  coordinates, epochs, and seals across planetary and deep space regimes. ")
    print("=========================================================================")

if __name__ == "__main__":
    main()
