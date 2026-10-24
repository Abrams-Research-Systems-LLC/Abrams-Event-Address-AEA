#!/usr/bin/env bash
# verify.sh [REPO_DIR] - reproduce checkable AEA-STATE/1 claims. Needs: rustup/cargo, gcc, python3, binutils.
set -u; R=$(cd "${1:-.}" && pwd); cd "$R"; PASS=0; FAIL=0
ok(){ echo "PASS: $*"; PASS=$((PASS+1)); }; bad(){ echo "FAIL: $*"; FAIL=$((FAIL+1)); }
echo "== repo $R  commit $(git rev-parse --short HEAD 2>/dev/null) branch $(git branch --show-current 2>/dev/null)"
python3 tools/aea.py verify tests/kat/cambridge.bin && ok python-verify || bad python-verify
SZ=$(stat -c%s tests/kat/cambridge.bin); [ "$SZ" = 136 ] && ok "record 136 B" || bad "record $SZ B"
P=$(python3 -c "import hashlib;d=open('tests/kat/cambridge.bin','rb').read();print(hashlib.sha256(d[:104]).hexdigest()==d[104:].hex(), d[104:].hex())")
echo "sha256(bytes[0:104]) == bytes[104:136]: $P"; case $P in True\ 9f6cc109*800e) ok "seal covers [0,104), digest 9f6cc109..800e";; *) bad seal-range;; esac
python3 -c "import struct;d=open('tests/kat/cambridge.bin','rb').read();print('raw LE u64/i64/f64 candidates containing 1246190426:',[o for o in range(0,104,8) if struct.unpack_from('<q',d,o)[0]==1246190426 or struct.unpack_from('<d',d,o)[0]==1246190426.0])"
echo "== cargo test"; T=$(cargo test 2>&1); echo "$T" | grep -E '^test |test result|error' ; N=$(echo "$T"|grep -oE 'ok\. [0-9]+ passed'|awk '{s+=$2}END{print s}'); F=$(echo "$T"|grep -oE '[0-9]+ failed'|awk '{s+=$1}END{print s}')
echo "total passed=$N failed=$F"; [ "${F:-0}" = 0 ] && [ "${N:-0}" -gt 0 ] && ok "cargo test $N passed" || bad "cargo test"
if grep -q '^optic' Cargo.toml; then echo "== cargo test --features optic"; T=$(cargo test --features optic 2>&1); echo "$T"|grep -E 'test result|error'; echo "$T"|grep -qE '[1-9][0-9]* failed|error\[' && bad optic-tests || ok "optic tests ($(echo "$T"|grep -oE 'ok\. [0-9]+ passed'|awk '{s+=$2}END{print s}') passed)"; fi
[ -f tests/bitflip.rs ] && { echo "== bitflip"; cargo test --test bitflip -- --nocapture 2>&1 | grep -iE 'detect|flip|undetect|result'; echo "(test asserts detected == 136*8-6 = 1082, zero_sign == 6)"; }
echo "== release build + nm"; cargo build --release -q 2>&1|tail -3; A=target/release/libaea.a
SYMS=$(nm -g --defined-only "$A" 2>/dev/null | awk '$2=="T"{print $3}' | grep -E '^aea_' | sort -u | tr '\n' ' '); echo "exported aea_* T symbols: $SYMS"
[ "$SYMS" = "aea_seal aea_verify aea_version " ] && ok "C ABI exactly seal/verify/version" || bad "C ABI = $SYMS"
echo "== C caller"; gcc -std=c11 -Wall -O2 -Iinclude examples/c_caller/main.c -Ltarget/release -laea -lpthread -ldl -lm -o /tmp/aea_c_$$ && /tmp/aea_c_$$ ; [ $? = 0 ] && ok "C caller" || bad "C caller"
echo "== Rust vs C vs Python digest"; RD=$(cat tests/kat/cambridge.hash 2>/dev/null|tr -d ' \n'); echo "cambridge.hash: $RD"
if [ -d examples/optic_caller ] && grep -q '^optic' Cargo.toml; then echo "== optic C demo"; cargo build --release -q --features optic && gcc -std=c11 -D_DEFAULT_SOURCE -O2 -Iinclude examples/optic_caller/main.c -Ltarget/release -laea -lpthread -ldl -lm -o /tmp/aea_o_$$ && /tmp/aea_o_$$ && ok "optic demo ran" || bad "optic demo"; cargo build --release -q; fi
echo "== Cortex-M .text"; for t in thumbv6m-none-eabi thumbv7em-none-eabihf thumbv8m.main-none-eabihf; do rustup target add $t >/dev/null 2>&1; cargo build --release -q --target $t 2>&1|tail -2; L=target/$t/release/libaea.a; if [ -f $L ]; then M=$(ar t $L | grep '^aea-'); D=$(mktemp -d); (cd $D && ar x $OLDPWD/$L $M); SZ=$( (llvm-size $D/$M 2>/dev/null || size $D/$M) | awk 'NR==2{print $1}'); rm -rf $D; echo "$t aea member .text = $SZ B"; fi; done
[ -f tests/kat/vectors.json ] && python3 - <<'PY'
import json,hashlib;v=json.load(open('tests/kat/vectors.json'));v=v.get('vectors',v) if isinstance(v,dict) else v;print('vectors.json entries:',len(v))
PY
echo "== SUMMARY: $PASS passed, $FAIL failed"; [ $FAIL = 0 ]
