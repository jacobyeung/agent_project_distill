"""Governed reader: for each ScanNet scene, read its SCENE.json candidates (stagec_gen), keep the one whose 32 frames equal
the row pins (pool) or lie inside the frame-map frames (extension), and stream SCENE.json + its three assets as tar."""
import json, os, subprocess, sys, time
jobs = json.load(open(sys.argv[1])); out = sys.argv[2]
S = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/stagec_gen_20261012/out'
log = open(out + '/reader_scn.log', 'a')
for j in jobs:
    t0 = time.time(); pick = None; why = []
    for g in ['generation_v1', 'generation_center_retry_v1', 'generation_supplemental_v1']:
        p = f'{S}/{g}/scenes/scannet__{j["id"]}/SCENE.json'
        if not os.path.exists(p): continue
        s = json.load(open(p)); fi = list(s['student_input']['frame_indices'])
        ok = fi == j['pins'] if j['pins'] else (len(fi) == 32 and set(fi) <= set(j['fm']))
        why.append((g, ok))
        a = s.get('assets', {})
        if ok and all(k in a for k in ('instance_mesh', 'calibration', 'instances')):
            pick = (p, [a[k]['path'] for k in ('instance_mesh', 'calibration', 'instances')], fi); break
    if not pick:
        log.write(json.dumps(dict(id=j['id'], status='no matching SCENE.json', cands=why)) + '\n'); log.flush(); continue
    files = [pick[0]] + pick[1]
    sys.stdout.flush()
    r = subprocess.run(['tar', 'cf', '-', '--ignore-failed-read', '-P'] + files, stdout=sys.stdout.buffer, stderr=subprocess.PIPE)
    log.write(json.dumps(dict(id=j['id'], status='ok' if r.returncode == 0 else 'tar rc %d' % r.returncode, scene_json=pick[0], assets=pick[1], fi=pick[2], err=r.stderr.decode()[-300:])) + '\n'); log.flush()
    time.sleep(max(0, 0.5 - (time.time() - t0)))
log.write('READER_DONE\n'); log.close()
