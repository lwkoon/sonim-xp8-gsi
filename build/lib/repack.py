#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Andrew Yong
# SPDX-License-Identifier: MIT
"""Rebuild a header-v0 boot image with edited appended DTBs and optional cmdline suffix.
usage: repack.py in.img out.img [--vendor-flags FLAGS] [--system-flags ...] [--cmdline-add STR] [--ramdisk FILE]"""
import struct, zlib, hashlib, subprocess, sys, os, tempfile, argparse
ap=argparse.ArgumentParser()
ap.add_argument('inp'); ap.add_argument('out')
ap.add_argument('--vendor-flags', default='wait,slotselect')
ap.add_argument('--cmdline-add', default='')
ap.add_argument('--ramdisk')
ap.add_argument('--no-dt-edit', action='store_true')
a=ap.parse_args()
d=open(a.inp,'rb').read()
hdr=list(struct.unpack('<8s10I16s512s32s1024s', d[:1632]))
magic,ks,kaddr,rs,raddr,ss,saddr,taddr,ps,hv,osv,name,cmd,idb,xcmd=hdr
assert magic==b'ANDROID!' and hv==0 and ss==0
def pg(n): return (n+ps-1)//ps*ps
k=d[ps:ps+ks]; r=d[ps+pg(ks):ps+pg(ks)+rs]
if a.ramdisk: r=open(a.ramdisk,'rb').read()
dec=zlib.decompressobj(16+zlib.MAX_WBITS); dec.decompress(k); rest=dec.unused_data
gz=k[:ks-len(rest)]
dtbs=[];o=0
while o<len(rest):
    sz=struct.unpack('>I',rest[o+4:o+8])[0]; dtbs.append(rest[o:o+sz]); o+=sz
new=[]
with tempfile.TemporaryDirectory() as t:
    for i,b in enumerate(dtbs):
        f=os.path.join(t,'x.dtb'); open(f,'wb').write(b)
        if not a.no_dt_edit:
            n='/firmware/android/fstab/vendor'
            if subprocess.run(['fdtget',f,n,'status'],capture_output=True).returncode==0:
                subprocess.check_call(['fdtput','-t','s',f,n,'status','okay'])
                subprocess.check_call(['fdtput','-t','s',f,n,'fsmgr_flags',a.vendor_flags])
        new.append(open(f,'rb').read())
kern=gz+b''.join(new)
c=cmd.rstrip(b'\0')
if a.cmdline_add: c=c+b' '+a.cmdline_add.encode()
assert len(c)<512
sha=hashlib.sha1()
for blob in (kern,r,b''):
    sha.update(blob); sha.update(struct.pack('<I',len(blob)))
h=struct.pack('<8s10I16s512s32s1024s',magic,len(kern),kaddr,len(r),raddr,0,saddr,taddr,ps,0,osv,name,c,sha.digest(),xcmd)
end=ps+pg(ks)+pg(rs)
tail=d[end:].rstrip(b'\0')  # keep the appended AVB1 signature blob (same RoT as current boot)
img=h.ljust(ps,b'\0')+kern.ljust(pg(len(kern)),b'\0')+r.ljust(pg(len(r)),b'\0')+tail
assert len(img)<=64*1024*1024
img=img.ljust(64*1024*1024,b'\0')
open(a.out,'wb').write(img)
print('kernel',len(kern),'ramdisk',len(r),'dtbs',len(new),'cmdline',c.decode())
