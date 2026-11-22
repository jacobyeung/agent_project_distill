"""Build the ARKit fetch plan (no network): per capture, the traj rows of the dense set (kit gtc_common.dense_indices,
stride 2 in traj-row index from the first anchor, plus every anchor) with their timestamps, and a byte estimate.
Anchor timestamps come from the k6 frame plan (as wa.py used them); other rows from the 3dod lowres_wide file names
(lists/arkit.txt, traj row k = k-th 3dod PNG; within 0.55 ms of the plan on all 576 anchors). All rows use wa.py's 2 ms
traj tolerance. The byte estimate scales the capture's 3dod PNG bytes by the probe capture's raw/3dod ratio.
usage: plan_arkit.py OUT_DIR [PROBE_CD]"""
import collections, gzip, json, math, os, sys
sys.dont_write_bytecode = True
sys.path.insert(0, '/scratch/jjyeung/orch_n30/lever7/gtcd/kit')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gtc_common as GC
import zipcd
import numpy as np

FRAMES_GTC = '/scratch/jjyeung/orch_n30/lever6/gtc/out/FRAMES_GTC.json'
PLAN = '/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/fb_pack/in/pk/frame_plan.json.gz'
ALIAS = '/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/work/payload/b/work/meta/x/sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json'
LIST = '/scratch/jjyeung/orch_n30/lever7/gtcd/lists/arkit.txt'
SUMMARY = '/scratch/jjyeung/orch_n30/lever7/gtcd/lists/SUMMARY.json'
PROBE_ID = '43828324'
TAIL = 70000            # wa.py's suffix read
SLACK = 1024            # wa.py's per-group slack past the member data
CD_PER_MEMBER = 80.0    # probe: 450,698 CD bytes / 5,634 entries
MEMBERS_PER_ROW = 6.04  # probe: 5,633 PNG members / 933 traj rows


def tar_bytes(sizes):
    n = sum(512 + 512*math.ceil(s/512) for s in sizes) + 1024
    return 10240*math.ceil(n/10240)


def main():
    out = sys.argv[1]; probe_cd = sys.argv[2] if len(sys.argv) > 2 else None
    G = json.load(open(FRAMES_GTC)); P = json.load(gzip.open(PLAN))
    al = {c['native']: c['plan_alias'] for c in json.load(open(ALIAS))['captures']}
    S = {c['capture']: c for c in json.load(open(SUMMARY))['per_capture']}
    names = collections.defaultdict(list)
    for p in open(LIST):
        p = p.strip(); names[p.split('/')[7]].append(zipcd.stamp(p))
    plan, rows = {}, []
    for c in sorted(G['captures'], key=lambda c: c['capture']):
        if not c['capture'].startswith('arkitscenes/'):
            continue
        cid = c['capture'].split('/', 1)[1]; e = P['a'][al[c['native']]]
        idx = GC.dense_indices(c['anchor_indices'], GC.STRIDE['arkit'])
        ts = dict(zip(idx, names[cid]))
        if len(names[cid]) != len(idx):
            raise SystemExit('list rows differ from the dense set: ' + cid)
        anc = {k: t for k, t, fl in e['need']}
        if set(anc) != set(c['anchor_indices']) or not all(fl for _, _, fl in e['need']):
            raise SystemExit('plan anchors differ: ' + cid)
        need = [[k, anc.get(k, ts[k]), 1] for k in idx]
        plan[cid] = dict(u=e['u'], rot=e['rot'], need=need, anchors=sorted(anc))
        s = S[c['capture']]
        rows.append(dict(id=cid, rot=e['rot'], traj_rows=s['N'], members=len(idx), anchors=len(anc), first=idx[0], last=idx[-1],
                         d3dod_bytes=s['bytes']))
    ratio, exact = None, None
    if probe_cd:
        fr = zipcd.frames_of(zipcd.parse_cd(open(probe_cd, 'rb').read()))
        tsa = np.array([f[0] for f in fr]); picks, miss = [], []
        for k, t, fl in plan[PROBE_ID]['need']:
            b = zipcd.nearest(tsa, t)
            (picks if b is not None and abs(tsa[b]-t) <= 0.002 else miss).append((k, b))
        rng = [zipcd.member_range(fr[b]) for _, b in picks]
        wire = sum(z-a+1 for a, z in rng)
        csz = sum(fr[b][3] for _, b in picks)
        r3 = [r for r in rows if r['id'] == PROBE_ID][0]
        ratio = wire/r3['d3dod_bytes']
        exact = dict(id=PROBE_ID, png_members=len(fr), picks=len(picks), unique=len({b for _, b in picks}), misses=miss,
                     member_csize_bytes=csz, member_wire_bytes=wire, cd_bytes=os.path.getsize(probe_cd), ratio_wire_to_3dod=ratio)
    tot = dict(members=0, wire=0, tar=0)
    for r in rows:
        cd = os.path.getsize(probe_cd) if (probe_cd and r['id'] == PROBE_ID) else int(r['traj_rows']*MEMBERS_PER_ROW*CD_PER_MEMBER)
        if exact and r['id'] == PROBE_ID:
            mem = exact['member_wire_bytes']; r['bytes_kind'] = 'exact (probe CD)'
        else:
            mem = int(r['d3dod_bytes']*ratio) if ratio else None; r['bytes_kind'] = 'estimate (3dod bytes x probe ratio)'
        r['cd_bytes'] = cd; r['member_bytes'] = mem
        r['wire_bytes'] = TAIL + cd + (mem or 0)
        per = (mem or 0)/r['members']
        r['tar_bytes'] = tar_bytes([TAIL, cd, 2048] + [per]*r['members'])
        tot['members'] += r['members']; tot['wire'] += r['wire_bytes']; tot['tar'] += r['tar_bytes']
    tot['tar'] += 10240
    json.dump(dict(captures={k: v for k, v in plan.items()}), open(os.path.join(out, 'PLAN_ARKIT.json'), 'w'))
    json.dump(dict(rows=rows, totals=tot, probe=exact, stride_note=(
        'stride 2 in traj-row index: traj rows are 10 fps (0.1 s), so the dense set is 5 fps (0.2 s); the zip holds about '
        '60 fps members (6.04 per traj row), so a dense frame is about every 12th member')), open(os.path.join(out, 'PLAN_SUMMARY.json'), 'w'), indent=1)
    for r in rows:
        print(r['id'], r['rot'], r['members'], r['wire_bytes'], r['bytes_kind'])
    print('TOTAL', tot); print('PROBE', exact)


if __name__ == '__main__':
    main()
