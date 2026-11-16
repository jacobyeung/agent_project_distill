from pathlib import Path
import collections,gzip,hashlib,json,sys
L=Path(__file__).resolve().parents[1];x=L/'work/real/x';out=L/'out'
sys.path.insert(0,str(L/'work/trees/tree_r1_rehearsal'))
from student_pilot.training_contract import audit_training_contract
manifest=json.loads((x/'66caacf5c9191457.json').read_text())
excluded=collections.defaultdict(list)
for p in x.glob('*.tsv'):
    with p.open() as f:
        for line in f:
            fields=line.strip().split('\t')
            if len(fields)>=2:excluded[tuple(fields[:2])].append(str(p))
ledger=out/'REAL_ROW_ADMISSION_LEDGER.jsonl';counts=collections.Counter()
with ledger.open('w') as dest:
    for s in manifest['sets']:
        role='packed' if 'packed' in s['files'] else 'rows'
        pin=s['files'][role];p=x/(pin['sha256'][:16]+'.jsonl.gz')
        with gzip.open(p,'rt') as f:
            for line_no,line in enumerate(f,1):
                row=json.loads(line);kind=row.get('question_type',row.get('type'))
                if kind not in ('object_abs_distance','room_size_estimation','route_planning'):continue
                verdict=audit_training_contract([row])[0];assert verdict is None
                exclusions=excluded[(s['name'],str(row['qid']))]
                entry=dict(source=str(p),line=line_no,set=s['name'],qid=row['qid'],question_type=kind,
                    final_contract_verdict=verdict,sealed_pool_eligible=not exclusions,
                    exclusion_lists=exclusions,actual_leg_consumption='not established by supplied package')
                dest.write(json.dumps(entry)+'\n');counts[kind]+=1
audit=json.loads((out/'REAL_ROW_AUDIT.json').read_text())
h=hashlib.sha256()
with ledger.open('rb') as f:
    for block in iter(lambda:f.read(1048576),b''):h.update(block)
audit['per_row_comparison']=dict(path=str(ledger),sha256=h.hexdigest(),counts=dict(counts),representation='Packed programs and direct rows; raw admitted mirrors are not duplicated.')
(out/'REAL_ROW_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
print(dict(counts),ledger.stat().st_size)
