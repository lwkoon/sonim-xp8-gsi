#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Andrew Yong
# SPDX-License-Identifier: MIT
"""SELinux file_contexts lookup with libselinux label_file ordering.

Specs without regex metacharacters are tried first; otherwise the last
matching spec wins, as in libselinux and so in e2fsdroid -S.
"""
import re
import stat

TYPES = {'--': stat.S_IFREG, '-d': stat.S_IFDIR, '-l': stat.S_IFLNK,
         '-c': stat.S_IFCHR, '-b': stat.S_IFBLK, '-s': stat.S_IFSOCK,
         '-p': stat.S_IFIFO}


def has_meta(spec):
    i = 0
    while i < len(spec):
        c = spec[i]
        if c in '.^$?*+|[({':
            return True
        if c == '\\':
            i += 1
        i += 1
    return False


class FileContexts:
    def __init__(self, paths):
        specs = []
        for path in paths:
            with open(path, encoding='utf-8') as f:
                for line in f:
                    t = line.split()
                    if not t or t[0].startswith('#'):
                        continue
                    if len(t) == 2:
                        rx, ftype, ctx = t[0], None, t[1]
                    elif len(t) == 3:
                        rx, ftype, ctx = t[0], TYPES[t[1]], t[2]
                    else:
                        raise ValueError('bad file_contexts line: %r' % line)
                    specs.append((re.compile('^(?:' + rx + ')$'), ftype, ctx,
                                  has_meta(rx)))
        # Stable: regex specs keep their order, exact paths move to the end.
        self.specs = ([s for s in specs if s[3]] + [s for s in specs if not s[3]])[::-1]

    def lookup(self, path, mode):
        for rx, ftype, ctx, _ in self.specs:
            if ftype is not None and ftype != stat.S_IFMT(mode):
                continue
            if rx.match(path):
                return None if ctx == '<<none>>' else ctx
        return None
