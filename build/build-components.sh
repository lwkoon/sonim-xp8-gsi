#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Andrew Yong
# SPDX-License-Identifier: MIT
#
# Build the MIT components (shim, vibrator, RROs) into out/components.
# Needs: build/fetch.sh sdk/ tools/ keys/
set -euo pipefail

# shellcheck source-path=SCRIPTDIR source=lib/tools.sh
. "$(dirname "$0")/lib/tools.sh"
unpack_sdk
unpack_ndk
unpack_patchelf

SRC=$ROOT/vendor
C=$OUT/components
W=$WORK/components
rm -rf "$W" && mkdir -p "$W" "$C"

# libxp8shim.so: 32-bit only, as only /vendor/lib/libgui_vendor.so needs it.
"$NDK_BIN/clang" --target=armv7a-linux-androideabi29 -O2 -fPIC -shared -nostdlib \
    -Wl,-soname,libxp8shim.so -Wl,-z,now -o "$W/libxp8shim.so" "$SRC/shim/xp8shim.cpp"
"$PATCHELF" --add-needed libselinux.so --add-needed libc.so "$W/libxp8shim.so"
cp "$W/libxp8shim.so" "$C/"

# xp8-vibrator: links against a stub libbinder_ndk that adds the LL-NDK symbols.
V=$W/vibrator && mkdir -p "$V"
SYSROOT=$NDK_BIN/../sysroot
VTGT=aarch64-linux-android30
"$NDK_BIN/clang" --target=$VTGT -O2 -fPIE -Wall -Werror -I "$SRC/vibrator/include" \
    -c -o "$V/xp8-vibrator.o" "$SRC/vibrator/xp8-vibrator.c"
python3 "$ROOT/build/lib/ndkstub.py" "$NDK_BIN/llvm-readelf" "$V" \
    "$SYSROOT/usr/lib/aarch64-linux-android/30/libbinder_ndk.so" \
    "$SRC/vibrator/libbinder_ndk.platform.txt" "$V/xp8-vibrator.o" >/dev/null
mkdir -p "$V/stub"
"$NDK_BIN/clang" --target=$VTGT -shared -nostdlib -Wl,-soname,libbinder_ndk.so \
    -Wl,--version-script,"$V/stub.map" -o "$V/stub/libbinder_ndk.so" "$V/stub.c"
"$NDK_BIN/clang" --target=$VTGT -pie -Wl,-z,now -o "$C/xp8-vibrator" "$V/xp8-vibrator.o" \
    -L "$V/stub" -lbinder_ndk -llog
cp "$SRC/vibrator/android.hardware.vibrator-xp8.xml" "$C/"

# Static RROs, signed with the AOSP testkey.
for d in "$SRC"/rro/*/; do
    n=$(basename "$d")
    r=$W/rro/$n && mkdir -p "$r"
    "$AAPT2" compile --dir "$d/res" -o "$r/res.zip"
    "$AAPT2" link -o "$r/u.apk" --manifest "$d/AndroidManifest.xml" -I "$ANDROID_JAR" "$r/res.zip"
    "$ZIPALIGN" -f -p 4 "$r/u.apk" "$r/a.apk"
    sign_apk testkey "$r/a.apk" "$C/$n.apk"
done

rm -rf "$W"
(cd "$C" && sha256sum ./*.so ./*.apk xp8-vibrator ./*.xml)
