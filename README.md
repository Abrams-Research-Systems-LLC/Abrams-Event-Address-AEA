# Abrams Event Address (AEA): AEA-STATE/1

[![CI](https://github.com/unlimitedinfinit/Abrams-Event-Address-AEA/actions/workflows/ci.yml/badge.svg)](https://github.com/unlimitedinfinit/Abrams-Event-Address-AEA/actions/workflows/ci.yml)
[![License: MIT OR Apache-2.0](https://img.shields.io/badge/License-MIT%20OR%20Apache--2.0-blue.svg)](LICENSE)

The CI badge above is GitHub's live workflow status, not a static image.

**AEA-STATE/1 is a proposed 136-byte record format.** It tags an estimated state with a frame and a time scale, and protects the record with a SHA-256 integrity digest. The reference implementation is a zero-heap `#![no_std]` Rust library with a C ABI. Version 1.0.0. Readiness is about TRL 3: a lab proof of concept with no hardware or flight demonstration yet.

## What it is
- A fixed, naturally aligned, 136-byte binary record. Its contents are: body (NAIF ID), time (seconds and nanoseconds on a declared time scale), reference frame, position, velocity, and an attitude quaternion. A SHA-256 digest of the first 104 bytes follows.
- A small C-callable library: `aea_seal`, `aea_verify`, `aea_version`, and the optional `aea_quat_check`.
- **Integrity only.** It detects accidental modification such as bit flips, memory or flash corruption, and truncation.

## What it is not
- It is **not authentication.** The digest is unkeyed, so anyone who can modify a record can recompute it. It does not protect against a deliberate attacker or spoofing. An authenticated profile is specified separately as a draft and is not implemented: [docs/AEA-AUTH-DRAFT.md](docs/AEA-AUTH-DRAFT.md).
- It is not a navigation filter, propagator, or frame/time converter. The caller supplies a state that is already expressed in the declared frame and time scale.
- It does not by itself improve GNSS-denied navigation, drift, EW resilience, or spoofing detection. Those are open research questions.
- It is not a ratified standard and it is not certified (DO-178C or otherwise).

## Wire layout (see [docs/ICD.md](docs/ICD.md))
| Offset | Size | Type | Field |
|---:|---:|---|---|
| 0 | 4 | u32 | `version` (=1) |
| 4 | 4 | u32 | `body_naif` (399 Earth, 499 Mars, 0 none) |
| 8 | 8 | i64 | `time_sec`: seconds since 1970-01-01T00:00:00 on the declared scale |
| 16 | 4 | u32 | `time_nsec` (< 1e9) |
| 20 | 2 | u16 | `frame` (1 ITRF2020, 2 GCRS, 3 BCRS, 4 BODY) |
| 22 | 2 | u16 | `time_scale` (1 TAI, 2 TT, 3 TCB, 4 TDB) |
| 24 | 24 | f64[3] | `pos_m` |
| 48 | 24 | f64[3] | `vel_mps` |
| 72 | 32 | f64[4] | `quat_xyzw` (identity = unmeasured; unit norm **not** enforced by seal) |
| 104 | 32 | u8[32] | SHA-256 of the canonical little-endian encoding of bytes [0,104) |

## Verify it yourself
```bash
cargo test                                   # unit, layout, 20 KAT vectors, exhaustive bit-flip test
python3 tools/gen_kat.py --check             # independent Python generator matches committed vectors
python3 tools/aea.py verify tests/kat/cambridge.bin
cargo build --release --target thumbv7em-none-eabihf   # also thumbv6m-none-eabi, thumbv8m.main-none-eabihf
cd examples/c_caller && cargo build --release --manifest-path ../../Cargo.toml && make run
```
Known-answer vectors are listed in `tests/kat/vectors.json` (human-readable) and `tests/kat/vectors.txt` (machine-readable). There are 20 vectors covering all frames and time scales, edge cases, and every error code. The original Cambridge vector is unchanged: `9f6cc1096562729a902167fd622e66a264a239f3e9a9d804414659e3ab97800e`.

## Measured facts (with method)
- `.text` of the AEA object, release + LTO, measured with `llvm-size` on 2026-10-15 (excludes compiler_builtins soft-float helpers): thumbv6m 2,625 B; thumbv7em 2,651 B; thumbv8m.main 2,651 B; 0 B data/bss. The pre-`aea_quat_check` baseline on thumbv7em was 2,315 B.
- Stack usage and cycle counts have **not** been measured yet. They are on the roadmap.
- Big-endian: the tests are wired to run on s390x under QEMU in CI. See CI for status.
- Bit-flip coverage: all 1,088 single-bit flips of the sealed Cambridge record are detected, with 6 documented exceptions. Those 6 are sign flips of fields equal to +0.0, which are canonicalized by design (see `tests/bitflip.rs`).

## Limitations
- Cortex-M4F has a single-precision FPU only, so double-precision handling uses software routines.
- The identity quaternion means both "unmeasured" and "aligned with frame axes". This is a known v1 ambiguity.
- ITRF coordinates are valid at the event epoch only. Comparing across years needs a plate-motion model applied by the user.
- The time rule is: `time_sec` on TAI = POSIX + (TAI−UTC) − 8, where TAI−UTC was about 8 s on 1970-01-01. The worked examples give J2000 equivalents.
- The SHA-256 implementation is not CAVP/CMVP validated.

## Research roadmap (headline)
These are open questions, not capabilities. We plan to investigate:
- an authenticated, sequence-numbered profile;
- whether sealed records help drift detection during GNSS outages;
- whether sealed records support cross-node consistency checks;
- measured embedded cost on Cortex-M/R and LEON.

## Repository layout
`src/` library · `include/aea.h` C header · `tests/` tests and KAT data · `tools/` Python reference decoder, KAT generator, and browser inspector · `fuzz/` cargo-fuzz targets · `examples/c_caller` · `docs/` ICD, scope, and auth draft.

No prebuilt binaries are released at this time. Build from source as shown above.

## License
MIT OR Apache-2.0. Both texts are in [LICENSE](LICENSE).
