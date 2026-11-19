"""Tests for pooled_harm_rule_v3_c1.py (ORCH ANSWER 0059Z item 2). Writes only under ./t_<pid>; registered files and READ_LEDGER are read only.
a. regression: the step-200 decision read of 673bc60f (h1read a8102c3207b): stdout byte-identical; JSON identical except script_sha256;
   ledger lines identical except utc/output path.
b. refusals: decision reads of 6ed2c7aa at 200, 673bc60f at 400, deadbeef at 400 refused with the run/step message.
c. a synthetic step-400 read of 6ed2c7aa (manifests by build_manifest.py) is accepted in decision mode at the later-look levels
   (1 - 0.05/32, 0.9875); the registered tool refuses the same read."""
import hashlib, json, os, re, shutil, subprocess, sys
from pathlib import Path
PY = '/scratch/jjyeung/envs/p1cpu/bin/python'
EVD = Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/pooled_rule')
REG, C1 = EVD/'pooled_harm_rule_v3.py', Path(__file__).resolve().parent/'pooled_harm_rule_v3_c1.py'
SRC = Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/build/a8102c3207b')
T = Path(__file__).resolve().parent/('t_%d' % os.getpid()); T.mkdir()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
fails = []
ID_MAP = json.load(open(json.load(open(EVD/'ROOM_CROSSWALK.json'))['sources']['id_map']['path']))
def check(name, ok, detail=''):
    print('%-4s %s %s' % ('PASS' if ok else 'FAIL', name, detail)); ok or fails.append(name)

def run(tool, d, step, receipt, ledger, out, cal=False):
    args = [PY, '-B', str(tool)] + (['--calibration'] if cal else []) + ['--step', str(step), '--read', str(d/'fetched/x/ITEMS.jsonl'),
            '--manifest-s1', str(d/'dev-S1_MANIFEST.json'), '--manifest-r0', str(d/'R0-dev_MANIFEST.json'),
            '--export-receipt', str(receipt), '--ledger', str(ledger), '--output', str(out)]
    return subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def ledger_copy(name, drop200=False):
    p = T/name
    lines = [l for l in (EVD/'READ_LEDGER.jsonl').read_text().splitlines(True)
             if not (drop200 and l.strip() and json.loads(l).get('kind') == 'decision' and json.loads(l).get('step') == 200)]
    p.write_text(''.join(lines)); return p

# a. regression on the real step-200 decision read
outs = {}
for tag, tool in (('reg', REG), ('c1', C1)):
    # disposable ledger without the step-200 decision lines, so each tool must append its two decision entries
    lg = ledger_copy('ledger_%s.jsonl' % tag, drop200=True); before = Path(lg).read_text(); o = T/('out200_%s.json' % tag)
    r = run(tool, SRC, 200, SRC/'runs/673bc60f/m200/artifact.json', lg, o)
    new = Path(lg).read_text()[len(before):]
    outs[tag] = (r.returncode, r.stdout, r.stderr, json.loads(o.read_text()) if o.exists() else None, new, o.read_bytes() if o.exists() else b'')
(rc1, so1, se1, j1, l1, b1), (rc2, so2, se2, j2, l2, b2) = outs['reg'], outs['c1']
check('a.exit codes equal', rc1 == rc2, '%s %s' % (rc1, rc2))
check('a.stdout byte-identical', so1 == so2 and len(so1) > 0, '%d bytes' % len(so1))
nerr = lambda e, tool: re.sub(rb'TOOL:[0-9]+:', b'TOOL:N:', e.replace(str(tool).encode(), b'TOOL'))
check('a.stderr equal after normalizing the script path and line numbers', nerr(se1, REG) == nerr(se2, C1), se1.decode().strip().replace('\n', ' | ')[:160])
strip = lambda j: {k: v for k, v in j.items() if k != 'script_sha256'} if j else j
check('a.json identical except script_sha256', strip(j1) == strip(j2) and j1 is not None)
norm = lambda s: [{k: v for k, v in json.loads(l).items() if k not in ('utc', 'output')} for l in s.splitlines() if l.strip()]
check('a.ledger: each tool appends two decision lines', len(norm(l1)) == 2 and len(norm(l2)) == 2 and all(e['kind'] == 'decision' and e['step'] == 200 for e in norm(l1)), '%d %d' % (len(norm(l1)), len(norm(l2))))
check('a.ledger lines identical except utc/output', norm(l1) == norm(l2) and len(norm(l1)) == 2)
check('a.json bytes identical after substituting script_sha256', b1.replace(sha(REG).encode(), b'X') == b2.replace(sha(C1).encode(), b'X') and len(b1) > 0, '%d bytes' % len(b1))
print('     regression verdict line:', so1.decode().strip().splitlines()[-1] if so1 else se1.decode()[-200:])

def synth(run_id, step):
    d = T/('syn_%s_%d' % (run_id, step)); x = d/'fetched/x'; x.mkdir(parents=True)
    for n in ('SUBMISSION.json',): shutil.copyfile(SRC/n, d/n)
    import io, tarfile, importlib.util
    shutil.copyfile(SRC/'fetched/EXIT.json', d/'fetched/EXIT.json')
    with tarfile.open(SRC/'fetched/result.tar.gz') as t:
        raw = t.extractfile('ITEMS.jsonl').read().decode()
    rows = [json.loads(l) for l in raw.splitlines() if l.strip()]
    for r in rows: r['step'] = step
    data = ''.join(json.dumps(r, sort_keys=True) + '\n' for r in rows).encode()
    with tarfile.open(d/'fetched/result.tar.gz', 'w:gz') as t:
        info = tarfile.TarInfo('ITEMS.jsonl'); info.size = len(data); t.addfile(info, io.BytesIO(data))
    fetch = json.loads((SRC/'fetched/FETCH.json').read_text())
    fetch['archive'] = dict(fetch['archive'], path=str(d/'fetched/result.tar.gz'), sha256=sha(d/'fetched/result.tar.gz'))
    (d/'fetched/FETCH.json').write_text(json.dumps(fetch, indent=1))
    spec_ = importlib.util.spec_from_file_location('ph', str(REG)); ph = importlib.util.module_from_spec(spec_); spec_.loader.exec_module(ph)
    for fam in ('main', 'a7'):
        (x/fam/'a0').mkdir(parents=True); shutil.copyfile(SRC/'fetched/x'/fam/'a0/request.json', x/fam/'a0/request.json')
    art = json.loads((SRC/'runs/673bc60f/m200/artifact.json').read_text()); art['step'] = step
    rp = d/('runs/%s/m%d/artifact.json' % (run_id, step)); rp.parent.mkdir(parents=True); rp.write_text(json.dumps(art, indent=1))
    spec = json.loads((SRC/'fetched/x/SPEC.json').read_text())
    spec['artifact'] = dict(spec['artifact'], path='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/%s/m%d/artifact.json' % (run_id, step), sha256=sha(rp))
    spec['step'] = step; spec['export_binding'] = dict(spec['export_binding'], run=run_id, step=step, generation='m%d' % step)
    (x/'SPEC.json').write_text(json.dumps(spec, indent=1))
    comp = json.loads((SRC/'fetched/x/COMPLETE.json').read_text()); comp['step'] = step; (x/'COMPLETE.json').write_text(json.dumps(comp, indent=1))
    (x/'ITEMS.jsonl').write_bytes(ph.decoded_member(str(d/'fetched/result.tar.gz'), 'ITEMS.jsonl', ID_MAP))
    for s in ('dev-S1', 'R0-dev'):
        subprocess.run([PY, '-B', str(EVD/'build_manifest.py'), 'kit', str(d), s, str(d/('%s_MANIFEST.json' % s))], check=True, stdout=subprocess.PIPE)
    return d, rp

# b. refusals
for run_id, step in (('6ed2c7aa', 200), ('673bc60f', 400), ('deadbeef', 400), ('6ed2c7aa', 600)):
    d, rp = synth(run_id, step)
    if (run_id, step) == ('6ed2c7aa', 600):
        r = run(C1, d, 400, rp, ledger_copy('l_%s_%d.jsonl' % (run_id, step)), T/'o.json')
        check('b.refuses 6ed2c7aa m600 read decided as step 400', r.returncode != 0 and b'REFUSED' in r.stderr + r.stdout, (r.stderr + r.stdout).decode().strip()[-120:])
        continue
    r = run(C1, d, step, rp, ledger_copy('l_%s_%d.jsonl' % (run_id, step)), T/'o.json')
    msg = (r.stderr + r.stdout).decode()
    check('b.refuses %s at %d' % (run_id, step), r.returncode != 0 and 'decision read is not of run' in msg, msg.strip()[-120:])

# c. acceptance of a 6ed2c7aa step-400 read built by build_manifest.py
d, rp = synth('6ed2c7aa', 400)
lg = ledger_copy('l_c.jsonl'); o = T/'out400_c1.json'
r = run(C1, d, 400, rp, lg, o)
check('c.c1 accepts 6ed2c7aa at 400 (decision mode)', r.returncode == 0 and o.exists(), (r.stderr.decode() + r.stdout.decode()).strip()[-160:])
if o.exists():
    j = json.loads(o.read_text())
    check('c.later-look levels', abs(j['levels']['H1'] - (1 - 0.05/32)) < 1e-12 and abs(j['levels']['H2'] - 0.9875) < 1e-12, str(j['levels']))
    check('c.run block names 6ed2c7aa m400', j['run']['run_id'] == '6ed2c7aa' and j['run']['step'] == 400)
    added = Path(lg).read_text()[len((EVD/'READ_LEDGER.jsonl').read_text()):]
    check('c.ledger (copy) gets two decision lines', len(norm(added)) == 2 and all(e['kind'] == 'decision' and e['run_id'] == '6ed2c7aa' for e in norm(added)))
r = run(REG, d, 400, rp, ledger_copy('l_c_reg.jsonl'), T/'out400_reg.json')
check('c.registered tool refuses the same read', r.returncode != 0 and 'decision read is not of run 673bc60f' in (r.stderr + r.stdout).decode())
# d. runaway counter reproduces derived_v3.py's runaway table on the step-200 read
RW = Path(__file__).resolve().parent/'count_runaways.py'
r = subprocess.run([PY, '-B', str(RW), '--x', str(SRC/'fetched/x'), '--output', str(T/'rw200.json')], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
der = json.loads((SRC/'R1_200_DERIVED.json').read_text())['runaways']
if r.returncode == 0:
    rw = json.loads((T/'rw200.json').read_text())['sets']
    same = all('%d/%d' % (rw[s]['single'], rw[s]['single_items']) == der[s]['single'] and '%d/%d' % (rw[s]['multi'], rw[s]['multi_items']) == der[s]['multi'] for s in ('dev-S1', 'R0-dev'))
    check('d.runaway counter equals derived_v3 on m200', same, '%s | %s' % ({s: (rw[s]['single'], rw[s]['multi']) for s in rw}, {s: (der[s]['single'], der[s]['multi']) for s in der}))
    check('d.repair runaway test fails at m200 (28/150, 62/287)', json.loads((T/'rw200.json').read_text())['repair_runaway_test_passes'] is False)
else:
    check('d.runaway counter runs', False, r.stderr.decode()[-200:])
print('tools: registered %s  c1 %s  runaways %s' % (sha(REG), sha(C1), sha(RW)))
print('RESULT:', 'ALL PASS' if not fails else 'FAILED: %s' % fails)
sys.exit(1 if fails else 0)
