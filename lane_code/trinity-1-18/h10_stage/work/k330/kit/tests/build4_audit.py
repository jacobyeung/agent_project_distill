"""Bounded CPU audit of pins, exact item membership and current syntax."""
import ast
import hashlib
import json
from pathlib import Path
from h1eval.items import K, load_manifest, sha
from h1eval.cli import modes
from h1eval.modes import DEFAULT_MODES, read_counts

review='eed915be8bf3c08de67045ff7adbfc3ab899d244da0d942be03e5a28f8657239'
assert sha(K/'tests/test_review.py')==review
inputs=[]
for name,digest in [('DEV_BACKDIR','730ed5363f91a19c99de6f903b947066f5da3b19c42e70f095fa518ac54c5f15'),
                    ('DEV_FORWARD_TWINS','4d6c3a9411d091d1f583a9e308525ca08dec55df05fe7c0a1c7c39e8043239af')]:
    path=K.parent/'work/items_in'/name/'TASKS.jsonl'
    assert sha(path)==digest
    inputs.append(dict(path=str(path),sha256=digest,bytes=path.stat().st_size))
m=load_manifest(K/'items/devs1_direct.json')
inv=json.loads((K/'items_sources/e193_items.json').read_text())['families']
expected={i for f in ('main','away','forward') for i in inv[f]['items']}
assert len(expected)==1825 and {r['id'] for r in m['items']}==expected
assert m['r0_check']['checked']==1825 and m['r0_check']['found']==0
assert {f:len(inv[f]['items']) for f in ('main','away','forward')}==dict(main=1525,away=150,forward=150)
report=dict(reviewer_sha256=review,inputs=inputs,item_sets={})
for name,count in [('devs1_routed',636),('devs1_direct',1825),('devs1_direct_main',1525),('revsi999',999)]:
    value=load_manifest(K/'items'/f'{name}.json')
    assert value['count']==count and value['r0_check']['checked']==count and value['r0_check']['found']==0
    report['item_sets'][name]={k:value[k] for k in ('count','item_set_sha256','r0_check')}
report['read_counts']={name:read_counts(load_manifest(K/'items'/f'{name}.json')['items'],modes(DEFAULT_MODES))
                       for name in ('devs1_routed','revsi999')}
files=[*K.joinpath('h1eval').rglob('*.py'),*K.joinpath('rows').glob('*.py'),*K.joinpath('tests').glob('*.py'),
       *K.joinpath('first_batch').glob('*.py')]
files += [K/'tree/student_pilot'/n for n in ('h1.py','h1_faithful.py','h1_r0.py','carrier_c1.py','carrier_c1_run.py','carrier_c1_routing.py')]
for p in files:ast.parse(p.read_text(),filename=str(p))
report['syntax_files']=len(files)
proof=json.loads((K/'logs/b4/first_batch_step2.json').read_text())
assert len(proof)==4 and all(r['step']==2 and r['own_rows']>0 and r['rows']==72 for r in proof)
report['step2_own_rows']=[r['own_rows'] for r in proof]
report['peak_rss_kib']=max(r['peak_rss_kib'] for r in proof)
report['operator_note_lines']=len((K/'h1eval/h10/RUN_H10.md').read_text().splitlines())
assert report['operator_note_lines']<=40
(K/'BUILD4_INPUT_SHA256.json').write_text(json.dumps(inputs,indent=2)+'\n')
(K/'logs/b4/audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
