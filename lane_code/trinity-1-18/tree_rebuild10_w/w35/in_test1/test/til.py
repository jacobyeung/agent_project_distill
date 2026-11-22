"""fix21 il.py tests on a fake job layout: mount/runs (the empty run folder), ns/p/q/w and ns/p/q/u (staged copies),
v.json with init_artifact and persisted_files as the job writes them. Usage: til.py <il.py> <out dir (new)>"""
import hashlib, json, os, subprocess, sys, shutil
from pathlib import Path
IL, D = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(); assert not D.exists()
def sha(b): return hashlib.sha256(b).hexdigest()
def layout(name):
    root = D/name; w = root/'ns/p/q/w'; u = root/'ns/p/q/u'; runs = root/'mount/runs'
    for p in (w, u, runs): p.mkdir(parents=True)
    shards = {'model-00001-of-00002.safetensors': b'A'*1000, 'model-00002-of-00002.safetensors': b'B'*1000}
    index = b'{"weight_map": {}}'
    for n, b in shards.items(): (w/n).write_bytes(b)
    (w/'model.safetensors.index.json').write_bytes(index)
    manifest = json.dumps(dict(index=dict(name='model.safetensors.index.json', sha256=sha(index)),
                               files=[dict(name=n, sha256=sha(b)) for n, b in shards.items()])).encode()
    (w/'full_weights.json').write_bytes(manifest)
    heads = b'H'*5000; (u/sha(heads)).write_bytes(heads)
    raw = root/'mount/runs/6ed2c7aa/m400'
    artifact = json.dumps(dict(step=400, full_weights=dict(path=str(raw/'full_weights/full_weights.json'), sha256=sha(manifest)),
                               heads=dict(path=str(raw/'heads.pt'), sha256=sha(heads)))).encode()
    (u/sha(artifact)).write_bytes(artifact)
    pf = {sha(manifest): str(w/'full_weights.json'), sha(index): str(w/'model.safetensors.index.json'),
          sha(heads): str(u/sha(heads)), sha(artifact): str(u/sha(artifact))}
    pf.update({sha(b): str(w/n) for n, b in shards.items()})
    v = dict(init_artifact=dict(artifact=dict(path=str(u/sha(artifact)), sha256=sha(artifact)), lm='full'),
             r1_training=dict(persisted_files=pf))
    return root, v, dict(manifest=sha(manifest), heads=sha(heads), artifact=sha(artifact), raw=raw, w=w, u=u)
def run(root, v):
    (root/'v.json').write_text(json.dumps(v))
    r = subprocess.run([sys.executable, '-I', '-B', str(IL), str(root/'v.json'), str(root/'mount')], capture_output=True, text=True)
    return r.returncode, (r.stdout.strip().splitlines() or [''])[-1][:300], r.stderr[-300:]
res = {}
root, v, h = layout('ok'); res['ok'] = run(root, v)
res['ok_links'] = [os.readlink(h['raw']/'full_weights'), os.readlink(h['raw']/'heads.pt')]
res['ok_rerun_idempotent'] = run(root, v)
root, v, h = layout('missing_heads_pin'); v['r1_training']['persisted_files'].pop(h['heads']); res['missing_heads_pin'] = run(root, v)
root, v, h = layout('missing_artifact_pin'); v['r1_training']['persisted_files'].pop(h['artifact']); res['missing_artifact_pin'] = run(root, v)
root, v, h = layout('no_persisted_files'); v['r1_training'].pop('persisted_files'); res['no_persisted_files'] = run(root, v)
root, v, h = layout('heads_target_missing'); os.rename(h['u']/h['heads'], root/'moved'); res['heads_target_missing'] = run(root, v)
root, v, h = layout('heads_target_differs'); (h['u']/h['heads']).write_bytes(b'X'*5000); res['heads_target_differs'] = run(root, v)
root, v, h = layout('shard_missing'); os.rename(h['w']/'model-00002-of-00002.safetensors', root/'moved'); res['shard_missing'] = run(root, v)
root, v, h = layout('existing_other_link'); h['raw'].mkdir(parents=True); os.symlink('/nowhere', h['raw']/'heads.pt'); res['existing_other_link'] = run(root, v)
root, v, h = layout('existing_real_dir'); (h['raw']/'full_weights').mkdir(parents=True); res['existing_real_dir'] = run(root, v)
root, v, h = layout('outside_runs'); res['outside_runs'] = (lambda r: r)(subprocess.run([sys.executable, '-I', '-B', str(IL), str((root/'v.json').write_text(json.dumps(v)) and root/'v.json'), str(root/'elsewhere')], capture_output=True, text=True).returncode)
print(json.dumps(res, indent=1, default=str))
