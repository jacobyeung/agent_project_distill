"""Trinity test only: a small fake job folder in the kit's layout (the j.sh paths), with the real tree
extracted at p/s as a.py extracts it and a fake config whose code pin is the kit's own source seal.
usage: mkfake.py <kit> <job folder> <venv dir>"""
import base64, hashlib, json, os, sys, tarfile
from pathlib import Path
kit, Q, venv = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
NJ = Path('/tmp/jjyeung/q_22c714e1')        # the namespace the pins name, as in the job
sys.path.insert(0, str(kit / 'b'))
from z import load
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p, v):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(v, sort_keys=True) + '\n'); return p
Q.mkdir(mode=0o700)
for d in ('cache', 'tmp', 'j', 'rp', 'live_spool', 'h/b', 'p/q/f/' + hashlib.sha256(b'/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/data2root').hexdigest(),
          'p/i', 's/aws/u/ap/8865619b/u', 's/c7d31ddd/data2root', 's/c7d31ddd/runs/aws128p_20261025/models', 's/c7d31ddd/venvs',
          's/c7d31ddd/anyhost', 's/epochs', 'x/b', 'x/k', 'x/o', 'x/ck', 'x/runs', 'x/data2root', 'x/models', 'x/u', 'x/arm'):
    (Q / d).mkdir(parents=True, exist_ok=True)
os.symlink(venv, Q / 's/c7d31ddd/venvs/rwtrain_torch211_cu129')
rec = put(Q / 's/c7d31ddd/anyhost/rec.json', dict(fake=True))
closure = put(Q / 'h/closure.json', dict(fake=True))
(Q / ('s/c7d31ddd/_jobs/cp4tk_' + sha(closure)[:12] + '/site_alias')).mkdir(parents=True)
put(Q / 'h/k/0.json', dict(commit='0' * 40, closure=dict(file=str(closure), sha256=sha(closure)),
                            record=dict(file=str(rec), sha256=sha(rec)), bwrap=dict(file='/usr/bin/bwrap', sha256=sha('/usr/bin/bwrap'))))
control = load(kit / 'k/a.json')
with tarfile.open(kit / control['source']['path']) as t: t.extractall(Q / 'p/s', filter='data')
seal = load(kit / 'k/7.json'); seal['archive']['path'] = str(kit / seal['archive']['path'])
code = put(Q / 'p/q/code.json', seal)
prep = put(Q / 'p/q/prep.json', dict(fake_preparation=True))
cfg = dict(world_size=4, training_mode='final', schema='fake-config-for-the-layout-test',
           code=dict(path=str(NJ / 'p/q/code.json'), sha256=sha(code)),
           preparation=dict(path=str(NJ / 'p/q/prep.json'), sha256=sha(prep)),
           r1_training=dict(persisted_files={}, review=None))
v0 = put(Q / 'p/q/v0.json', cfg)
put(Q / 'v.json', cfg)
put(Q / 'p/q/RESULT.json', dict(status='ADMIT', init_milestone=400, config=dict(path=str(NJ / 'p/q/v0.json'), sha256=sha(v0))))
put(Q / 'p/plan.json', dict(fake=True))
put(Q / 'r.json', {'_paths': {}})
(Q / 'j.sh').write_text('# fake\n'); (Q / '990015.steps').write_text('fake\n')
print('fake job folder', Q, 'files', sum(1 for _ in Q.rglob('*')))
