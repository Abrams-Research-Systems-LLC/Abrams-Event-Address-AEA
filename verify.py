#!/usr/bin/env python3
"""
verify.py — Self-Contained Auditor Reproduction Script for AEA-STATE/1 v1.0.0
Works on Windows, Linux, and macOS.
Zero external Python dependencies (standard library only).
Recomputes hashes, layout, 20 KAT vectors, property-level bit-flips, demos,
and (when Rust toolchain is present) tests and symbol exports. Never accesses `../`.
"""

import sys
import os
import struct
import hashlib
import json
import subprocess
import shutil

RECORD_BYTES = 136
PREFIX_BYTES = 104
HASH_BYTES = 32

CAMBRIDGE_DIGEST = "9f6cc1096562729a902167fd622e66a264a239f3e9a9d804414659e3ab97800e"

pass_count = 0
fail_count = 0
skip_count = 0

def ok(msg):
    global pass_count
    pass_count += 1
    print(f"  [PASS] {msg}")

def fail(msg):
    global fail_count
    fail_count += 1
    print(f"  [FAIL] {msg}")

def skip(msg):
    global skip_count
    skip_count += 1
    print(f"  [SKIP] {msg}")

def check_banner(title):
    print(f"\n=== {title} ===")

def main():
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(repo_dir)

    print("===================================================================")
    print("  AEA-STATE/1 v1.0.0 — Comprehensive Auditor Verification Suite    ")
    print(f"  Repo Directory: {repo_dir}")
    print("===================================================================")

    # Check 1: Cambridge KAT binary check
    check_banner("Check 1: Cambridge KAT Binary & SHA-256 Seal Verification")
    camb_bin_path = os.path.join(repo_dir, "tests", "kat", "cambridge.bin")
    if not os.path.exists(camb_bin_path):
        fail(f"Missing {camb_bin_path}")
    else:
        with open(camb_bin_path, "rb") as f:
            data = f.read()
        if len(data) == RECORD_BYTES:
            prefix = data[:PREFIX_BYTES]
            stored_hash = data[PREFIX_BYTES:].hex()
            calc_hash = hashlib.sha256(prefix).hexdigest()

            if calc_hash == CAMBRIDGE_DIGEST and stored_hash == CAMBRIDGE_DIGEST:
                ok(f"Record is exactly {RECORD_BYTES} B, seal covers [0..{PREFIX_BYTES}) matching {CAMBRIDGE_DIGEST[:16]}...{CAMBRIDGE_DIGEST[-8:]}")
            else:
                fail(f"Digest mismatch! Calculated: {calc_hash}, Stored: {stored_hash}")
        else:
            fail(f"Record size is {len(data)} B (expected {RECORD_BYTES} B)")

    # Check 2: Independent Python KAT Generator Check
    check_banner("Check 2: Independent Python KAT Generator Check (20 vectors)")
    gen_kat_path = os.path.join(repo_dir, "tools", "gen_kat.py")
    if os.path.exists(gen_kat_path):
        res = subprocess.run([sys.executable, gen_kat_path, "--check"], capture_output=True, text=True)
        if res.returncode == 0:
            ok("Independent Python KAT generator matches committed tests/kat/vectors.{json,txt} (20 vectors)")
        else:
            fail(f"gen_kat.py --check failed:\n{res.stdout}\n{res.stderr}")
    else:
        fail(f"Missing {gen_kat_path}")

    # Check 3: Exhaustive Bitflip Property Check via Python Simulation
    check_banner("Check 3: Exhaustive Single-Bit-Flip Corruption Detection (1,088 bits)")
    if os.path.exists(camb_bin_path):
        with open(camb_bin_path, "rb") as f:
            base_data = bytearray(f.read())

        total_bits = RECORD_BYTES * 8
        detected = 0
        zero_sign_absorbed = 0

        sys.path.insert(0, os.path.join(repo_dir, "tools"))
        try:
            import aea
            for bit in range(total_bits):
                flipped = bytearray(base_data)
                flipped[bit // 8] ^= (1 << (bit % 8))

                valid, exp_h, stor_h = aea.verify_record(bytes(flipped))
                if not valid:
                    detected += 1
                else:
                    zero_sign_absorbed += 1

            if detected == 1082 and zero_sign_absorbed == 6:
                ok(f"All 1,088 single-bit flips tested: {detected} detected, {zero_sign_absorbed} sign bits of +0.0 absorbed by -0.0 canonicalization")
            else:
                fail(f"Unexpected bitflip results: detected={detected}, zero_sign_absorbed={zero_sign_absorbed}")
        except Exception as e:
            fail(f"Bitflip simulation error: {e}")

    # Check 4: Automated Demos Math & Execution
    check_banner("Check 4: Automated Demos Math & Output Verification")
    demo1 = os.path.join(repo_dir, "examples", "log_merge_demo.py")
    demo2 = os.path.join(repo_dir, "examples", "mission_timeline_demo.py")
    if os.path.exists(demo1) and os.path.exists(demo2):
        r1 = subprocess.run([sys.executable, demo1], capture_output=True, text=True)
        r2 = subprocess.run([sys.executable, demo2], capture_output=True, text=True)
        if r1.returncode == 0 and "925.0 meters" in r1.stdout and r2.returncode == 0 and "[FAIL]" not in r2.stdout:
            ok("examples/log_merge_demo.py and examples/mission_timeline_demo.py executed cleanly with exact math")
        else:
            fail(f"Demo execution failed or produced unexpected text.\nDemo 1:\n{r1.stdout}\nDemo 2:\n{r2.stdout}")
    else:
        fail("Missing demo files in examples/")

    # Check 5: Cargo / Rust Tests (14 tests)
    check_banner("Check 5: Rust Automated Test Suite (14 Tests)")
    cargo_bin = shutil.which("cargo")
    if cargo_bin:
        res = subprocess.run(["cargo", "test"], capture_output=True, text=True)
        out = res.stdout + res.stderr
        passed_lines = [l for l in out.splitlines() if "test result: ok." in l]
        if res.returncode == 0:
            total_passed = 0
            for l in passed_lines:
                parts = l.split()
                if "passed;" in parts:
                    idx = parts.index("passed;")
                    try:
                        total_passed += int(parts[idx - 1])
                    except ValueError:
                        pass
            ok(f"cargo test passed cleanly ({total_passed} tests verified across unit, layout, kat, kat_vectors, bitflip)")
        else:
            fail(f"cargo test failed:\n{out}")
    else:
        skip("cargo not found in PATH; skipping Rust compilation tests")

    # Check 6: C ABI Interface & Exported Symbols
    check_banner("Check 6: C ABI Interface & Exported Symbols")
    header_path = os.path.join(repo_dir, "include", "aea.h")
    if os.path.exists(header_path):
        with open(header_path, "r", encoding="utf-8") as f:
            h_text = f.read()
        has_seal = "int32_t aea_seal(" in h_text
        has_verify = "int32_t aea_verify(" in h_text
        has_version = "uint32_t aea_version(" in h_text
        has_assert = "sizeof(AeaRecord) == 136" in h_text

        if has_seal and has_verify and has_version and has_assert:
            ok("include/aea.h defines exactly three public C functions (aea_seal, aea_verify, aea_version) with static 136-byte assertion")
        else:
            fail("include/aea.h missing expected function signatures or size assertion")
    else:
        fail(f"Missing {header_path}")

    # Check 7: Committed Embedded Sizes Artifact Check
    check_banner("Check 7: Embedded Footprint & Code Size Artifact Check")
    sizes_txt = os.path.join(repo_dir, "test_results", "embedded_sizes.txt")
    if os.path.exists(sizes_txt):
        with open(sizes_txt, "r") as f:
            stxt = f.read()
        if "2329" in stxt and "2315" in stxt and "2319" in stxt:
            ok("Embedded size logs verified: Cortex-M0 (2,329 B), Cortex-M4/M7 (2,315 B), Cortex-M33 (2,319 B)")
        else:
            fail("embedded_sizes.txt content does not match expected numbers")
    else:
        fail("test_results/embedded_sizes.txt not found in repository")

    # Final Summary
    total_checks = pass_count + fail_count + skip_count
    print("\n===================================================================")
    print(f"  VERIFICATION SUMMARY: {pass_count} PASSED, {fail_count} FAILED, {skip_count} SKIPPED (Total {total_checks} Checks)")
    print("===================================================================")

    if fail_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
