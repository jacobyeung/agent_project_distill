"""Project the authenticated H1 selection; optionally regenerate native inputs first."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
PARENT='eac5f9f01587803b2402f80cc310b75ec1f960270a6bc059416b1e1407b1e7c9'
def enc(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(enc(x)+'\n')

def project(parent):
    candidate=copy.deepcopy(parent);removed={}
    for name,entry in candidate['sources'].items():
        if entry.get('status')!='ELIGIBLE':continue
        types=entry.get('per_type',{})
        if not set(types)&{'room_size_estimation','absolute_size_room'}:continue
        if set(types)-{'room_size_estimation','absolute_size_room'}:raise ValueError('Mixed room source requires ordered index filtering')
        removed[name]=entry['retained']
        entry.update(status='DEFERRED',reason='moved_to_vqa_store')
        for key in ('selection','retained','per_type'):entry.pop(key)
    candidate['selected_rows']=sum(v.get('retained',0) for v in candidate['sources'].values() if v['status']=='ELIGIBLE')
    return candidate,removed

def main():
    p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,default=ROOT/'work/records/pool_selection_eac5f9f0.json')
    p.add_argument('--indices',type=Path,default=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx/k'))
    p.add_argument('--out',type=Path,default=ROOT/'out/proof/selection')
    p.add_argument('--native-receipt',type=Path,help='Fresh s1_pool.prepare receipt from complete H1 kit')
    p.add_argument('--implementation',type=Path);p.add_argument('--code-record',type=Path)
    p.add_argument('--unit-binding',type=Path);p.add_argument('--config',type=Path)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True,mode=0o700)
    if sha(a.parent)!=PARENT:raise ValueError('H1 selection pin differs')
    parent=load(a.parent)
    if a.native_receipt:
        import selection_parent
        native=selection_parent.project(load(a.native_receipt))
        native['implementation']=parent['implementation']
        for name,entry in native['sources'].items():
            pin=entry.get('selection');expected=parent['sources'][name].get('selection')
            if pin is not None:
                if expected is None or pin['sha256']!=expected['sha256'] or sha(pin['path'])!=expected['sha256']:
                    raise ValueError('Regenerated ordered index differs: '+name)
                entry['selection']=expected
        if native!=parent:raise ValueError('Native regeneration differs from parent selection')
    candidate,removed=project(parent)
    indices={}
    available={sha(f):f for f in a.indices.glob('pool_indices_*.json')}
    for name,e in parent['sources'].items():
        if 'selection' not in e:continue
        pin=e['selection'];f=available.get(pin['sha256'])
        if f is None:raise ValueError('Missing ordered index bytes: '+name)
        values=load(f)
        if len(values)!=e['retained'] or values!=sorted(set(values)):raise ValueError('Ordered index differs')
        indices[name]=dict(sha256=pin['sha256'],count=len(values),unchanged=name not in removed)
    unchanged={n:enc(v).encode()==enc(candidate['sources'][n]).encode() for n,v in parent['sources'].items() if n not in removed}
    if not all(unchanged.values()):raise ValueError('Non-room entry changed')
    if a.implementation:
        if not a.code_record:raise ValueError('Implementation rebind requires code record')
        implementation=load(a.implementation);files=load(a.code_record)['files']
        if any(files.get(n)!=h for n,h in implementation.items()):raise ValueError('Selection code closure differs')
        allowed={'student_pilot/carrier_c1_data.py','student_pilot/carrier_c1_run.py','student_pilot/type_mix.py'}
        if any(implementation.get(n)!=parent['implementation'].get(n) for n in set(implementation)|set(parent['implementation']) if n not in allowed):
            raise ValueError('Selection admission predicate changed')
        candidate['implementation']=implementation
    if a.unit_binding:
        if not a.native_receipt or not a.config:raise ValueError('Unit regeneration requires native parent receipt and config')
        from unit_binding import regenerate
        candidate=regenerate(candidate,load(a.unit_binding),a.unit_binding.parent,a.indices,
                             load(a.config)['s1_routing']['catalog'],a.out/'u')
        if hashlib.sha256((enc(candidate)+'\n').encode()).hexdigest()!=load(a.config)['s1_routing']['selection']['sha256']:
            raise ValueError('Regenerated unit selection differs from bound config')
    write(a.out/'r.json',candidate)
    write(a.out/'q.json',dict(schema='r1-selection-projection-v1',status='PASS',parent_sha256=PARENT,
        selection_sha256=sha(a.out/'r.json'),removed_source_rows=removed,removed_selection_rows=sum(removed.values()),
        selected_rows=candidate['selected_rows'],non_room_entry_bytes_equal=unchanged,indices=indices,
        tool_sha256=sha(__file__),native_regeneration_executed=a.native_receipt is not None,native_unit_regeneration_executed=a.unit_binding is not None,
        native_receipt=dict(path=str(a.native_receipt),sha256=sha(a.native_receipt)) if a.native_receipt else None,
        final_materialized_room_rows_expected=581,final_materialized_room_rows_verified=False,
        note='586 selected source rows precede final admission; 581 is the brief\'s materialized count. Full native regeneration needs the source archives absent locally.',
        production_authorized=False))
    print(enc(dict(selected=candidate['selected_rows'],removed=sum(removed.values()),non_room_equal=all(unchanged.values()))))

if __name__=='__main__':main()
