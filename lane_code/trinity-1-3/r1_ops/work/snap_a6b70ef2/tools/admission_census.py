"""Count real rows with the sealed predicates; never claim a frame/preparation proof."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import traceback
import re

ROOT = Path(__file__).resolve().parents[1]
SEALED = Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/base/tree_b01ce449')
SLICES = Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/rows_slices/slices_final')

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

def pin(path): return dict(path=str(path), sha256=sha(path))
def load(path): return json.loads(Path(path).read_text())
def write(path, value): Path(path).write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--receipt', type=Path)
    p.add_argument('--receipt-sha256')
    p.add_argument('--database', type=Path)
    p.add_argument('--out', type=Path, default=ROOT/'out/ADMISSION_BY_TYPE.json')
    a = p.parse_args()
    sys.path[:0] = [str(SEALED), str(SEALED/'generator/derivgen_v7')]
    from student_pilot import carrier_c1_run as run, carrier_c1_data as data
    from student_pilot import carrier_c1_routing as routing, ground_rows, s1_pool
    from student_pilot.s1_exclusions import Exclusions
    from student_pilot.row_removals import Removals
    # R0 is an H1 deployment addition; all other predicates come from b01ce449.
    import importlib.util
    spec = importlib.util.spec_from_file_location('student_pilot.h1_r0', ROOT/'work/tree/student_pilot/h1_r0.py')
    h0 = importlib.util.module_from_spec(spec);spec.loader.exec_module(h0)
    spec = importlib.util.spec_from_file_location('student_pilot.r1_policy', ROOT/'work/tree/student_pilot/type_mix.py')
    policy = importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
    k = ROOT/'work/records'
    cfg = load(ROOT/'work/reference/configs/h1_1.json')
    r1 = {**cfg, 'route_table': {**cfg['route_table'], 'room_size_estimation':'direct', 'absolute_size_room':'direct'}}
    rule = Exclusions(pin(k/'dev_scene_exclusions.json'), pin(k/'benchmark_scene_exclusions.json'))
    remove = Removals([{**v, 'path': str(k/Path(v['path']).name)} for v in cfg['remove_files']])
    reserve = h0.Reserve(pin(ROOT/'work/reference/auth/R0_ROOMS.txt'))
    held = {s:set(v) for s,v in load(k/'66c427e2.json').items()}
    bench = routing.load_exclusions(pin(k/'dafa4a9c.json'))
    reported = routing.load_exclusions(pin(k/'99e6eed6.json'))
    result = dict(schema='r1-row-admission-census-v1', status='PARTIAL',
        scope='Native row structure, route policy, label/scene/QID exclusions and H1 R0. No RGB reads, model, source census, division ancestry or full production preparation.',
        full_production_admission=False, sealed_tree=str(SEALED), predicates={
            n:sha(SEALED/n) for n in ('student_pilot/ground_rows.py','student_pilot/s1_pool.py',
                'student_pilot/carrier_c1_run.py','student_pilot/carrier_c1_data.py')},
        authority_files={p.name:pin(p) for p in k.iterdir() if p.is_file() and (p.name.startswith('remove_') or p.name in ('dev_scene_exclusions.json','benchmark_scene_exclusions.json','dafa4a9c.json','66c427e2.json'))},
        routing={}, direct_room={}, vqa_by_type={}, pool_by_type={})

    def eligibility(row, stream):
        reasons=[]
        if not remove.keep(row): reasons.append('label_removal')
        if run.held_row(row,stream,held,cfg.get('exclude_sources',{})): reasons.append('held_qid_or_source')
        matches=rule.matches(row)
        reasons.extend('scene_'+s for s,yes in matches.items() if yes)
        if reserve.excluded(row): reasons.append('r0_room')
        hit,_=run.excluded_row(row,bench,reported,stream)
        if hit and not rule.excluded(row) and not reserve.excluded(row): reasons.append('benchmark_stream_contamination')
        return reasons

    for family in ('a0_recovery','a0_units'):
        path=SLICES/(family+'.jsonl'); c=Counter(); reasons=Counter(); eligible_reasons=Counter(); examples={}; repack=Counter()
        with path.open() as f:
            for line in f:
                row=json.loads(line);c['rows']+=1
                try: excluded=eligibility(row,'routing')
                except (KeyError,ValueError,TypeError) as e: excluded=[type(e).__name__+': '+str(e)]
                if not excluded:c['eligible']+=1
                else:eligible_reasons.update(excluded)
                try:
                    s1_pool.validate_source_row(row,'packed')
                    routing.check_row(row)
                    c['syntax_admitted']+=1
                    if not excluded:c['admitted']+=1
                except (ValueError,KeyError,TypeError) as e:
                    reason=type(e).__name__+': '+str(e);reasons[reason]+=1
                    tb=traceback.extract_tb(e.__traceback__)[-1]
                    record=row.get('ground_record',{})
                    examples.setdefault(reason,dict(qid=row['qid'],line=c['rows'],raises=dict(file=tb.filename,line=tb.lineno,code=tb.line),fields=dict(not_seen=record.get('not_seen'),gt_agrees=record.get('gt_agrees'),training_admitted=record.get('training_admitted'),top_level_events_present='events' in row,record_events_present='events' in record)))
                try:
                    record=dict(row['ground_record'],suffix=row['target'])
                    packed=ground_rows.pack(record,row['provenance'])
                    routing.check_row(packed);repack['admitted']+=1
                except (ValueError,KeyError,TypeError) as e:repack[type(e).__name__+': '+str(e)]+=1
        result['routing'][family]=dict(input=pin(path),**{n:c[n] for n in ('rows','eligible','syntax_admitted','admitted')},
            refusal_reasons=dict(reasons), eligibility_refusals=dict(eligible_reasons),examples=examples,
            native_repack_diagnostic=dict(repack), admission_changed=False)

    def bucket():return dict(rows=0,eligible=0,admitted=0,h1_policy_admitted=0,refusal_reasons=Counter(),examples={})
    types=defaultdict(bucket);pools=defaultdict(bucket)
    def assess(row):
        refusals=eligibility(row,'vqa')
        try:
            data.layout_inputs(row,'duplicate',None,verify_partners=True)
            inputs=row['student_input'];anchors=data.anchor_slots(inputs)
            nested=anchors is not None and len(inputs['frames'])==64
            if not nested and (len(inputs['frames'])!=32 or len(inputs['frame_indices'])!=32):
                raise ValueError('C1 preservation rows require 32 pinned native frames (VQA: 64 with anchor_slots)')
            if nested and (len(anchors)!=32 or data.nested_indices([inputs['frame_indices'][k] for k in anchors])!=(inputs['frame_indices'],anchors)):
                raise ValueError('Nested VQA rows must hold the 32 anchors plus their bisection frames')
            if any(set(f)!={'path','sha256'} for f in inputs['frames']):raise ValueError('Input requires an exact path/SHA256 pin')
            if not isinstance(row.get('target'),str) or not row['target'].strip():raise ValueError('VQA requires an admitted answer target')
        except (KeyError,ValueError,TypeError) as e: refusals.append(type(e).__name__+': '+str(e))
        if row.get('question_type') in ('room_size_estimation','absolute_size_room'):
            if not policy.room_trace(row):refusals.append('room_requires_qualitative_trace_A2')
        h1drop=run.routed_type(row,cfg)
        if run.routed_type(row,r1):refusals.append('routed_type_rows_dropped')
        return refusals,h1drop
    def add(b,row,refusals,h1drop):
        b['rows']+=1
        if not [r for r in refusals if r!='routed_type_rows_dropped']:b['eligible']+=1
        if not refusals:b['admitted']+=1
        if not refusals and not h1drop:b['h1_policy_admitted']+=1
        b['refusal_reasons'].update(refusals)
        for reason in refusals:b['examples'].setdefault(reason,row['qid'])

    from student_pilot.s1_routing import Frames
    fk=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx/k')
    frame_pins={key:pin(fk/name) for key,name in [('map','frame_map.jsonl.gz'),('plan','frame_plan.json.gz'),('fps','frame_rates.json')]}
    for key,configkey in [('map','frame_map'),('plan','frame_plan'),('fps','fps_authority')]:
        if frame_pins[key]['sha256']!=cfg['s1_routing'][configkey]['sha256']:raise ValueError('Frame authority differs')
    frames=Frames(frame_pins['map'],frame_pins['plan'],fps_authority=frame_pins['fps'])
    merged=[]
    for family,path in [('room_m2',SLICES/'a0_room.jsonl'),('room_ft2',Path('/scratch/jjyeung/orch_n30/rows_a2/out/a2_room_ft2_v1/slice_a2_room_ft2.jsonl'))]:
        b=bucket()
        raw_reasons=Counter();materialization_reasons=Counter()
        with path.open() as f:
            for line in f:
                row=json.loads(line);raw_reasons.update(assess(row)[0])
                try:
                    inputs,audit=frames.resolve(row)
                    row={**row,'student_input':inputs}
                    refusals,h1drop=assess(row)
                    if not refusals:merged.append(row)
                except (KeyError,ValueError,TypeError) as e:
                    reason=type(e).__name__+': '+str(e);materialization_reasons[reason]+=1
                    refusals=[reason];h1drop=True
                add(b,row,refusals,h1drop)
        result['direct_room'][family]=dict(input=pin(path),**b,raw_refusal_reasons=dict(raw_reasons),
            materialization_refusal_reasons=dict(materialization_reasons),frame_authority=frame_pins)
    with (ROOT/'work/room_rows.jsonl').open('w') as f:
        for row in merged:f.write(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n')
    # Publish routing/room findings before any optional large-store IO.
    write(a.out if a.receipt is None else a.out.with_name('ADMISSION_PARTIAL.json'),result)
    if a.receipt is None:return
    if not a.receipt_sha256 or sha(a.receipt)!=a.receipt_sha256:raise ValueError('Receipt SHA differs')
    receipt=load(a.receipt); db=a.database or Path(receipt['database']['path'])
    if receipt['schema']!='c1-stream-v1' or receipt['stream']!='vqa':raise ValueError('Store is not native VQA')
    if sha(db)!=receipt['database']['sha256']:raise ValueError('Database SHA differs')
    conn=sqlite3.connect(db.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
    seen=set();samples={};seen_types=set();indices=defaultdict(list)
    traced=Counter();away=Counter()
    try:
        for expected,(i,encoded,target) in enumerate(conn.execute('SELECT i,row,target FROM rows ORDER BY i')):
            if i!=expected:raise ValueError('Noncontiguous database indices')
            row=json.loads(encoded);typ=row['question_type'];seen_types.add(typ)
            refusals,h1drop=assess(row)
            if row.get('pool')=='r1_room_traced':
                traced['rows']+=1
                traced['sealed_row_checks_pass']+=not [reason for reason in refusals if reason!='room_requires_qualitative_trace_A2']
                traced['qualitative_trace_pass']+=policy.room_trace(row)
                traced['eligible']+=not refusals
            if row['qid'].endswith('_away_opp'):
                away['rows']+=1;away['eligible']+=not refusals
                if row.get('pool')!='r1_away_opp':raise ValueError('Away marker mismatch')
            if row['qid'] in seen:refusals.append('duplicate_qid')
            seen.add(row['qid']);add(types[typ],row,refusals,h1drop)
            pool=str(row.get('pool') or row.get('provenance',{}).get('family') or 'unlabeled')
            add(pools[pool+'::'+typ],row,refusals,h1drop)
            if not refusals:
                indices[typ].append(i)
                if len(samples.setdefault(typ,[]))<5:samples[typ].append(dict(i=i,row=row,target=json.loads(target)))
        if sum(b['rows'] for b in types.values())!=receipt['count']:raise ValueError('Store count differs')
    finally:conn.close()
    result.update(status='COMPLETE_ROW_CENSUS', receipt=pin(a.receipt),database=dict(path=str(db),sha256=receipt['database']['sha256']),
        traced_room=dict(traced),reworded_away=dict(away,qid_suffix='_away_opp',pool='r1_away_opp'),vqa_by_type=dict(types),pool_by_type=dict(pools),types_covered=sorted(seen_types),all_types_covered=set(types)==seen_types,
        vqa_rows=sum(b['rows'] for b in types.values()),vqa_admitted=sum(b['admitted'] for b in types.values()))
    write(ROOT/'work/admitted_indices.json',dict(indices));write(ROOT/'work/real_samples.json',samples)
    write(a.out,result)
    print(json.dumps(dict(status=result['status'],rows=result['vqa_rows'],admitted=result['vqa_admitted'],types=len(types))))

if __name__=='__main__':main()
