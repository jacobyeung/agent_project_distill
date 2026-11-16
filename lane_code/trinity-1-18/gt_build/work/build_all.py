"""Run the clean-room builders (work/cr/builder_cr, sha-checked) for one dataset batch, <=24 processes.
usage: build_all.py {t1|arkit|arkit_t10} [NPROC] [DATASET filter for t1: scannet|scannetpp]   rows -> logs/BUILD_<batch>.jsonl"""
import json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
G = '/scratch/jjyeung/orch_n30/gt_build'; W = G + '/work'; B = W + '/cr/builder_cr'; PY = '/scratch/jjyeung/envs/p1cpu/bin/python'
batch = sys.argv[1]; nproc = min(int(sys.argv[2]) if len(sys.argv) > 2 else 24, 24); only = sys.argv[3] if len(sys.argv) > 3 else None
P = json.load(open(W + '/cr/PILOT300_INPUTS.json')); FR = json.load(open(W + '/ARKIT_FRAMES.json'))
env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1')
jobs = []
for r in P:
    ds, sid = r['canonical'].split('/')
    if batch == 't1' and ds in ('scannet', 'scannetpp') and only in (None, ds):
        sub = 'scannet' if ds == 'scannet' else 'scannetpp'
        dirs = {os.path.dirname(a['path']) for a in r['assets'].values()}; assert len(dirs) == 1
        names = sorted(os.path.basename(a['path']) for a in r['assets'].values())
        assert names == ['instance_mesh.npz', 'instances.json', 'official_cameras.npz'], names
        out = f'{G}/out/dose_pool/out/t1_gt/gt/' + os.path.basename(r['gt_path'])
        jobs.append((r['canonical'], [PY, B + '/build_t1_cr.py', G + '/stage/' + sub + dirs.pop(), out], out))
    elif batch.startswith('arkit') and ds == 'arkitscenes':
        t10 = batch == 'arkit_t10'
        if t10 != (FR[sid]['plain'] is None): continue
        root = f'{W}/arkit_src{"_t10" if t10 else ""}/{sid}'; os.makedirs(root + '/src', exist_ok=True)
        st = f'{G}/stage/arkit/{sid}'
        for n in (f'{sid}_3dod_annotation.json', f'{sid}_frames'):
            if not os.path.lexists(f'{root}/src/{n}'): os.symlink(f'{st}/{n}', f'{root}/src/{n}')
        if t10:  # declared variant input: the 10 Hz timeline, slot s -> nearest depth frame to t0 + 0.1 s
            ts = lambda s: float(s.split('_')[1].rsplit('.', 1)[0])
            names = open(f'{W}/arkit_lists/{sid}/depth_list.txt').read().split(); t0 = ts(names[0])
            slots = [min(names, key=lambda n: abs(ts(n) - (t0 + 0.1 * s))) for s in range(FR[sid]['slots'])]
            open(f'{root}/depth_list.txt', 'w').write('\n'.join(slots) + '\n')
        elif not os.path.exists(f'{root}/depth_list.txt'):
            os.symlink(f'{W}/arkit_lists/{sid}/depth_list.txt', f'{root}/depth_list.txt')
        out = f'{G}/out/dose_pool/out/arkit_gt/gt/' + os.path.basename(r['gt_path'])
        if t10: out = f'{G}/out/variants/arkit_t10/' + os.path.basename(r['gt_path'])
        jobs.append((r['canonical'], [PY, B + '/build_arkit_cr.py', sid, root + '/src', out, json.dumps(r['grid'])], out))
for _, _, o in jobs: os.makedirs(os.path.dirname(o), exist_ok=True)
log = open(f'{G}/logs/BUILD_{batch}.jsonl', 'a')
def run(j):
    cn, cmd, out = j
    if os.path.exists(out): return dict(canonical=cn, out=out, skipped='exists')
    t = time.time(); p = subprocess.run(cmd, env=env, capture_output=True, text=True, cwd=W)
    return dict(canonical=cn, out=out, rc=p.returncode, stdout=p.stdout.strip()[-400:], stderr=p.stderr.strip()[-800:], sec=round(time.time() - t, 1))
print(time.strftime('%FT%TZ', time.gmtime()), batch, len(jobs), 'jobs', nproc, 'procs', flush=True)
with ThreadPoolExecutor(nproc) as ex:
    for res in ex.map(run, jobs):
        log.write(json.dumps(res) + '\n'); log.flush()
print(time.strftime('%FT%TZ', time.gmtime()), 'done', flush=True)
