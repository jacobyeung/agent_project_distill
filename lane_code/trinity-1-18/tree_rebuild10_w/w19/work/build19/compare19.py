from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build19';O=B/'proofs/regressions';O.mkdir(parents=True,exist_ok=True)
def load(p):return json.loads(p.read_text())
old=load(L/'work/build18/proofs/final/suite_tree/r2/results.json');new=load(B/'proofs/final/suite_tree/r2/results.json')
assert new['complete'] and not new['fatal']
missing=sorted(set(old['passed'])-set(new['passed']))
a=load(L/'work/build18/proofs/final/packet/results.json');b=load(B/'proofs/final/packet/results.json')
lost=sorted(k for k,v in a.items() if v['outcome']=='passed' and b.get(k,{}).get('outcome')!='passed')
extra_fail=sorted(k for k,v in b.items() if v['outcome']=='failed' and a.get(k,{}).get('outcome')!='failed')
result=dict(status='PASS' if not (missing or lost or extra_fail or new['failures'] or new['errors']) else 'FAIL',
    regressions=missing+lost+extra_fail,r2_tests=new['tests'],r2_failures=new['failures'],r2_errors=new['errors'],
    packet_test_inventory_equal=set(a)==set(b),packet={s:sum(v['outcome']==s for v in b.values()) for s in ('passed','failed','skipped')},
    qualified_packet_failures={k:v['detail'] for k,v in b.items() if v['outcome']=='failed'},
    sources=['work/build18/proofs/final/suite_tree/r2/results.json','work/build19/proofs/final/suite_tree/r2/results.json',
             'work/build18/proofs/final/packet/results.json','work/build19/proofs/final/packet/results.json'])
baseline=load(L.parent/'w18/out/TREE_SEAL.json');current=load(L/'out/TREE_SEAL.json')
assert baseline['tree_sha256']=='60e6ea72b5e9fcaa3e400e4d57f0816002e541c44c768097ea0303c78fdc5084'
before=baseline['files'];after=current['files']
changed=sorted(k for k,v in after.items() if before.get(k)!=v)
assert not (set(before)-set(after))

result['changed_source_files']=changed;result['baseline_seal']=baseline['tree_sha256'];result['current_seal']=current['tree_sha256']
(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');assert result['status']=='PASS' and result['packet_test_inventory_equal']
print(json.dumps({k:v for k,v in result.items() if k!='qualified_packet_failures'},indent=2))
