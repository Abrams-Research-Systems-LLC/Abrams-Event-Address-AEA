#![no_main]
//! Arbitrary 136-byte inputs: aea_verify must never panic or crash, and must
//! return one of the documented codes.
use libfuzzer_sys::fuzz_target;
use aea::{aea_verify, AeaRecord};

fuzz_target!(|data: &[u8]| {
    if data.len() < 136 { return; }
    let mut rec: AeaRecord = aea::zeroed();
    unsafe { core::ptr::copy_nonoverlapping(data.as_ptr(), &mut rec as *mut AeaRecord as *mut u8, 136) };
    let rc = unsafe { aea_verify(&rec) };
    assert!(matches!(rc, 0 | 1 | -2 | -3 | -4 | -5 | -6), "undocumented rc {rc}");
});
