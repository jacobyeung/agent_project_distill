"""Consume a tar stream of (a/<name>.mp4 32-frame clip, b/<name>.mp4 64-frame clip) pairs from stdin, in memory:
sha256 and size of every member, and the dense-mapping pixel check (each 32-clip frame against its mapped
64-clip frame at position i64.index(i), and against the next 64-clip frame). Writes one small JSON; no media
touches disk."""
import hashlib, io, json, sys, tarfile
import av, numpy as np
IDX = json.load(open('/data2/jjyeung/agent_project_data/external_benchmarks/revsi/hf_metadata/sampled_video_frame_idx.json'))
out_path = sys.argv[1]
def frames(data):
    with av.open(io.BytesIO(data)) as c:
        return [f.to_ndarray(format='rgb24').astype(np.int16) for f in c.decode(video=0)]
files, checks, pend = {}, {}, {}
with tarfile.open(fileobj=sys.stdin.buffer, mode='r|') as tar:
    for m in tar:
        data = tar.extractfile(m).read()
        files[m.name] = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        kind, name = m.name.split('/', 1)
        pend.setdefault(name, {})[kind] = data
        if len(pend[name]) == 2:
            p = pend.pop(name); v = name[:-4]
            a, b = frames(p['a']), frames(p['b'])
            i32, i64 = IDX[v]['32-frame'], IDX[v]['64-frame']
            pos = [i64.index(i) for i in i32]
            ok = len(a) == 32 and len(b) == 64
            matched = [float(np.abs(a[k] - b[pos[k]]).mean()) for k in range(min(32, len(a)))] if ok else []
            neigh = [float(np.abs(a[k] - b[pos[k] + 1 if pos[k] < 63 else pos[k] - 1]).mean()) for k in range(min(32, len(a)))] if ok else []
            checks[v] = dict(n32=len(a), n64=len(b), positions=pos, matched_mae=matched, neighbour_mae=neigh,
                             matched_max=max(matched) if matched else None, neighbour_min=min(neigh) if neigh else None,
                             separated=bool(ok and max(matched) < min(neigh)))
json.dump(dict(files=files, checks=checks, n_files=len(files), n_checked=len(checks),
               all_separated=all(c['separated'] for c in checks.values())), open(out_path, 'w'))
