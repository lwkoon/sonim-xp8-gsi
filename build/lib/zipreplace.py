#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Andrew Yong
# SPDX-License-Identifier: MIT
"""Copy a zip and replace entries in place with Info-ZIP, keeping every other
entry's compressed bytes, the entry order, method and date.

usage: zipreplace.py IN OUT [--drop-v1-sig] NAME=FILE...

--drop-v1-sig removes META-INF/MANIFEST.MF, *.SF, *.RSA, *.DSA, *.EC so that
apksigner writes a fresh v1 signature. Run zipalign on OUT afterwards.
"""
import calendar
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile


def main():
    args = sys.argv[1:]
    drop = '--drop-v1-sig' in args
    args = [a for a in args if a != '--drop-v1-sig']
    src, dst, repl = args[0], os.path.abspath(args[1]), dict(a.split('=', 1) for a in args[2:])
    with zipfile.ZipFile(src) as z:
        infos = {i.filename: i for i in z.infolist()}
    missing = set(repl) - set(infos)
    if missing:
        sys.exit('zipreplace: not in %s: %s' % (src, ', '.join(sorted(missing))))
    shutil.copyfile(src, dst)
    env = dict(os.environ, TZ='UTC')
    sig = re.compile(r'^META-INF/(MANIFEST\.MF|[^/]+\.(SF|RSA|DSA|EC))$')
    dels = [n for n in infos if drop and sig.match(n)]
    if dels:
        subprocess.run(['zip', '-q', '-d', dst] + dels, check=True, env=env)
    with tempfile.TemporaryDirectory() as t:
        for name, path in repl.items():
            info = infos[name]
            f = os.path.join(t, name)
            os.makedirs(os.path.dirname(f), exist_ok=True)
            shutil.copyfile(path, f)
            ts = calendar.timegm(info.date_time + (0, 0, 0))
            os.utime(f, (ts, ts))
            level = '-0' if info.compress_type == zipfile.ZIP_STORED else '-6'
            subprocess.run(['zip', '-q', '-X', '-fz-', '-UN=n', level, dst, name], cwd=t, check=True, env=env)


if __name__ == '__main__':
    main()
