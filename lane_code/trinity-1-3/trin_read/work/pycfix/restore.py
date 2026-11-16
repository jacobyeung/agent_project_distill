"""Restore staged runtime_1 files whose bytes drifted (pycache rewrites) from the verified dl/runtime_1.tar.
Keeps the drifted bytes as evidence (pycfix/drifted.tar), checks every restored file against the STAGING inventory."""
import hashlib, json, os, tarfile
R = '/scratch/jjyeung/orch_n30/trin_read/root'; W = '/scratch/jjyeung/orch_n30/trin_read/work/pycfix'
inv = json.load(open(R+'/STAGING.json'))['pieces']['runtime_1']['evidence']['inventory']
errs = json.load(open('/scratch/jjyeung/orch_n30/trin_read/work/selfcheck_13_t3.json'))['checks']['pieces']['errors']
rel = sorted(e['path'][len(R)+1:] for e in errs)
assert all(r in inv and '__pycache__' in r for r in rel), 'non-pycache or uninventoried drift'
sha = lambda b: hashlib.sha256(b).hexdigest()
with tarfile.open(W+'/drifted.tar', 'x') as t:
    for r in rel: t.add(R+'/'+r, arcname=r)
want = set(rel); done = 0
with tarfile.open('/scratch/jjyeung/orch_n30/trin_read/dl/runtime_1.tar') as t:
    for m in t:
        if m.name in want:
            assert m.isfile(); b = t.extractfile(m).read()
            assert sha(b) == inv[m.name]['sha256'] and len(b) == inv[m.name]['bytes'], m.name
            dst = R+'/'+m.name; tmp = dst+'.restore.tmp'
            with open(tmp, 'xb') as f: f.write(b)
            os.chmod(tmp, m.mode & 0o7777); os.utime(tmp, (m.mtime, m.mtime)); os.replace(tmp, dst); done += 1
assert done == len(want), (done, len(want))
bad = [r for r in rel if sha(open(R+'/'+r,'rb').read()) != inv[r]['sha256']]
json.dump(dict(restored=done, still_bad=bad, drifted_tar=W+'/drifted.tar'), open(W+'/RESTORE.json','x'), indent=1)
print(done, len(bad))
