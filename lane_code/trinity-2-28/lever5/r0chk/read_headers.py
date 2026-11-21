#!/usr/bin/env python3
"""Stream PLY headers (bytes up to end_header, max 8 KiB) of scenes listed in files given as args, as JSON lines to stdout."""
import json, os, sys
BASE='/data2/jjyeung/raw_datasets/scannetpp/data'
for lst in sys.argv[1:]:
    group=os.path.basename(lst).split('_')[0]
    for scene in open(lst).read().split():
        p=os.path.join(BASE,scene,'scans','mesh_aligned_0.05.ply')
        rec=dict(group=group,scene=scene)
        try:
            with open(p,'rb') as f:
                raw=f.read(8192)
            rec['size']=os.stat(p).st_size
            i=raw.find(b'end_header')
            rec['header']=raw[:i+10].decode('ascii','replace') if i>=0 else None
        except OSError as e:
            rec['error']=type(e).__name__
        sys.stdout.write(json.dumps(rec)+'\n'); sys.stdout.flush()
