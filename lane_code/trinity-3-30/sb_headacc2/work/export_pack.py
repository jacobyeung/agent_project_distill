"""Stage the per-item evidence the head-accuracy kits read (lane sb_headacc2). Read-only on sources; writes work/pack/."""
import sys, json, gzip, hashlib, os
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
OUT = '/scratch/jjyeung/orch_n30/sb_headacc2/work/pack/'
def dump(name, rows):
    p = OUT + name
    with gzip.GzipFile(p, 'wb', mtime=0) as f:
        for r in rows:
            f.write((json.dumps(r, sort_keys=True, default=str) + '\n').encode())
    print(name, len(rows), os.path.getsize(p), sorted({r['type'] for r in rows})[:12])
which = sys.argv[1]
if which == 'direct':
    dump('DIRECT_R1_200_R0dev.jsonl.gz', K.direct('R1', 200, 'R0-dev'))
    dump('DIRECT_R1_200_devS1.jsonl.gz', K.direct('R1', 200, 'dev-S1'))
    dump('DIRECT_D0_200_R0dev_absdist.jsonl.gz', K.direct('D0', 200, 'R0-dev', types=['object_abs_distance']))
else:
    for step in (544, 200):
        try:
            rows = K.routed(step)
            dump('ROUTED_%d_devS1.jsonl.gz' % step, rows)
        except Exception as e:
            print('routed', step, 'FAILED', repr(e)[:300])
json.dump(K.SOURCES, open(OUT + 'SOURCES_%s.json' % which, 'w'), indent=1, default=str)
