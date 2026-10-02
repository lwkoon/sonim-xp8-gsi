#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Andrew Yong
# SPDX-License-Identifier: MIT
"""Apply a .bpatch file (offset, original bytes, patched bytes) to a binary.

usage: bytepatch.py PATCH INPUT OUTPUT
Refuses unless INPUT and the result match the sha256-in/sha256-out lines.
"""
import hashlib
import sys


def main():
    patch, inp, out = sys.argv[1:4]
    data = bytearray(open(inp, 'rb').read())
    want = {}
    edits = []
    for line in open(patch, encoding='utf-8'):
        t = line.rstrip('\n').split('\t')
        if not t[0] or t[0].startswith('#'):
            continue
        if t[0] in ('sha256-in', 'sha256-out'):
            want[t[0]] = t[1]
        else:
            edits.append((int(t[0], 0), bytes.fromhex(t[1]), bytes.fromhex(t[2])))
    have = hashlib.sha256(data).hexdigest()
    if have != want['sha256-in']:
        sys.exit('bytepatch: %s has sha256 %s, expected %s (different stock build?)'
                 % (inp, have, want['sha256-in']))
    for off, old, new in edits:
        if data[off:off + len(old)] != old:
            sys.exit('bytepatch: unexpected bytes at %#x' % off)
        data[off:off + len(new)] = new
    have = hashlib.sha256(data).hexdigest()
    if have != want['sha256-out']:
        sys.exit('bytepatch: result has sha256 %s, expected %s' % (have, want['sha256-out']))
    open(out, 'wb').write(data)


if __name__ == '__main__':
    main()
