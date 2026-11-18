"""Job B (mode t, world 4) local build on a row store version.
  build_b.py fix R_JSON ROWS_PART VB_NAME OUT   receipt, ROWS, fixture derivation fx/, identity + contract, 4.json (from 4b.json)
  build_b.py over OUT                           Orchard over.json (READY; add_k review.json, staging.json, 4.json from OUT)
Bundle on Orchard: okh7/i_bb09a77d/VB_NAME (the job receipt, shared with job A2) and okh7/i_bb09a77d/b5/{over,4,review,staging,full_weights}.json."""
import json, sys, os, hashlib, subprocess, shutil
from pathlib import Path
D0 = Path('/scratch/jjyeung/orch_n30/cont_ops/work/d0'); B = D0 / 'jobB'; PY = sys.executable
IN = '/project/community/jjyeung/okh7/i_bb09a77d/'; SUB = 'b5/'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def wj(p, v, compact=False): Path(p).write_text((json.dumps(v, sort_keys=True, separators=(',', ':')) if compact else json.dumps(v, indent=1, sort_keys=True)) + '\n')
if sys.argv[1] == 'fix':
    R, PART, VB, OUT = Path(sys.argv[2]), sys.argv[3], sys.argv[4], Path(sys.argv[5]); OUT.mkdir(parents=True, exist_ok=False)
    r = json.loads(R.read_text()); assert r['database']['path'] == PART
    r['database']['path'] = '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/bb09a77d/v/rows.sqlite'
    (OUT / 'receipt.json').write_text(json.dumps(r, indent=2, sort_keys=True) + '\n')
    wj(OUT / 'ROWS.json', dict(rows_part=PART, rows_sha256=r['database']['sha256'])); (OUT / 'VB').write_text(VB + '\n')
    env = dict(os.environ, DK_TOKENS='TOKENS_B.json', DK_ROWS=str(OUT / 'ROWS.json'), DK_RECEIPT=str(OUT / 'receipt.json'), DK_VB=VB)
    over = json.loads(subprocess.run([PY, str(B / 'make_over_b.py')], env=env, check=True, capture_output=True, text=True).stdout)
    wj(OUT / 'over_local.json', over); wj(OUT / 'over_fx.json', dict(over, fixture=True))
    res = subprocess.run([PY, str(D0 / 'tools/derive_kit.py'), str(D0 / 'kitfull'), str(OUT / 'fx'), str(OUT / 'over_fx.json')], capture_output=True, text=True)
    (OUT / 'fx.result.json').write_text(res.stdout); (OUT / 'fx.err').write_text(res.stderr)
    if res.returncode: sys.exit('fixture derivation refused: ' + res.stderr[-800:])
    ic = json.loads(subprocess.run([PY, str(D0 / 'a2/contract.py'), str(OUT / 'fx')], check=True, capture_output=True, text=True).stdout)
    a4 = json.loads((B / '4b.json').read_text()); a4['config_sha256'] = ic['identity']; wj(OUT / '4.json', a4, compact=True)
    shutil.copy(B / 'full_weights.json', OUT / 'full_weights.json')
    fx = json.loads(res.stdout); wj(OUT / 'ids.json', dict(ic, config_key=fx['config_key'], fixture_manifest=fx['manifest_sha256'],
        rows=r['database']['sha256'], receipt=sha(OUT / 'receipt.json'), a4=sha(OUT / '4.json')))
    print((OUT / 'ids.json').read_text())
else:
    OUT = Path(sys.argv[2]); VB = (OUT / 'VB').read_text().strip(); over = json.loads((OUT / 'over_local.json').read_text())
    ids = json.loads((OUT / 'ids.json').read_text())
    rv, st = json.loads((OUT / 'review.json').read_text()), json.loads((OUT / 'staging.json').read_text())
    assert rv['config_sha256'] == st['config_sha256'] == ids['identity'] and rv['admission_contract_sha256'] == ids['contract'] and rv['verdict'] == st['status'] == 'PASS' and st['missing'] == []
    M = {str(OUT / 'receipt.json'): IN + VB, str(D0 / 'base/runs/469ddece/m544/artifact.json'): IN + 'artifact.json',
         str(B / 'full_weights.json'): IN + SUB + 'full_weights.json', str(D0 / 'v1/E00_MEMBERS.json'): IN + 'E00_MEMBERS.json',
         str(D0 / 'v1/sealed_vqa_receipt.json'): IN + 'sealed_vqa_receipt.json',
         str(D0 / 'v1/pool_selection_aa128e6f.json'): IN + 'pool_selection_aa128e6f.json'}
    o = json.loads(json.dumps(over))
    o['add_k'] = {k: dict(v, path=M[v['path']]) for k, v in o['add_k'].items()}
    for n in ('4.json', 'review.json', 'staging.json'): o['add_k'][n] = dict(path=IN + SUB + n, sha256=sha(OUT / n))
    o['content'] = {k: M[v] for k, v in o['content'].items()}
    o['e00_listing'] = M[o['e00_listing']]; o['sealed_docs'] = [M[x] for x in o['sealed_docs']]; o['status'] = 'READY'
    txt = json.dumps(o, indent=1, sort_keys=True) + '\n'; assert '/scratch/jjyeung' not in txt and 'orch_n30' not in txt
    (OUT / 'over.json').write_text(txt); print('over', sha(OUT / 'over.json'))
