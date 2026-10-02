#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Andrew Yong
# SPDX-License-Identifier: MIT
"""Write a link-time stub (C source + version script) for a shared library.

usage: ndkstub.py READELF OUTDIR NDK_STUB.so EXTRA.txt OBJ...

Covers every undefined symbol of OBJ that NDK_STUB.so or EXTRA.txt
('name version' lines) defines, keeping the version node of each.
"""
import re
import subprocess
import sys


def dynsyms(readelf, path, defined):
    out = subprocess.run([readelf, '--dyn-syms' if path.endswith('.so') else '--syms', '-W', path],
                         capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        f = line.split()
        if len(f) < 8 or not f[0].endswith(':'):
            continue
        if (f[6] != 'UND') == defined:
            yield f[7]


def main():
    readelf, outdir, stub, extra, *objs = sys.argv[1:]
    known = {}
    for s in dynsyms(readelf, stub, True):
        m = re.match(r'^([^@]+)@@?(\S+)$', s)
        if m:
            known[m.group(1)] = m.group(2)
    for line in open(extra):
        f = line.split()
        if f and not f[0].startswith('#'):
            known[f[0]] = f[1]
    need = sorted({s for o in objs for s in dynsyms(readelf, o, False)} & set(known))
    nodes = {}
    for s in need:
        nodes.setdefault(known[s], []).append(s)
    with open(outdir + '/stub.c', 'w') as f:
        f.writelines('void %s(void) {}\n' % s for s in need)
    with open(outdir + '/stub.map', 'w') as f:
        for v in sorted(nodes):
            f.write('%s {\n  global:\n%s};\n' % (v, ''.join('    %s;\n' % s for s in nodes[v])))
    print(' '.join(need))


if __name__ == '__main__':
    main()
