"""Build GT rasters from the governed inputs. Usage: build_rasters.py ark|scn [NPROC]
ark: gb2 b2.py with rule set R1 (K1_GT_RASTER_REBUILD_20261115.md) per capture in work/streams_ark_jobs.json whose
     reader log line is ok; staged as work/ark_src/<id>/{src/<links>, depth_list.txt} (b2 reads src/../depth_list.txt).
scn: builder_cr build_t1_cr.build(asset_dir) per scene in work/inputs/scn/reader_scn.log with status ok.
Outputs work/rasters/{arkit,scannet}/<key>.npz (never overwritten) and work/rasters/BUILD_<mode>.jsonl."""
import json, os, sys, subprocess, hashlib
from concurrent.futures import ThreadPoolExecutor
L = '/scratch/jjyeung/orch_n30/b12_cntapp'; W = L + '/work'; PY = '/scratch/jjyeung/envs/p1cpu/bin/python'
B = W + '/builder'
R1 = '{"dt":"us","floor":"A","band":true,"pose64":true,"f32":true}'
ENV = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1', B2OPT=R1,
           CUDA_VISIBLE_DEVICES='')
mode = sys.argv[1]; nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 16
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
def logs(p):
    out = {}
    for l in open(p):
        if l.startswith('{'): d = json.loads(l); out[d['id']] = d
    return out
if mode == 'ark':
    jobs = {j['id']: j for j in json.load(open(W + '/streams_ark_jobs.json'))}; lg = logs(W + '/inputs/reader_ark.log')
    od = W + '/rasters/arkit'
    def run(i):
        j = jobs[i]; out = f'{od}/{i}.npz'
        if lg[i]['status'] != 'ok': return dict(id=i, alias=j['alias'], status='reader ' + lg[i]['status'])
        if not os.path.exists(out):
            st = f'{W}/ark_src/{i}'; src = st + '/src'; os.makedirs(src, exist_ok=True)
            for n in (f'{i}_frames', f'{i}_3dod_annotation.json'):
                if not os.path.lexists(f'{src}/{n}'): os.symlink(f'{W}/inputs/ark/{i}/{n}', f'{src}/{n}')
            if not os.path.exists(st + '/depth_list.txt'):
                open(st + '/depth_list.txt', 'w').write(open(f'{W}/inputs/ark_lists/{i}.depth_list.txt').read())
            p = subprocess.run([PY, B + '/gb2/code/b2.py', i, src, out, json.dumps(j['pins'])], env=ENV, capture_output=True, text=True)
            if p.returncode: return dict(id=i, alias=j['alias'], status='build rc %d' % p.returncode, err=p.stderr[-400:])
        return dict(id=i, alias=j['alias'], status='ok', path=out, sha256=sha(out))
    keys = sorted(k for k in jobs if k in lg)
else:
    jobs = {j['id']: j for j in json.load(open(W + '/streams_scn_jobs.json'))}; lg = logs(W + '/inputs/scn/reader_scn.log')
    od = W + '/rasters/scannet'
    def run(i):
        d = lg[i]; out = f'{od}/scannet__{i}.npz'
        if d['status'] != 'ok': return dict(id=i, alias=jobs[i]['alias'], status='reader ' + d['status'])
        dirs = {os.path.dirname(W + '/inputs/scn/' + a.lstrip('/')) for a in d['assets']}
        if len(dirs) != 1: return dict(id=i, alias=jobs[i]['alias'], status='assets in several dirs')
        if not os.path.exists(out):
            code = ('import sys; sys.argv=["x"]; sys.path[:0]=[%r]; import runpy; m=runpy.run_path(%r); print(m["build"](%r, %r))'
                    % (B + '/builder_cr', B + '/builder_cr/build_t1_cr.py', dirs.pop(), out))
            p = subprocess.run([PY, '-c', code], env=ENV, capture_output=True, text=True)
            if p.returncode: return dict(id=i, alias=jobs[i]['alias'], status='build rc %d' % p.returncode, err=p.stderr[-400:])
        return dict(id=i, alias=jobs[i]['alias'], status='ok', path=out, sha256=sha(out), fi=d['fi'])
    keys = sorted(k for k in jobs if k in lg)
keys = keys[:int(os.environ.get('LIMIT', len(keys)))]
os.makedirs(od, exist_ok=True)
with ThreadPoolExecutor(nproc) as ex: res = list(ex.map(run, keys))
with open(f'{W}/rasters/BUILD_{mode}.jsonl', 'w') as f:
    for r in res: f.write(json.dumps(r) + '\n')
import collections; print(mode, collections.Counter(r['status'][:40] for r in res))
