#!/usr/bin/env bash
# tools/make_release.sh TAG [OUTDIR]
# Builds the source tarball for TAG with `git archive` (LF endings via .gitattributes)
# and writes SHA256SUMS. Never modifies existing tags or previously published assets.
set -euo pipefail
TAG="${1:?usage: tools/make_release.sh TAG [OUTDIR]}"; OUT="${2:-dist}"
V="${TAG#v}"; NAME="aea-${V}"
git rev-parse -q --verify "${TAG}^{commit}" >/dev/null || { echo "no such tag/ref: $TAG" >&2; exit 1; }
mkdir -p "$OUT"
[ -e "$OUT/${NAME}.tar.gz" ] && { echo "refusing to overwrite $OUT/${NAME}.tar.gz" >&2; exit 1; }
git archive --format=tar --prefix="${NAME}/" "$TAG" | gzip -n -9 > "$OUT/${NAME}.tar.gz"
(cd "$OUT" && sha256sum "${NAME}.tar.gz" > SHA256SUMS && cat SHA256SUMS)
echo "commit: $(git rev-parse "${TAG}^{commit}")"
