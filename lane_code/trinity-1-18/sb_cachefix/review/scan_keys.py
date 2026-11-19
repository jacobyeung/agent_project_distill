"""Instance and record key sets across every stored K1 stage-1 cache (read-only, node-local scratch)."""
import collections
import json
from multiprocessing import Pool
from pathlib import Path

K1 = Path('/scratch/jjyeung/k1/run_convert_2')


def one(path):
    cache = json.loads(path.read_text())
    inst, rec, types = collections.Counter(), collections.Counter(), collections.Counter()
    for f in cache['frames'].values():
        for r in f['phrases'].values():
            rec.update(r.keys())
            types[type(r['presence']).__name__] += 1
            for i in r.get('instances') or []:
                inst.update(i.keys())
    return inst, rec, types


if __name__ == '__main__':
    paths = sorted(p/'candidates.json' for p in K1.iterdir() if (p/'candidates.json').is_file())
    inst, rec, types = collections.Counter(), collections.Counter(), collections.Counter()
    with Pool(8) as pool:
        for a, b, c in pool.imap_unordered(one, paths, chunksize=4):
            inst.update(a); rec.update(b); types.update(c)
    print(json.dumps(dict(caches=len(paths), instance_keys=dict(inst), record_keys=dict(rec),
                          record_presence_types=dict(types)), indent=1))
