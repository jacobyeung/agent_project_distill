from pathlib import Path
from collections import Counter
from copy import deepcopy
import importlib.util,json,sys,re
L=Path(__file__).resolve().parents[2];B=L/'work/build21';O=B/'proofs/v2h';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(L/'work/tree_r1'),str(L/'work/n1fix2')]
from monitor9 import Monitor
m=Monitor(L/'work/tree_r1')
from student_pilot.p3_provenance import file_pin,pinned,load,write,sha256
from student_pilot import ground_rows
spec=importlib.util.spec_from_file_location('student_pilot.r1_coverage',B/'candidate/r1_coverage.py');C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
split=file_pin(L.parent/'ext/v2h/SPLIT_V2.json');guard=C.WordingExclusion(split)
R=Path('/scratch/jjyeung/n30_mirror/dist_diag/coverage_v2h')
files={name:file_pin(R/('COVERAGE_UNITS_V2H.jsonl' if name.endswith('units') else 'COVERAGE_DISTANCE_V2H.jsonl')) for name in C.PINS}
counts={};examples={};seen=set()
for name,pin in files.items():
    assert pin['sha256']==C.PINS[name]
    n=0;examples[name]=[]
    with pinned(pin).open() as f:
        for line in f:
            row=json.loads(line);guard.check(row);n+=1
            assert row['qid'] not in seen;seen.add(row['qid'])
            if 'ground_record' in row:record=dict(deepcopy(row['ground_record']),suffix=row['target'])
            else:
                events=[dict(call=x.group(1),response=x.group(2)) for x in re.finditer(r'(<(?:ground|gap)\b[^>\n]*>)\n(<tool_response>\n.*?\n</tool_response>)',row['suffix'],re.S)]
                record=dict(deepcopy(row),events=events)
            packed=ground_rows.pack(record,row['provenance']);ground_rows.validate(packed)
            if len(examples[name])<20:examples[name].append(dict(qid=row['qid'],question=row['question'],target=packed['target']))
    counts[name]=n
write(O/'VALIDATION.json',dict(status='PASS',files=files,split=split,counts=counts,validator='student_pilot.ground_rows.pack + validate',heldout_hits=0,examples=examples))
planted=load(pinned(split))['held_out'][0].format(a='chair',b='table',u='meters')
try:guard.check(dict(qid='planted',question=planted));raise AssertionError('Held-out wording admitted')
except ValueError as e:assert str(e).startswith('R1_HELD_OUT_WORDING:');write(O/'PLANTED.json',dict(status='REFUSE',error=str(e)))
m.save(O);print(json.dumps(counts))
