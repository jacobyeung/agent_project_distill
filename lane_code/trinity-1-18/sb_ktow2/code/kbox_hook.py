"""One named binding for the box kit's A0 evidence and frozen object rule."""
from common import *
HOOK=ROOT/'configs/KBOX_WINNING_BOX_RULE.json'

def evidence():
 cfg=read_json(HOOK);path=local(cfg['a0_path'])
 if not path.exists():return [],missing(path)
 sha(path);rows=[json.loads(s) for s in path.read_text().splitlines()]
 return [r for r in rows if r['arm']=='A0_deployed'],dict(status='AVAILABLE',path=str(path))

def compare(c,got):
 rows,binding=evidence();ref={r['row_id']:r for r in rows if r['capture']==c['canonical']}
 absent=[r['row_id'] for r in got if r['row_id'] not in ref]
 if absent:return dict(status='MISSING',capture=c['canonical'],expected_path=binding.get('path',binding.get('expected_path')),missing_A0_rows=absent,reason='Box kit has not emitted A0 for this capture')
 checks=[]
 for r in got:
  a=ref[r['row_id']];expected=a.get('response') or (f"distance {a['prediction']:.2f} m" if a['prediction'] is not None else a.get('refusal_code'))
  checks.append(dict(row_id=r['row_id'],equal=r['prediction']==a['prediction'] and r['response']==expected,prediction=r['prediction'],reference=a['prediction'],response=r['response'],reference_response=expected))
 return dict(status='PASS' if checks and all(r['equal'] for r in checks) else 'FAIL',capture=c['canonical'],rows=checks)
