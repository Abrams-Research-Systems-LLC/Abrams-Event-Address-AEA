# AEA-STATE/1 v1.0.3 — Claims and How to Check Them

This document lists every quantitative and architectural claim made about AEA-STATE/1 v1.0.3, the exact command to reproduce it, and the reference file.

## 1. Specification & Wire Layout
- **Claim:** AEA-STATE/1 is a fixed, naturally aligned 136-byte binary record (`repr(C)`, 8-byte alignment, zero padding).
  - **Command:** `cargo test --test layout`
  - **Verification:** `tests/layout.rs` asserts `std::mem::size_of::<AeaRecord>() == 136`, `align_of == 8`, and verifies all field offsets [0..136).
- **Claim:** Prefix bytes [0, 104) are hashed with SHA-256; negative zero (`-0.0`) is canonicalized to `+0.0`.
  - **Command:** `python tools/aea.py verify tests/kat/cambridge.bin` & `cargo test test_negative_zero`
  - **Verification:** `src/state.rs` (`canon`), `tools/aea.py` (`canon_f64`).
- **Claim:** C ABI exports exactly three public functions: `aea_seal`, `aea_verify`, `aea_version`.
  - **Command:** `cargo build --release` followed by symbol check (`nm -g --defined-only target/release/libaea.a | grep aea_` exports exactly `aea_seal`, `aea_verify`, `aea_version`).
  - **Verification:** `include/aea.h`, `src/lib.rs`.

## 2. Test Vectors & Known-Answer Tests (KAT)
- **Claim:** 14 of 14 automated tests pass on x86_64 host and under big-endian s390x (QEMU).
  - **Command:** `cargo test` (Host: 7 unit + 3 layout + 1 Cambridge KAT + 2 KAT-suite + 1 bitflip = 14 tests).
  - **CI Target:** `cargo test --target s390x-unknown-linux-gnu` (in `.github/workflows/ci.yml`).
- **Claim:** 20 independent Known-Answer Test vectors generated in Python (`hashlib`) match the Rust C-ABI output bit-for-bit.
  - **Command:** `python tools/gen_kat.py --check` & `cargo test --test kat_vectors`
  - **Verification:** `tests/kat/vectors.json`, `tests/kat/vectors.txt`.
- **Claim:** Cambridge KAT digest `9f6cc1096562729a902167fd622e66a264a239f3e9a9d804414659e3ab97800e` matches four independent ways (Rust, C, Python, standalone `sha256sum`).
  - **Command:** `python tools/aea.py verify tests/kat/cambridge.bin` (or `python verify.py` / `./verify.sh`).

## 3. Corruption Detection & Fuzzing
- **Claim:** Single-bit flip corruption detection catches 1,082 out of 1,088 bits flipped across the sealed record (100% of non-zero-sign bits).
  - **Command:** `cargo test --test bitflip`
  - **Explanation:** 136 bytes × 8 = 1,088 bit positions. Exactly 6 bits correspond to IEEE-754 sign bits of fields set to `+0.0`. Since the spec canonicalizes `-0.0` to `+0.0`, those 6 bit flips produce identical hashes by design. All remaining 1,082 bit flips are detected.
- **Claim:** Two cargo-fuzz targets (`verify_bytes`, `seal_roundtrip`) run in public CI with no panics or crashes.
  - **Command:** `cargo +nightly fuzz run verify_bytes -- -max_total_time=60` and `seal_roundtrip`.
  - **Artifacts:** `fuzz/fuzz_targets/verify_bytes.rs`, `fuzz/fuzz_targets/seal_roundtrip.rs`.

## 4. Microcontroller Footprint
- **Claim:** Compiles `#![no_std]` without heap allocation (`0 malloc`) for Arm Cortex-M bare-metal in ~2.3 KB of code plus read-only data (llvm-size text column: .text + .rodata + .ARM.exidx).
  - **Command:**
    - `thumbv6m-none-eabi` (Cortex-M0): 2,329 B
    - `thumbv7em-none-eabihf` (Cortex-M4/M7): 2,315 B
    - `thumbv8m.main-none-eabihf` (Cortex-M33): 2,319 B
  - **Verification:** `test_results/embedded_sizes.txt`, verified in CI via `llvm-size` assertion.

## 5. Scope Boundaries (What it does NOT do)
- AEA-STATE/1 is **TRL 3** (host-verified proof of concept; no flight hardware runs yet).
- It is **not** a navigation engine, filter, or propagator.
- It is **not** a digital signature or authentication envelope (the SHA-256 seal is unkeyed integrity against bit errors and storage corruption; anyone can reseal a record).
- It does **not** bound drift, mitigate GPS denial, or save propellant by itself.
- Authenticated profile is specified separately as a draft (`docs/AEA-AUTH-DRAFT.md`).
