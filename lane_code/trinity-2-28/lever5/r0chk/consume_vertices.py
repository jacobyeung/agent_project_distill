#!/usr/bin/env python3
"""Read framed vertex stream from stdin; save xyz float32 .npy and meta .json per scene into argv[1]."""
import json, os, struct, sys
import numpy as np
D=sys.argv[1]; inp=sys.stdin.buffer
dt=np.dtype([('x','<f4'),('y','<f4'),('z','<f4'),('r','u1'),('g','u1'),('b','u1')])
def rd(n):
    b=bytearray()
    while len(b)<n:
        c=inp.read(n-len(b))
        if not c: raise EOFError
        b+=c
    return bytes(b)
n=0
while True:
    h=inp.read(4)
    if not h: break
    if len(h)<4: h+=rd(4-len(h))
    meta=json.loads(rd(struct.unpack('<I',h)[0])); L=struct.unpack('<Q',rd(8))[0]
    a=np.frombuffer(rd(L),dtype=dt)
    xyz=np.stack([a['x'],a['y'],a['z']],1).astype(np.float32)
    stem='%s_%s_%s'%(meta['group'],meta['scene'],meta['mode'])
    np.save(os.path.join(D,stem+'.npy'),xyz); json.dump(meta,open(os.path.join(D,stem+'.json'),'w')); n+=1
print('scenes',n,file=sys.stderr)
