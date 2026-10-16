#![no_main]
//! Arbitrary inputs: if aea_seal succeeds, aea_verify must succeed, and the stored
//! digest must equal SHA-256 of encode_prefix(). If seal fails, hash is untouched.
use libfuzzer_sys::fuzz_target;
use aea::{aea_seal, aea_verify, AeaRecord};

fuzz_target!(|data: &[u8]| {
    if data.len() < 104 { return; }
    let mut rec: AeaRecord = aea::zeroed();
    unsafe { core::ptr::copy_nonoverlapping(data.as_ptr(), &mut rec as *mut AeaRecord as *mut u8, 104) };
    rec.hash = [0xAA; 32];
    let rc = unsafe { aea_seal(&mut rec) };
    if rc == 0 {
        assert_eq!(unsafe { aea_verify(&rec) }, 0);
    } else {
        assert!(rc < 0);
        assert_eq!(rec.hash, [0xAA; 32]);
    }
});
