# Changelog

All notable changes to the Abrams Event Address (AEA) project are documented in this file.

## [1.0.3] - Unreleased (draft)

### Summary
Reproducibility and packaging fixes. No change to the AEA-STATE/1 record format, the C ABI, or the measured code sizes (2,329 B / 2,315 B / 2,319 B).

### Fixed
- **Line endings**: Added `.gitattributes` forcing LF for all text files. The published `aea-1.0.2.tar.gz` asset was built on Windows and contains CRLF line endings, so it is not byte-identical to `git archive v1.0.2`, and `verify.sh` from that tarball fails under bash on Linux. The v1.0.2 asset is left unchanged because its hash is published; use a v1.0.3 archive or `git archive v1.0.2` instead.
- **verify.sh**: Now committed with mode 100755, so `./verify.sh` runs directly.
- **CI fuzz job**: Pinned to `nightly-2026-10-01` instead of the floating `nightly`. `cargo-fuzz` is still installed at its latest version, so fuzz runs are smoke tests, not bit-for-bit reproducible.

### Added
- `tools/make_release.sh TAG [OUTDIR]`: builds `aea-<version>.tar.gz` with `git archive --prefix=aea-<version>/` and writes `SHA256SUMS`.

### Note on Tag History (complete)
Before tags were frozen, two of them were moved:
- `v1.0.0` was first created, then re-pointed as a lightweight tag (to `1cdf414`), then re-created as annotated tag object `eaa1fb2` on commit `d2bbe24`, where it now stays.
- `v1.0.1` was first placed on `961454b`, then re-pointed to `45787dc`, where it now stays.
- `v1.0.2` (`19a34e0`) has not been moved.
From v1.0.2 onward, tags are never moved; any correction ships as a new version.

### Notes
- `test_results/*.txt` are developer-environment runs from Oct 15, 2026 (before v1.0.0) and contain local absolute paths. CI logs on the tagged commit are the reference.

---

## [1.0.2] - 2026-10-24

### Summary
Submittable evaluation baseline release resolving packaging, documentation, and verification feedback.

### Changed
- **Technical Brief**: Updated document header to "Authoritative Technical Brief · October 2026 · Evaluation Baseline"; removed superseded draft and prior-contact notices across all 35 packages.
- **DARPA Cover Letter**: Softened state record wording to "byte-exact, checkable 4D spacetime state record format designed to reduce frame and time-scale ambiguity".
- **Documentation & CI Size Labels**: Relabeled embedded size metrics in `README.md`, `verify.sh`, and `ci.yml` from `.text` to "code plus read-only data (llvm-size text column)" to accurately describe the 2,329 B / 2,315 B / 2,319 B measurements.
- **Verification Suite (`verify.py`)**: Enhanced Check 7 to actively measure and assert Berkeley text for all installed Cortex-M targets: Cortex-M0 (2,329 B), Cortex-M4/M7 (2,315 B), and Cortex-M33 (2,319 B).
- **Release Assets**: Generated and published full source archive `aea-1.0.2.tar.gz` and updated `SHA256SUMS` to cover all release artifacts.

---

## [1.0.1] - 2026-10-24

### Note on Tag History
During release preparation on October 24, 2026, the `v1.0.1` tag was initially placed at commit `961454b` and subsequently re-pointed to `45787dc` (at approximately 17:40 MDT) to include active Berkeley text measurement, rustup environment guarding, and Mars areoid datum documentation. Tags `v1.0.0` and `v1.0.1` are now frozen at their respective commits (`d2bbe24` and `45787dc`), and all submission packages target release `v1.0.2`.

### Changed
- Replaced LICENSE-APACHE text with exact upstream text from apache.org.
- Restored dual-license links in `README.md` to point directly to `LICENSE-MIT` and `LICENSE-APACHE`.
- Updated `SHA256SUMS` to calculate checksums across full files rather than record prefix slices.
- Guarded `verify.py` against environments lacking `rustup` so cargo-only environments report clean skips.
- Annotated Mars elevation reference datum in timeline demo, KAT generator, and vectors.

---

## [1.0.0] - 2026-10-24

### Summary
Initial baseline specification and reference implementation, now at commit `d2bbe24`. Note: this tag was moved before tags were frozen; see the tag history under 1.0.3.

### Added
- Fixed 136-byte `AEA-STATE/1` data structure with little-endian canonical prefix and SHA-256 integrity digest.
- `#![no_std]`, zero-dependency, zero-heap Rust library exporting three C-ABI functions (`aea_seal`, `aea_verify`, `aea_version`).
- 20-vector known-answer test (KAT) suite and original Cambridge known-answer test vector.
- Independent Python reference validator and browser-based inspector.
- Continuous integration matrix covering x86_64, QEMU s390x big-endian, Cortex-M0/M4/M33 bare metal, and cargo-fuzz smoke tests.
