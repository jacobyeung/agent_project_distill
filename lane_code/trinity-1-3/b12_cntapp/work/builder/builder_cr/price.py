import json, os, time, collections
d = json.load(open('/scratch/jjyeung/orch_cd/k1_build/work/kit_k1a/out/CAPTURES.json'))
caps = {c['canonical']: c for c in d['captures']}
S = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/stagec_gen_20261012/out'
GENS = ['generation_v1', 'generation_center_retry_v1', 'generation_supplemental_v1']
AK = '/data3/shared/datasets/arkitscenes/3dod/Training'
out = []
for p in d['pilot']:
    cn = p['canonical']; ds, sid = cn.split('/'); grid = caps[cn]['anchor_grids'][0]
    rec = dict(canonical=cn, split=p['split'], gt_bytes=p['gt']['bytes'], gt_sha256=p['gt']['expected_sha256'], gt_path=p['gt']['path'], grid=grid)
    if ds == 'arkitscenes':
        a = f'{AK}/{sid}'
        rec['annotation'] = os.path.exists(f'{a}/{sid}_3dod_annotation.json')
        rec['traj'] = os.path.exists(f'{a}/{sid}_frames/lowres_wide.traj')
        try: n = len(os.listdir(f'{a}/{sid}_frames/lowres_depth'))
        except FileNotFoundError: n = 0
        rec['depth_frames'] = n; rec['grid_ok'] = n > max(grid)
        time.sleep(0.3)
    else:
        pre = 'scannet' if ds == 'scannet' else 'scannetppv2'
        cands = []
        for g in GENS:
            f = f'{S}/{g}/scenes/{pre}__{sid}/SCENE.json'
            if os.path.exists(f):
                s = json.load(open(f)); time.sleep(0.5)
                fi = s['student_input']['frame_indices']
                cands.append(dict(scene_json=f, frame_match=fi == grid,
                                  assets={k: s['assets'][k] for k in ('instance_mesh', 'calibration', 'instances') if k in s['assets']}))
        rec['scene_jsons'] = cands
        m = [c for c in cands if c['frame_match']]
        rec['grid_ok'] = bool(m)
        if m:
            rec['assets'] = m[0]['assets']
            rec['input_bytes'] = sum(v['size_bytes'] for v in m[0]['assets'].values())
            rec['assets_exist'] = all(os.path.exists(v['path']) for v in m[0]['assets'].values())
    out.append(rec)
json.dump(out, open('PILOT300_INPUTS.json', 'w'), indent=1)
c = collections.Counter((r['canonical'].split('/')[0], r['grid_ok'], r.get('assets_exist', r.get('annotation'))) for r in out)
print(c)
for ds in ['scannet', 'scannetpp']:
    rs = [r for r in out if r['canonical'].startswith(ds + '/') and r['grid_ok']]
    print(ds, len(rs), 'input bytes', sum(r['input_bytes'] for r in rs), 'max', max(r['input_bytes'] for r in rs))
print('missing', [ (r['canonical'], len(r.get('scene_jsons', []))) for r in out if not r['grid_ok']])
