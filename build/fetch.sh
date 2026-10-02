#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Andrew Yong
# SPDX-License-Identifier: MIT
#
# Download every input in inputs.lock into cache/ and verify its sha256.
# usage: build/fetch.sh [PREFIX...]   e.g. build/fetch.sh sdk/ tools/ keys/
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
CACHE=${CACHE:-$here/../cache}
LOCK=$here/inputs.lock

sha256() {
    if command -v sha256sum >/dev/null; then sha256sum "$1" | cut -d' ' -f1
    else shasum -a 256 "$1" | cut -d' ' -f1; fi
}

wanted() {
    [ $# -eq 1 ] && return 0
    local name=$1 p; shift
    for p in "$@"; do [[ $name == "$p"* ]] && return 0; done
    return 1
}

fail=0
while read -r name url sum flag; do
    [[ -z ${name:-} || $name == \#* ]] && continue
    wanted "$name" "$@" || continue
    dst=$CACHE/$name
    if [ -f "$dst" ] && [ "$(sha256 "$dst")" = "$sum" ]; then
        continue
    fi
    mkdir -p "$(dirname "$dst")"
    echo "fetch $name"
    if [ -t 2 ]; then
        curl -fL --retry 3 --progress-bar -o "$dst.part" "$url"
    else
        curl -fL --retry 3 -sS -w '  %{size_download} bytes in %{time_total} s\n' -o "$dst.part" "$url"
    fi
    if [ "${flag:-}" = base64 ]; then
        base64 -d < "$dst.part" > "$dst.dec" && mv "$dst.dec" "$dst.part"
    fi
    got=$(sha256 "$dst.part")
    if [ "$got" != "$sum" ]; then
        echo "sha256 mismatch for $name: got $got, want $sum" >&2
        rm -f "$dst.part"
        fail=1
        continue
    fi
    mv "$dst.part" "$dst"
done < <(cat "$LOCK"; echo)

exit $fail
