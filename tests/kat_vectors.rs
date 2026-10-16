//! Runs every vector in tests/kat/vectors.txt (generated independently by
//! tools/gen_kat.py using Python hashlib) through the Rust C-ABI.
use aea::{aea_seal, aea_verify, AeaRecord};

const VECTORS: &str = include_str!("kat/vectors.txt");

fn hex(b: &[u8; 32]) -> String {
    b.iter().map(|x| format!("{:02x}", x)).collect()
}
fn unhex(s: &str) -> [u8; 32] {
    let mut o = [0u8; 32];
    for i in 0..32 {
        o[i] = u8::from_str_radix(&s[2 * i..2 * i + 2], 16).unwrap();
    }
    o
}

#[test]
fn kat_vectors_match_python_generator() {
    let mut n = 0;
    for line in VECTORS.lines().filter(|l| !l.starts_with('#') && !l.trim().is_empty()) {
        let t: Vec<&str> = line.split_whitespace().collect();
        assert_eq!(t.len(), 21, "bad line: {line}");
        let f: Vec<f64> = t[8..18].iter().map(|h| f64::from_bits(u64::from_str_radix(h, 16).unwrap())).collect();
        let mut rec = AeaRecord {
            version: t[2].parse().unwrap(),
            body_naif: t[3].parse().unwrap(),
            time_sec: t[4].parse().unwrap(),
            time_nsec: t[5].parse().unwrap(),
            frame: t[6].parse().unwrap(),
            time_scale: t[7].parse().unwrap(),
            pos_m: [f[0], f[1], f[2]],
            vel_mps: [f[3], f[4], f[5]],
            quat_xyzw: [f[6], f[7], f[8], f[9]],
            hash: [0u8; 32],
        };
        let want_rc: i32 = t[18].parse().unwrap();
        match t[1] {
            "seal" => {
                let rc = unsafe { aea_seal(&mut rec) };
                assert_eq!(rc, want_rc, "{}: seal rc", t[0]);
                if rc == 0 {
                    assert_eq!(hex(&rec.hash), t[19], "{}: digest", t[0]);
                    assert_eq!(unsafe { aea_verify(&rec) }, 0, "{}: verify after seal", t[0]);
                } else {
                    assert_eq!(rec.hash, [0u8; 32], "{}: hash must be untouched on error", t[0]);
                }
            }
            "verify" => {
                rec.hash = unhex(t[20]);
                assert_eq!(unsafe { aea_verify(&rec) }, want_rc, "{}: verify rc", t[0]);
            }
            op => panic!("unknown op {op}"),
        }
        n += 1;
    }
    assert_eq!(n, 20, "expected 20 vectors");
}

#[test]
fn committed_cambridge_bin_matches_vector() {
    let bin = include_bytes!("kat/cambridge.bin");
    let line = VECTORS.lines().find(|l| l.starts_with("cambridge_itrf_tai ")).unwrap();
    let want = line.split_whitespace().nth(19).unwrap();
    assert_eq!(hex(bin[104..136].try_into().unwrap()), want);
}
