#!/usr/bin/env python3
"""Independent KAT generator for AEA-STATE/1 (Python stdlib only).

This deliberately does NOT call the Rust library. It re-implements validation
and prefix encoding from docs/ICD.md and hashes with hashlib.sha256, then writes:
  tests/kat/vectors.txt   machine-readable (consumed by tests/kat_vectors.rs)
  tests/kat/vectors.json  human-readable
Run:  python3 tools/gen_kat.py          (write)
      python3 tools/gen_kat.py --check  (fail if committed files differ)
"""
import hashlib, json, math, struct, sys, os

OK, MISMATCH = 0, 1
E_VERSION, E_NSEC, E_FRAME, E_SCALE, E_NONFINITE = -2, -3, -4, -5, -6
ITRF, GCRS, BCRS, BODY = 1, 2, 3, 4
TAI, TT, TCB, TDB = 1, 2, 3, 4

def canon(x): return 0.0 if x == 0.0 else x

def validate(r):
    if r["version"] != 1: return E_VERSION
    if r["time_nsec"] >= 1_000_000_000: return E_NSEC
    if not 1 <= r["frame"] <= 4: return E_FRAME
    if not 1 <= r["time_scale"] <= 4: return E_SCALE
    if any(not math.isfinite(x) for x in r["pos_m"] + r["vel_mps"] + r["quat_xyzw"]): return E_NONFINITE
    return OK

def prefix(r):
    b = struct.pack("<IIqIHH", r["version"], r["body_naif"], r["time_sec"], r["time_nsec"], r["frame"], r["time_scale"])
    b += struct.pack("<10d", *[canon(x) for x in r["pos_m"] + r["vel_mps"] + r["quat_xyzw"]])
    assert len(b) == 104
    return b

def geodetic_to_xyz(lat, lon, h, a, f):
    e2 = f * (2 - f); la, lo = math.radians(lat), math.radians(lon)
    n = a / math.sqrt(1 - e2 * math.sin(la) ** 2)
    return [(n + h) * math.cos(la) * math.cos(lo), (n + h) * math.cos(la) * math.sin(lo), (n * (1 - e2) + h) * math.sin(la)]

def tai_sec_from_utc_posix(posix, tai_minus_utc):
    # ICD rule: seconds since 1970-01-01T00:00:00 TAI = POSIX + (TAI-UTC) - 8  (TAI-UTC was ~8 s at 1970-01-01)
    return posix + tai_minus_utc - 8

def base(**kw):
    r = dict(version=1, body_naif=399, time_sec=0, time_nsec=0, frame=ITRF, time_scale=TAI,
             pos_m=[0.0, 0.0, 0.0], vel_mps=[0.0, 0.0, 0.0], quat_xyzw=[0.0, 0.0, 0.0, 1.0])
    r.update(kw); return r

CAMB = dict(time_sec=1246190426, pos_m=[3916909.5232774816, 8057.749278632174, 5016918.648210711])
# Mars, Jezero (Perseverance) 18.4447 N, 77.4508 E, h=-2570 m, on IAU2000 Mars ellipsoid a=3396190 m, b=3376200 m
MARS_A, MARS_B = 3396190.0, 3376200.0
JEZERO = geodetic_to_xyz(18.4447, 77.4508, -2570.0, MARS_A, (MARS_A - MARS_B) / MARS_A)

V = [  # (name, op, record, note[, stored_hash_override])
    ("cambridge_itrf_tai", "seal", base(**CAMB), "Original repo KAT (must equal 9f6cc109...)"),
    ("cambridge_itrf_tt", "seal", base(**{**CAMB, "time_sec": CAMB["time_sec"] + 32, "time_nsec": 184_000_000, "time_scale": TT}),
     "Same instant on TT (TT = TAI + 32.184 s)"),
    ("leo_gcrs_tai", "seal", base(time_sec=tai_sec_from_utc_posix(1767225600, 37), frame=GCRS, pos_m=[6778137.0, 0.0, 0.0], vel_mps=[0.0, 7668.558, 0.0]),
     "Circular 400 km LEO illustrative state (2026-01-01T00:00:00 UTC)"),
    ("earth_bcrs_tdb", "seal", base(body_naif=0, frame=BCRS, time_scale=TDB, time_sec=tai_sec_from_utc_posix(946728000, 32),
     pos_m=[-2.6e10, 1.33e11, 5.77e10], vel_mps=[-29800.0, -4900.0, -2100.0]), "Illustrative BCRS state; body_naif 0 = none (NOT a barycenter; the BCRS origin is implied by the frame); 2000-01-01T12:00:00 UTC"),
    ("earth_bcrs_tcb", "seal", base(body_naif=0, frame=BCRS, time_scale=TCB, time_sec=tai_sec_from_utc_posix(946728000, 32),
     pos_m=[-2.6e10, 1.33e11, 5.77e10], vel_mps=[-29800.0, -4900.0, -2100.0]), "Same as above, TCB tag; body 0 = none (different hash by design)"),
    ("mars_jezero_body_tai", "seal", base(body_naif=499, frame=BODY, time_sec=tai_sec_from_utc_posix(1613681700, 37), pos_m=JEZERO),
     "Jezero crater 18.4447N 77.4508E h=-2570 m, IAU2000 Mars ellipsoid; 2021-02-18T20:55:00 UTC"),
    ("negative_zero_canonical", "seal", base(**{**CAMB, "vel_mps": [-0.0, -0.0, -0.0], "quat_xyzw": [-0.0, -0.0, -0.0, 1.0]}),
     "-0.0 canonicalized; hash must equal cambridge_itrf_tai"),
    ("max_nsec", "seal", base(**{**CAMB, "time_nsec": 999_999_999}), "Upper bound of time_nsec accepted"),
    ("negative_time_pre1970", "seal", base(**{**CAMB, "time_sec": -1}), "Negative time_sec is valid (signed)"),
    ("rotated_quat_moving", "seal", base(**{**CAMB, "vel_mps": [1.5, -2.25, 0.125], "quat_xyzw": [0.0, 0.0, math.sqrt(0.5), math.sqrt(0.5)]}),
     "90 deg about Z, nonzero velocity"),
    ("non_unit_quat_accepted", "seal", base(**{**CAMB, "quat_xyzw": [0.0, 0.0, 0.0, 2.0]}),
     "v1.0.0 does NOT enforce unit norm; sealed OK (caller's responsibility)"),
    ("extreme_finite_values", "seal", base(pos_m=[sys.float_info.max, -sys.float_info.max, 5e-324], vel_mps=[sys.float_info.min, 0.0, -1.0]),
     "Largest finite, smallest subnormal and normal doubles"),
    ("err_version_2", "seal", base(**{**CAMB, "version": 2}), "AEA_ERR_VERSION"),
    ("err_nsec_1e9", "seal", base(**{**CAMB, "time_nsec": 1_000_000_000}), "AEA_ERR_NSEC_BOUND"),
    ("err_frame_0", "seal", base(**{**CAMB, "frame": 0}), "AEA_ERR_FRAME (0 reserved INVALID)"),
    ("err_frame_5", "seal", base(**{**CAMB, "frame": 5}), "AEA_ERR_FRAME (out of range)"),
    ("err_time_scale_0", "seal", base(**{**CAMB, "time_scale": 0}), "AEA_ERR_TIME_SCALE"),
    ("err_nan_position", "seal", base(**{**CAMB, "pos_m": [float("nan"), 0.0, 0.0]}), "AEA_ERR_NON_FINITE"),
    ("err_inf_velocity", "seal", base(**{**CAMB, "vel_mps": [0.0, float("inf"), 0.0]}), "AEA_ERR_NON_FINITE"),
    ("verify_hash_mismatch", "verify", base(**CAMB), "Cambridge with 1 bit flipped in stored hash -> AEA_ERR_MISMATCH (1)", "flip"),
]

def bits(x): return struct.unpack("<Q", struct.pack("<d", x))[0]

def build():
    rows, js = [], []
    for v in V:
        name, op, r, note = v[:4]
        rc = validate(r)
        h = hashlib.sha256(prefix(r)).hexdigest() if rc == OK else "-"
        stored = "-"
        if op == "verify":
            hb = bytearray(hashlib.sha256(prefix(r)).digest()); hb[0] ^= 1
            stored, rc, h = hb.hex(), MISMATCH, "-"
        f = r["pos_m"] + r["vel_mps"] + r["quat_xyzw"]
        rows.append(" ".join([name, op, str(r["version"]), str(r["body_naif"]), str(r["time_sec"]), str(r["time_nsec"]),
                              str(r["frame"]), str(r["time_scale"])] + ["%016x" % bits(x) for x in f] + [str(rc), h, stored]))
        js.append(dict(name=name, op=op, note=note, fields={k: (r[k] if not isinstance(r[k], list) else [repr(x) for x in r[k]]) for k in r},
                       expected_rc=rc, expected_sha256=None if h == "-" else h, stored_hash=None if stored == "-" else stored,
                       prefix_hex=prefix(r).hex() if rc in (OK, MISMATCH) or True else None))
    txt = "# AEA-STATE/1 KAT vectors. Generated by tools/gen_kat.py (Python hashlib). DO NOT EDIT.\n" \
          "# name op version body time_sec time_nsec frame time_scale pos[3] vel[3] quat[4] (f64 bits hex) expected_rc expected_sha256 stored_hash\n" + "\n".join(rows) + "\n"
    return txt, json.dumps(dict(format="AEA-STATE/1", generator="tools/gen_kat.py", vectors=js), indent=1) + "\n"

if __name__ == "__main__":
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "kat")
    txt, js = build()
    paths = {"vectors.txt": txt, "vectors.json": js}
    if "--check" in sys.argv:
        bad = [p for p, c in paths.items() if open(os.path.join(root, p)).read() != c]
        if bad: print("KAT files out of date:", bad); sys.exit(1)
        print("KAT files up to date (%d vectors)" % len(V)); sys.exit(0)
    for p, c in paths.items(): open(os.path.join(root, p), "w").write(c)
    camb = [l for l in txt.splitlines() if l.startswith("cambridge_itrf_tai ")][0]
    assert "9f6cc1096562729a902167fd622e66a264a239f3e9a9d804414659e3ab97800e" in camb, "Cambridge KAT drifted!"
    print("wrote %d vectors" % len(V))
