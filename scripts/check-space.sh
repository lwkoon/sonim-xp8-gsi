#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Andrew Yong
# SPDX-License-Identifier: MIT
#
# Refuse to start when a filesystem holding the given directories is short of space.
# usage: scripts/check-space.sh ROUTE DIR...
#   ROUTE  assemble  scripts/assemble.sh (stock system_a unpacked, vendor tree, images)
#          build     the full source build (build/*.sh, system image)
# XP8_MIN_FREE_GIB overrides the route's threshold.
set -euo pipefail

usage() { sed -n '5,10s/^# \{0,1\}//p' "$0" >&2; exit 2; }
[ $# -ge 2 ] || usage
route=$1; shift
case $route in
    assemble) need=8 ;;
    build)    need=40 ;;
    *) usage ;;
esac
need=${XP8_MIN_FREE_GIB:-$need}

seen=" "
short=0
for d in "$@"; do
    p=$d
    while [ ! -d "$p" ]; do p=$(dirname "$p"); done
    # df -P: portable one-line output; column 4 is free 1K blocks, column 6 the mount point.
    read -r _ _ _ free _ mnt < <(df -Pk "$p" | tail -n 1)
    case $seen in *" $mnt "*) continue ;; esac
    seen="$seen$mnt "
    gib=$((free / 1024 / 1024))
    if [ "$gib" -lt "$need" ]; then
        echo "check-space: $mnt (for $d) has $gib GiB free; the $route route needs $need GiB" >&2
        short=1
    else
        echo "check-space: $mnt has $gib GiB free (need $need GiB)"
    fi
done
exit $short
