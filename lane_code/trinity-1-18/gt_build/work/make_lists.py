"""Build the three exact file lists (ScanNet, ScanNet++, ARKit) for the governed streams, from PILOT300_INPUTS.json
and the gt_rasters ARKit listings (no new /data* listing)."""
import json, os
W = '/scratch/jjyeung/orch_n30/gt_build/work'
P = json.load(open(f'{W}/cr/PILOT300_INPUTS.json'))
L = json.load(open('/scratch/jjyeung/orch_n30/gt_rasters/work/PILOT162_ARKIT_LISTINGS.json'))
ts = lambda s: float(s.split('_')[1].rsplit('.', 1)[0])
pins = {}
for ds, tag in [('scannet', 'scannet'), ('scannetpp', 'scannetpp')]:
    rows = []
    for r in P:
        if not r['canonical'].startswith(ds + '/'): continue
        for k in ('instance_mesh', 'calibration', 'instances'):
            a = r['assets'][k]; assert a['path'].startswith('/data2/')
            rows.append(dict(path=a['path'][1:], size=a['size_bytes'], sha256=a['sha256']))
    assert len({x['path'] for x in rows}) == len(rows)
    open(f'{W}/LIST_{tag}.txt', 'w').write(''.join(x['path'] + '\n' for x in rows))
    json.dump(rows, open(f'{W}/LIST_{tag}.json', 'w'), indent=0)
    print(tag, len(rows), 'files', sum(x['size'] for x in rows), 'bytes')
files, frames = [], {}
for r in P:
    if not r['canonical'].startswith('arkitscenes/'): continue
    cid = r['canonical'].split('/')[1]; lst = L[cid]
    names = sorted(lst['names'], key=ts); assert len(names) == lst['n']
    t0 = ts(names[0]); grid = r['grid']
    slot = [round((ts(n) - t0) / 0.1) for n in names]
    m = dict(plain=[names[i] for i in grid if i < len(names)] if max(grid) < len(names) else None)
    if lst['gaps']:
        near = [names[min(range(len(names)), key=lambda j: abs(ts(names[j]) - (t0 + 0.1 * i)))] for i in grid]
        m['t10'] = near; m['slots'] = slot[-1] + 1
    frames[cid] = m
    sel = sorted({n for v in (m['plain'], m.get('t10')) if v for n in v}, key=ts)
    files += [f'{cid}/{cid}_3dod_annotation.json', f'{cid}/{cid}_frames/lowres_wide.traj']
    files += [f'{cid}/{cid}_frames/lowres_depth/{n}' for n in sel]
    files += [f'{cid}/{cid}_frames/lowres_wide_intrinsics/{n[:-4]}.pincam' for n in sel]
    os.makedirs(f'{W}/arkit_lists/{cid}', exist_ok=True)
    open(f'{W}/arkit_lists/{cid}/depth_list.txt', 'w').write('\n'.join(names) + '\n')
assert len(set(files)) == len(files)
open(f'{W}/LIST_arkit.txt', 'w').write(''.join(f + '\n' for f in files))
json.dump(frames, open(f'{W}/ARKIT_FRAMES.json', 'w'), indent=0)
print('arkit', len(frames), 'captures', len(files), 'files')
for c in ('41125837', '42899811', '42899906'):
    print(c, 'listing slots', L[c]['slots'], 'my slots', frames[c]['slots'], 'plain', frames[c]['plain'] is not None,
          'distinct t10 frames', len(set(frames[c]['t10'])))
