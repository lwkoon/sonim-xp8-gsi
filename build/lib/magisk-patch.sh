#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Andrew Yong
# SPDX-License-Identifier: MIT
#
# Patch a stock boot image with Magisk on a Linux host, with the same flags the
# Magisk app picks on the stock XP8: the APK's own boot_patch.sh, run by its
# static busybox, with the host-arch magiskboot and the arm64 device binaries.
# usage: build/lib/magisk-patch.sh MAGISK_APK IN_BOOT OUT_BOOT WORKDIR
set -euo pipefail

[ $# -eq 4 ] || { echo "usage: $0 MAGISK_APK IN_BOOT OUT_BOOT WORKDIR" >&2; exit 2; }
apk=$1 in=$2 out=$3 w=$4

[ "$(uname -s)" = Linux ] || { echo "magisk-patch: needs Linux (use scripts/assemble.sh --docker)" >&2; exit 1; }
case $(uname -m) in
    x86_64) host=x86_64 ;;
    aarch64|arm64) host=arm64-v8a ;;
    *) echo "magisk-patch: no magiskboot for $(uname -m)" >&2; exit 1 ;;
esac

rm -rf "$w"
mkdir -p "$w/x"
unzip -q -o -d "$w/x" "$apk" assets/boot_patch.sh assets/util_functions.sh assets/stub.apk \
    "lib/$host/libmagiskboot.so" "lib/$host/libbusybox.so" \
    lib/arm64-v8a/libmagiskinit.so lib/arm64-v8a/libmagisk.so lib/arm64-v8a/libinit-ld.so
p=$w/p
mkdir -p "$p"
cp "$w/x/assets/boot_patch.sh" "$w/x/assets/util_functions.sh" "$w/x/assets/stub.apk" "$p/"
cp "$w/x/lib/$host/libmagiskboot.so" "$p/magiskboot"
cp "$w/x/lib/$host/libbusybox.so" "$p/busybox"
cp "$w/x/lib/arm64-v8a/libmagiskinit.so" "$p/magiskinit"
cp "$w/x/lib/arm64-v8a/libmagisk.so" "$p/magisk"
cp "$w/x/lib/arm64-v8a/libinit-ld.so" "$p/init-ld"
cp "$in" "$p/boot.img"
chmod 755 "$p"/*

# boot_patch.sh expects these from the app's util_functions.sh; SOURCEDMODE skips loading it.
# PREINITDEVICE=persist is what the app chooses on the XP8.
cat > "$p/run.sh" <<'EOF'
ui_print() { echo "$1"; }
abort() { echo "$1"; exit 1; }
grep_prop() { sed -n "s/^$1=//p" "$2" | head -n 1; }
BOOTMODE=false
SOURCEDMODE=true
PREINITDEVICE=persist
KEEPVERITY=true
KEEPFORCEENCRYPT=true
PATCHVBMETAFLAG=false
RECOVERYMODE=false
LEGACYSAR=true
. ./boot_patch.sh boot.img
EOF
(cd "$p" && ./busybox sh run.sh) > "$w/boot_patch.log" 2>&1 ||
    { cat "$w/boot_patch.log" >&2; echo "magisk-patch: boot_patch.sh failed" >&2; exit 1; }
[ -f "$p/new-boot.img" ] || { cat "$w/boot_patch.log" >&2; exit 1; }
mv "$p/new-boot.img" "$out"
rm -rf "$w/x" "$p"
