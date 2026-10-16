//! Exhaustive single-bit-flip test over all 1088 bits of the sealed Cambridge record.
//! Every flip must be detected (verify != AEA_OK), EXCEPT flipping the sign bit of a
//! field whose value is +0.0: -0.0 is canonicalized to +0.0 by design (ICD 2.1 rule 2),
//! so that flip is intentionally invisible. The test asserts exactly that and counts them.
use aea::{aea_seal, aea_verify, AeaRecord, AEA_OK};
use core::mem::size_of;

fn cambridge() -> AeaRecord {
    let mut r = aea::zeroed();
    r.body_naif = 399;
    r.time_sec = 1246190426;
    r.pos_m = [3916909.5232774816, 8057.749278632174, 5016918.648210711];
    assert_eq!(unsafe { aea_seal(&mut r) }, AEA_OK);
    r
}

#[test]
fn every_single_bit_flip_is_detected_except_zero_sign() {
    assert_eq!(size_of::<AeaRecord>(), 136);
    let base = cambridge();
    let (mut detected, mut zero_sign) = (0, 0);
    for byte in 0..136usize {
        for bit in 0..8u8 {
            let mut r = base;
            unsafe { *(&mut r as *mut AeaRecord as *mut u8).add(byte) ^= 1 << bit };
            let rc = unsafe { aea_verify(&r) };
            if rc != AEA_OK {
                detected += 1;
                continue;
            }
            // Undetected: must be the sign bit (bit 63) of an f64 field holding +0.0.
            assert!(byte >= 24 && byte < 104, "undetected flip outside float area: byte {byte} bit {bit}");
            let fidx = (byte - 24) / 8;
            let in_field = byte - 24 - fidx * 8;
            let sign_byte = if cfg!(target_endian = "little") { 7 } else { 0 }; // in-memory struct is native-endian
            assert!(in_field == sign_byte && bit == 7, "undetected non-sign flip at byte {byte} bit {bit}");
            let vals = [base.pos_m[0], base.pos_m[1], base.pos_m[2], base.vel_mps[0], base.vel_mps[1], base.vel_mps[2],
                        base.quat_xyzw[0], base.quat_xyzw[1], base.quat_xyzw[2], base.quat_xyzw[3]];
            assert_eq!(vals[fidx].to_bits(), 0, "sign flip of nonzero value went undetected");
            zero_sign += 1;
        }
    }
    // Cambridge has 6 zero-valued floats (vel x3, quat x,y,z) -> 6 benign sign flips.
    assert_eq!(zero_sign, 6);
    assert_eq!(detected, 136 * 8 - 6);
}
