#!/usr/bin/env python3
"""CPU startup check of the official VSI-Bench 5,130 video path on Orchard (lane official_reads).
Builds a symlink view of what a job stages (q7 stage + cp4tk_eval/inputs), runs the official harness's own load_tasks
(official_full, video_32: resolves and sha256-hashes every video, as at job startup) and compute_videos_sha256, then
rebuilds f17's videos_sha256 payload (f17's AWS video_root, these per-file shas) and compares it to 7088baaa...
usage: python3 -I vcheck.py TREE VIEW OUT.json"""
import json, os, sys, time
from types import SimpleNamespace
TREE, VIEW, OUT = sys.argv[1:4]
sys.path.insert(0, os.path.join(TREE, 'official'))
sys.path.insert(0, TREE)
import run_eval_hc as h
J = '/project/community/jjyeung'
META = J + '/cp4tk_eval/official/meta_5130.jsonl'
REL = 'data2root/jjyeung/agent_project_data/vsibench_videos'
SRCS = [J + '/q7e/stage/distill/' + REL, J + '/cp4tk_eval/inputs/' + REL]
F17_ROOT = '/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/5f67d1f3/c/eb94a102/d1_3a6a1cf9'
F17_SHA = '7088baaa11e9dbbd5563ea122e9b7c4c3a1c5cd4c61020a98c93e0e1e6bbc3a1'
t0 = time.time()
rows = [json.loads(l) for l in open(META) if l.strip()]
src_of, dup = {}, []
for src in SRCS:
    if not os.path.isdir(src):
        continue
    for d in sorted(os.listdir(src)):
        for n in sorted(os.listdir(os.path.join(src, d))):
            key = d + '/' + n
            if key in src_of:
                dup.append(key)
            else:
                src_of[key] = os.path.join(src, d, n)
need = sorted({'%s/%s.mp4' % (r['dataset'], r['scene_name']) for r in rows})
for key in need:
    if key in src_of:
        os.makedirs(os.path.join(VIEW, os.path.dirname(key)), exist_ok=True)
        link = os.path.join(VIEW, key)
        if not os.path.lexists(link):
            os.symlink(src_of[key], link)
missing = [k for k in need if k not in src_of]
args = SimpleNamespace(dataset_mode='official_full', meta_jsonl=META, video_root=VIEW, data2_root='', frame_source='video_32',
                       prepared_dir='', limit=0, max_frames_num=32, arch='q35', prompt_mode='ours')
rep = {'needed_videos': len(need), 'missing_videos': missing, 'duplicate_names_across_sources': dup}
try:
    tasks = h.load_tasks(args)
    rep['tasks'] = len(tasks)
    sha_of = {}
    for t in tasks:
        sha_of[os.path.relpath(t['video_path'], VIEW)] = t['video_sha256']
    payload = [('official_%s' % r['id'], (os.path.join(F17_ROOT, r['dataset'], r['scene_name'] + '.mp4'),
                                          sha_of['%s/%s.mp4' % (r['dataset'], r['scene_name'])])) for r in rows]
    import hashlib
    rep['f17_payload_sha256'] = hashlib.sha256(json.dumps(payload, sort_keys=True).encode('utf-8')).hexdigest()
    rep['matches_f17_videos_sha256'] = rep['f17_payload_sha256'] == F17_SHA
    rep['view_videos_sha256'] = h.compute_videos_sha256('official_full', META, '', '', '', VIEW, '', True)
    rep['per_file_sha256'] = sha_of
    rep['status'] = 'OK' if rep['matches_f17_videos_sha256'] and not missing and len(tasks) == 5130 else 'FAIL'
except Exception as e:
    rep['status'] = 'FAIL'; rep['error'] = repr(e)
rep['seconds'] = round(time.time() - t0)
json.dump(rep, open(OUT, 'w'), indent=1, sort_keys=True)
print(json.dumps({k: v for k, v in rep.items() if k != 'per_file_sha256'}, sort_keys=True)[:2000])
