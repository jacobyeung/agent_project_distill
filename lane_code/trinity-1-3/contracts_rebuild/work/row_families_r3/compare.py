"""Compare complete row bytes, enumerate ON deltas, and audit each rendered ON row."""
import argparse,copy,hashlib,json,sys
from collections import Counter,defaultdict
from pathlib import Path
L=Path(__file__).resolve().parents[2];W=Path(__file__).resolve().parent
sys.path.insert(0,str(L/'work/trees/r6_r3'))
from trace_format.contracts import contract_epoch
from student_pilot.training_contract import audit_training_contract
ap=argparse.ArgumentParser();ap.add_argument('--output',default='comparison.json');a=ap.parse_args()
arms={arm:json.loads((W/f'{arm}.json').read_text()) for arm in ('base','off','on')}
for arm,data in arms.items():
    for r in data['results']:r['artifact_source']=str(W/f'{arm}.json')
    for extra in (W/f'supplement_{arm}.json',W/f'keypoints_{arm}.json'):
        if extra.exists():
            other=json.loads(extra.read_text())['results']
            for r in other:r['artifact_source']=str(extra)
            data['results'].extend(other)
index={arm:{(r['family'],r['variant']):r for r in data['results']} for arm,data in arms.items()}
manifest=json.loads((L/'out/PATCH_MANIFEST_R3.json').read_text())
changed=set(manifest['files'])
def encoded(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
def diffs(x,y,path=''):
    if type(x)!=type(y):return [(path,x,y)]
    if isinstance(x,dict):
        out=[]
        for k in sorted(set(x)|set(y)):
            p=path+'/'+str(k).replace('~','~0').replace('/','~1')
            if k not in x or k not in y:out.append((p,{'missing':True} if k not in x else x[k],{'missing':True} if k not in y else y[k]))
            else:out+=diffs(x[k],y[k],p)
        return out
    if isinstance(x,list):
        if len(x)!=len(y):return [(path,x,y)]
        return [d for i,(u,v) in enumerate(zip(x,y)) for d in diffs(u,v,path+'/'+str(i))]
    return [] if x==y else [(path,x,y)]

reasons={
 'heading_fields_withheld':'out/REVIEW_DISPOSITION_R3.md',
 'metric_only_boxes':'out/REVIEW_DISPOSITION_R3.md',
 'mdg_bridge':'out/CONTRACTS_REPORT_R3.md',
 'normalized_phrases':'out/REVIEW_DISPOSITION_R3.md',
 'open_vocabulary_names':'out/PATCH_MANIFEST_R3.json',
 'statuses':'out/REVIEW_DISPOSITION_R3.md',
}
def mapping(family,variant,path,old,new):
    # This is a conservative first-pass classification. Unmapped changes remain
    # defects until a reviewed, exact case-specific explanation is recorded.
    nadir=variant.startswith('nadir_positive')
    if family=='runtime/mdg_distance':return 'mdg_bridge'
    if nadir and any(k in path for k in ('/metric_only','/metric_metadata','/metric_values','/metric_gaps','/full_precision_box','/camera_centre_f1')):return 'metric_only_boxes'
    if nadir and any(k in path for k in ('/suffix','/target','/response','/text','/spans','/segments','/tool_output_spans','/suffix_tokens')):
        return 'heading_fields_withheld'
    if nadir and '/program_audit/unrounded_' in path and isinstance(old,(int,float)) and isinstance(new,(int,float)) and abs(old-new)<1e-10:return 'metric_only_boxes'
    if family=='recovery/normalized_phrase':return 'normalized_phrases'
    if family=='recovery/open_vocabulary':return 'open_vocabulary_names'
    return None

families=defaultdict(list);all_defects=[];candidate_bindings={}
for key in sorted(set().union(*(set(v) for v in index.values()))):
    family,variant=key;entries={arm:idx.get(key) for arm,idx in index.items()}
    if any(x is None for x in entries.values()):
        all_defects.append(dict(family=family,variant=variant,reason='arm_sample_missing'));continue
    b,o,n=(entries[x] for x in ('base','off','on'))
    valid=lambda r:r['status']=='rendered'
    off_equal=(valid(b)==valid(o) and (encoded(b['row'])==encoded(o['row']) if valid(b) else (b['error_type'],b['error'])==(o['error_type'],o['error'])))
    outcome=dict(variant=variant,statuses={k:v['status'] for k,v in entries.items()},off_parity=off_equal,off_row_byte_parity=off_equal if valid(b) and valid(o) else None,
                 source_paths={arm:v['artifact_source'] for arm,v in entries.items()},audit=None,differences=[],refusals={arm:{k:v[k] for k in ('error_type','error','traceback')} for arm,v in entries.items() if not valid(v)})
    outcome['row_sha256']={arm:hashlib.sha256(encoded(v['row'])).hexdigest() for arm,v in entries.items() if valid(v)}
    if not off_equal:all_defects.append(dict(family=family,variant=variant,reason='OFF_base_mismatch',differences=diffs(b.get('row'),o.get('row'))))
    if valid(n):
        row=n['row']
        # These names come from the fixture's declared GT instance labels, not
        # the generated operands or any new inference from its answer text.
        names=row.get('candidate_phrases',['chair','table','plant','floor'])
        binding={str(row.get('qid')):names}
        candidate_bindings[family+'/'+variant]=dict(qid=str(row.get('qid')),phrases=names,source_path=str(W/'render_arms.py'),note='clip_for labels; recovery uses its explicitly declared fixture names')
        with contract_epoch(True):
            unbound=audit_training_contract([row])[0]
            verdict=audit_training_contract([row],manifest=binding)[0]
        outcome['audit']=dict(verdict='admitted' if verdict is None else 'deferred',reason=verdict,unbound_verdict='admitted' if unbound is None else 'deferred',unbound_reason=unbound,
            candidate_binding_source=str(W/'candidate_bindings.json'),source_path=str(L/'work/trees/r6_r3/student_pilot/training_contract.py'))
        # Also audit the exact base row under the ON rules to distinguish existing
        # format incompatibility from a new rendering regression.
        if valid(b):
            with contract_epoch(True):outcome['base_row_under_on_audit']=audit_training_contract([b['row']],manifest={str(b['row'].get('qid')):names})[0]
    if valid(b) and valid(n):
        for path,old,new in diffs(b['row'],n['row']):
            reason=mapping(family,variant,path,old,new)
            outcome['differences'].append(dict(path=path,base=old,on=new,contract_change=reason,reason_source=str(L/reasons[reason]) if reason else None))
            if reason is None:all_defects.append(dict(family=family,variant=variant,reason='unexplained_ON_difference',path=path))
    elif valid(b)!=valid(n):
        all_defects.append(dict(family=family,variant=variant,reason='ON_renderability_changed',base=b['status'],on=n['status'],error=n.get('error')))
    families[family].append((entries,outcome))

records=[]
for name,samples in families.items():
    executed=set().union(*(set(e['executed_source_paths']) for entries,_ in samples for e in entries.values()))
    # Fixture constructors are excluded from production reachability for untouched
    # consumers. The dynamic trace is retained independently for inspection.
    touched=bool(executed&changed)
    if name.startswith(('point_program/','control/','headcall/','pointing/','camera/','camera_leaf/')):touched=False
    rows={arm:sum(entries[arm]['status']=='rendered' for entries,_ in samples) for arm in arms}
    records.append(dict(family=name,entry_point=samples[0][0]['base']['entry_point'],touched=touched,
        touched_paths=sorted(executed&changed) if touched else [],executed_paths=sorted(executed),
        rows_per_arm=rows,attempts_per_arm=len(samples),off_parity=all(o['off_parity'] for _,o in samples),
        on_difference_count=sum(len(o['differences']) for _,o in samples),
        audit_counts=dict(Counter(o['audit']['verdict'] for _,o in samples if o['audit'])),
        audit_reasons=dict(Counter(o['audit']['reason'] for _,o in samples if o['audit'] and o['audit']['reason'])),
        samples=[o for _,o in samples],source_paths=sorted(set(e['artifact_source'] for entries,_ in samples for e in entries.values()))+[str(W/'render_arms.py'),str(W/'extra_families.py'),str(W/'program_families.py'),str(W/'supplement.py')]))
near=[o for r in records if r['family']=='ground/object_abs_distance' for o in r['samples'] if o['variant'].startswith('nadir_positive')]
near_ok=bool(near) and all(o['audit'] and o['audit']['verdict']=='admitted' and o['statuses']['on']=='rendered' for o in near)
if not near_ok:all_defects.append(dict(reason='served_near_nadir_distance_not_admitted'))
summary=dict(families=len(records),rendered_rows={arm:sum(r['rows_per_arm'][arm] for r in records) for arm in arms},off_parity=all(r['off_parity'] for r in records),near_nadir_distance_admitted=near_ok,
             on_audits=dict(Counter(o['audit']['verdict'] for r in records for o in r['samples'] if o['audit'])),unexplained_or_failed_checks=len(all_defects),source_path=str(W/a.output))
out=dict(summary=summary,families=records,defects=all_defects,comparison='UTF-8 JSON of the entire returned row with preserved dictionary insertion order, compact separators and no field filtering. Original text, events and private audits are all compared byte for byte.',source_paths=[str(W/f'{arm}.json') for arm in arms])
(W/'candidate_bindings.json').write_text(json.dumps(candidate_bindings,indent=2))
(W/a.output).write_text(json.dumps(out,indent=2,allow_nan=False))
print(json.dumps(summary));print(json.dumps(dict(Counter(d['reason'] for d in all_defects))))
