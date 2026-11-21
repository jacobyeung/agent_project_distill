#!/usr/bin/env python3
"""Emit framed vertex bytes for (group, scene, mode) rows of a TSV plan to stdout. mode full|strided. Frame: u32 len, JSON, u64 len, bytes."""
import json, os, struct, sys
BASE=sys.argv[2] if len(sys.argv)>2 else '/data2/jjyeung/raw_datasets/scannetpp/data'; CH=4368; N=32; VB=15
out=sys.stdout.buffer
for line in open(sys.argv[1]):
    group,scene,mode,hlen,nv=line.split(); hlen=int(hlen); nv=int(nv)
    p=os.path.join(BASE,scene,'scans','mesh_aligned_0.05.ply')
    with open(p,'rb') as f:
        f.seek(hlen-11); assert f.read(11)==b'end_header\n', scene
        if mode=='full':
            meta=dict(group=group,scene=scene,mode=mode,nv=nv,chunks=[[0,nv]]); data_len=nv*VB
            m=json.dumps(meta).encode(); out.write(struct.pack('<I',len(m))+m+struct.pack('<Q',data_len))
            left=data_len
            while left:
                b=f.read(min(left,1<<22)); assert b; out.write(b); left-=len(b)
        else:
            starts=[int(round(i*(nv-CH)/(N-1))) for i in range(N)] if nv>CH*N else [0]
            chunks=[[s,min(CH,nv-s)] for s in starts] if nv>CH*N else [[0,nv]]
            meta=dict(group=group,scene=scene,mode=mode,nv=nv,chunks=chunks); data_len=sum(c[1] for c in chunks)*VB
            m=json.dumps(meta).encode(); out.write(struct.pack('<I',len(m))+m+struct.pack('<Q',data_len))
            for s,c in chunks:
                f.seek(hlen+s*VB); b=f.read(c*VB); assert len(b)==c*VB; out.write(b)
    out.flush()
