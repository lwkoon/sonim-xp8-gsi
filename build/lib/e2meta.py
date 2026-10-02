#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Andrew Yong
# SPDX-License-Identifier: MIT
"""Read file metadata from an ext4 image with debugfs (no mount, no root).

usage: e2meta.py IMAGE ROOT [--tree DIR]

Prints one TSV row per entry below ROOT, sorted by path:
  path  mode(octal, with type bits)  uid  gid  selinux  capability(hex|-)  data
where data is the sha256 of a regular file (needs --tree, an rdump of ROOT),
'->target' for a symlink, or 'dir'.
"""
import argparse
import hashlib
import os
import re
import stat
import subprocess
import sys


def debugfs(image, cmds):
    """Run debugfs commands in one process; return each command's output."""
    script = ''.join(c + '\n' for c in cmds)
    p = subprocess.run(['debugfs', '-f', '-', image], input=script.encode(),
                       capture_output=True, check=True)
    out = p.stdout.decode('utf-8', 'surrogateescape')
    parts = re.split(r'^debugfs: ', out, flags=re.M)[1:]
    if len(parts) != len(cmds):
        sys.exit('e2meta: debugfs output did not match %d commands' % len(cmds))
    return [x.split('\n', 1)[1] if '\n' in x else '' for x in parts]


def q(path):
    return '"' + path.replace('\\', '\\\\').replace('"', '\\"') + '"'


def ea_names(text):
    return [m.group(1) for m in re.finditer(r'^  (\S+) \(\d+\)', text, re.M)]


def ea_value(text):
    m = re.search(r'^\S+ \((\d+)\) = ([0-9a-f ]*)$', text, re.M)
    v = bytes.fromhex(m.group(2).replace(' ', '')) if m else b''
    if not m or len(v) != int(m.group(1)):
        sys.exit('e2meta: cannot parse xattr value: %r' % text)
    return v


def walk(image, root):
    """Return {relpath: (mode, uid, gid, {xattr: bytes})}; '' is ROOT itself."""
    root = '/' + root.strip('/') if root.strip('/') else '/'
    meta = {}
    level = ['']
    while level:
        outs = debugfs(image, ['ls -p ' + q(os.path.join(root, d) if d else root)
                               for d in level])
        nxt = []
        for d, out in zip(level, outs):
            for line in out.splitlines():
                f = line.split('/')
                if len(f) < 7 or f[0] != '':
                    continue
                name = '/'.join(f[5:-2])
                if f[1] == '0' or not name:
                    continue
                if name in ('.', '..'):
                    if name == '.' and d == '':
                        meta[''] = [int(f[2], 8), int(f[3]), int(f[4])]
                    continue
                rel = os.path.join(d, name) if d else name
                mode = int(f[2], 8)
                meta[rel] = [mode, int(f[3]), int(f[4])]
                if stat.S_ISDIR(mode):
                    nxt.append(rel)
        level = nxt
    paths = sorted(meta)
    full = {p: q(os.path.join(root, p) if p else root) for p in paths}
    outs = debugfs(image, ['ea_list ' + full[p] for p in paths])
    want = [(p, n) for p, o in zip(paths, outs) for n in ea_names(o)]
    vals = debugfs(image, ['ea_get -x %s %s' % (full[p], n) for p, n in want])
    eas = {p: {} for p in paths}
    for (p, n), o in zip(want, vals):
        eas[p][n] = ea_value(o)
    return {p: tuple(meta[p]) + (eas[p],) for p in paths}


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest()


def label(eas):
    v = eas.get('security.selinux')
    return v.rstrip(b'\0').decode() if v is not None else '-'


def cap(eas):
    v = eas.get('security.capability')
    return v.hex() if v is not None else '-'


def rows(image, root, tree=None):
    for p, (mode, uid, gid, eas) in sorted(walk(image, root).items()):
        other = set(eas) - {'security.selinux', 'security.capability'}
        if other:
            sys.exit('e2meta: unexpected xattrs on %s: %s' % (p or '/', sorted(other)))
        if stat.S_ISDIR(mode):
            data = 'dir'
        elif tree is None:
            data = '-'
        elif stat.S_ISLNK(mode):
            data = '->' + os.readlink(os.path.join(tree, p))
        else:
            data = sha256(os.path.join(tree, p))
        yield (p or '.', '%o' % mode, str(uid), str(gid), label(eas), cap(eas), data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('image')
    ap.add_argument('root')
    ap.add_argument('--tree')
    a = ap.parse_args()
    for r in rows(a.image, a.root, a.tree):
        print('\t'.join(r))


if __name__ == '__main__':
    main()
