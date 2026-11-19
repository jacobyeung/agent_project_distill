"""Job A2 (mode p rerun) local build. Usage: build_a2.py R_JSON ROWS_PART VB_NAME OUT_DIR
R_JSON: local copy of the row store's Orchard receipt r.json; ROWS_PART: its Orchard r.sqlite path; VB_NAME: name of the job
receipt under okh7/i_bb09a77d/. Writes OUT: receipt.json, ROWS.json, over_fx.json, fixture derivation fx/ (+ fx.result.json),
4.json (bound to the fixture identity, modes [p]), over.json (Orchard paths, PREPARATION_ONLY), full_weights.json, ja2.sh."""
import json, sys, os, hashlib, subprocess, shutil
from pathlib import Path
R, PART, VB, OUT = Path(sys.argv[1]), sys.argv[2], sys.argv[3], Path(sys.argv[4]); OUT.mkdir(parents=True, exist_ok=False)
D0 = Path('/scratch/jjyeung/orch_n30/cont_ops/work/d0'); B = D0 / 'jobB'; PY = sys.executable
IN = '/project/community/jjyeung/okh7/i_bb09a77d/'
GO = Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops/20261115T2358Z_ORCH_ANSWER_job_a_failed.md')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
r = json.loads(R.read_text()); assert r['database']['path'] == PART, (r['database']['path'], PART)
r['database']['path'] = '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/bb09a77d/v/rows.sqlite'
(OUT / 'receipt.json').write_text(json.dumps(r, indent=2, sort_keys=True) + '\n')
(OUT / 'ROWS.json').write_text(json.dumps(dict(rows_part=PART, rows_sha256=r['database']['sha256']), indent=1) + '\n')
env = dict(os.environ, DK_TOKENS='TOKENS_A2.json', DK_ROWS=str(OUT / 'ROWS.json'), DK_RECEIPT=str(OUT / 'receipt.json'), DK_VB=VB)
over = json.loads(subprocess.run([PY, str(B / 'make_over_b.py')], env=env, check=True, capture_output=True, text=True).stdout)
(OUT / 'over_fx.json').write_text(json.dumps(dict(over, fixture=True), indent=1, sort_keys=True) + '\n')
res = subprocess.run([PY, str(D0 / 'tools/derive_kit.py'), str(D0 / 'kitfull'), str(OUT / 'fx'), str(OUT / 'over_fx.json')], capture_output=True, text=True)
(OUT / 'fx.result.json').write_text(res.stdout); (OUT / 'fx.err').write_text(res.stderr)
if res.returncode: sys.exit('fixture derivation refused: ' + res.stderr[-800:])
fx = json.loads(res.stdout); ident = fx['config_identity']
a4 = json.loads((D0 / 'bundle_r8/r8/4.json').read_text())
g = dict(path='g/20261115T2358Z.md', sha256=sha(GO))
a4.update(config_sha256=ident, written_authorization='sha256:' + g['sha256'],
          written_authorizations=[w for w in a4['written_authorizations'] if not w['path'].startswith('g/')] + [g])
(OUT / '4.json').write_text(json.dumps(a4, sort_keys=True, separators=(',', ':')) + '\n')
shutil.copy(B / 'full_weights.json', OUT / 'full_weights.json')
M = {str(OUT / 'receipt.json'): IN + VB, str(D0 / 'base/runs/469ddece/m544/artifact.json'): IN + 'artifact.json',
     str(B / 'full_weights.json'): IN + 'a2/full_weights.json', str(D0 / 'v1/E00_MEMBERS.json'): IN + 'E00_MEMBERS.json',
     str(D0 / 'v1/sealed_vqa_receipt.json'): IN + 'sealed_vqa_receipt.json',
     str(D0 / 'v1/pool_selection_aa128e6f.json'): IN + 'pool_selection_aa128e6f.json'}
o = json.loads(json.dumps(over))
o['add_k'] = {k: dict(v, path=M[v['path']]) for k, v in o['add_k'].items()}
o['add_k']['4.json'] = dict(path=IN + 'a2/4.json', sha256=sha(OUT / '4.json'))
o['content'] = {k: M[v] for k, v in o['content'].items()}
o['e00_listing'] = M[o['e00_listing']]; o['sealed_docs'] = [M[x] for x in o['sealed_docs']]; o['status'] = 'PREPARATION_ONLY'
txt = json.dumps(o, indent=1, sort_keys=True) + '\n'; assert '/scratch/jjyeung' not in txt and 'orch_n30' not in txt
(OUT / 'over.json').write_text(txt)
shutil.copy(B / 'ja2.sh', OUT / 'ja2.sh'); [shutil.copy(D0 / 'a2' / n, OUT / n) for n in ('fam.py', 's2.py', 's2.sh', 's2sum.py')]
print(json.dumps(dict(identity=ident, config_key=fx['config_key'], manifest=fx['manifest_sha256'], rows=r['database']['sha256'],
                      receipt=sha(OUT / 'receipt.json'), a4=sha(OUT / '4.json'), over=sha(OUT / 'over.json'), closure=fx['closure']), indent=1))
