# AEA-AUTH/1: authenticated profile (DRAFT, NOT IMPLEMENTED)

> **Status: DRAFT for discussion. Nothing in this document is implemented, tested, or interoperable.** AEA-AUTH/1 is a **separate future profile**; it is never part of AEA-STATE/1, and STATE/1 records stay exactly 136 bytes with an unkeyed integrity hash. Any uncertainty (covariance) sidecar would likewise be a separate future profile, never part of STATE/1. It does not change AEA-STATE/1 v1.0.0. Field sizes, algorithms, and codes may change. No security claim may be made for AEA until this profile is implemented with published test vectors and reviewed independently.

## 1. Problem
The AEA-STATE/1 digest is unkeyed SHA-256. It detects storage and transmission corruption, but an adversary who can modify a record can recompute the digest. AEA-AUTH/1 adds three things:
- sender authentication;
- integrity against deliberate modification;
- replay detection.

It does not provide confidentiality.

## 2. Design rules
1. **Wrap, don't modify.** The 136-byte AEA-STATE/1 record is carried unchanged inside the envelope, and its SHA-256 still verifies.
2. **Version separation.** An envelope has its own magic and version. A v1.0.0 consumer never mistakes an envelope for a bare record.
3. **Algorithm agility by suite ID, not negotiation.** A receiver is configured with an allowed suite and key set, and rejects everything else.
4. Use standard primitives only, each with its own test vectors:
   - HMAC-SHA256 per RFC 2104 / FIPS 198-1, tested against RFC 4231 vectors;
   - Ed25519 per RFC 8032, tested against the RFC 8032 §7.1 vectors.

## 3. Envelope layout (little-endian, proposed)
| Off | Size | Field | Notes |
|---:|---:|---|---|
| 0 | 4 | `magic` = `"AEAA"` | |
| 4 | 2 | `env_version` = 1 | |
| 6 | 2 | `suite` | 1 = HMAC-SHA256-256, 2 = HMAC-SHA256-128 (truncated), 3 = Ed25519 |
| 8 | 8 | `sender_id` | Opaque platform/node ID assigned by the deployment |
| 16 | 4 | `key_id` | Identifies the key or key epoch for rotation |
| 20 | 4 | `flags` | Reserved, must be 0 |
| 24 | 8 | `seq` | Monotonic per (`sender_id`, `key_id`). Never reused. Starts at 1. |
| 32 | 136 | `record` | An AEA-STATE/1 record whose SHA-256 must already verify |
| 168 | 16, 32, or 64 | `tag` | MAC (suites 1/2) or signature (suite 3) over bytes [0,168) |

Total sizes are 184 B (suite 2), 200 B (suite 1), and 232 B (suite 3).

## 4. Receiver procedure (proposed)
1. Check the length, `magic`, `env_version`, and that `suite` is allowed. Check `flags == 0`.
2. Look up the key by (`sender_id`, `key_id`) and reject unknown keys.
3. Verify the tag over [0,168), using constant-time comparison for MACs.
4. Run `aea_verify(record)`; it must return `AEA_OK`.
5. Replay check: require `seq > last_seq[sender_id, key_id]`, or use a sliding window of W (e.g. 64) for links that may reorder. Accept the envelope, then update `last_seq`.
6. Optionally, check freshness by comparing `record.time` against local time within the deployment tolerance. This needs a trusted local clock.

## 5. Key management (out of scope; deployment must specify)
- HMAC suites use pre-shared symmetric keys. Any key holder can forge messages from any other holder of the same key, so use per-link keys.
- Ed25519 needs public-key distribution and revocation.
- After a reboot, the sequence counter must be persisted or the key epoch advanced. Otherwise a reset counter enables replay.

## 6. Open questions
- Is truncated HMAC-128 acceptable for the target links?
- What do ground and air links each need in terms of cost? To be measured; see the H5 plan.
- Should the record's time scale and frame be bound into policy (for example, rejecting BCRS from an air node)?
- Should there be a compact profile for low-bandwidth links, for example float32 or delta encoding?

## 7. Implementation acceptance criteria (before any claim)
- [ ] Implemented behind a cargo feature `auth`, off by default, with no change to the v1.0.0 code paths.
- [ ] RFC 4231 and RFC 8032 vectors pass, plus at least 10 AEA-AUTH envelope KATs generated independently in Python.
- [ ] Negative tests cover bad tag, wrong key_id, replayed seq, reordered seq outside the window, truncated envelope, and a non-verifying inner record.
- [ ] Fuzz targets for envelope parsing.
- [ ] Measured cycles, stack, and code size on Cortex-M4/M7.
- [ ] Independent security review.
