#!/bin/bash
export TZ=UTC; echo "host $(hostname -s) $(date -u +%TZ)"
grep -m1 'model name' /proc/cpuinfo; echo "flags: $(grep -m1 '^flags' /proc/cpuinfo | grep -oE '\b(sha_ni|avx2|avx512f|vaes)\b' | sort -u | tr '\n' ' ')"; nproc --all; uptime
/usr/bin/python3 -I -c '
import hashlib,os,time,ssl
b=os.urandom(1<<30); m=memoryview(b); h=hashlib.sha256(); t=time.perf_counter()
for _ in range(4):
    for i in range(0,len(b),1<<20): h.update(m[i:i+(1<<20)])
s=time.perf_counter()-t; print("sha256 1MiB blocks: %.3f GB/s (%s)"%((4<<30)/s/1e9, ssl.OPENSSL_VERSION))'
