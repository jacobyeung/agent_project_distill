"""Declaration-mode evidence with the exact delivered camera-wording source."""
from pathlib import Path
import os,sys,hashlib,json,gzip,sqlite3,importlib.util
from unittest.mock import patch
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];TREE=ROOT/'work/new';RO=ROOT.parent/'ro/orch_n30';CAM=RO/'fb_pack/cam/out'
sys.path.insert(0,str(TREE));sys.dont_write_bytecode=True
import torch;torch.set_num_threads(16)
from student_pilot import r1_routing as new
from student_pilot.r1_coverage import EXTRA_PINS,ROUTING_FAMILIES,deferred
from student_pilot.carrier_c1_routing import ROUTING_SCHEMA,render
from student_pilot.r1_camera_trace_form import rewrite_row,rewrite_text
from student_pilot.p3_provenance import file_pin
label=sys.argv[1] if len(sys.argv)>1 else 'A';baseline_tree=ROOT/'work'/('base' if label=='A' else 'baseA2')
root=ROOT/'work'/('declaration_'+label);root.mkdir(exist_ok=True)
inputs={}
def pin(p):
    value=file_pin(p);inputs[value['path']]=value['sha256'];return value
pin(Path(__file__));pin(ROOT/'out/SETUP.json')
for tree in (TREE,baseline_tree):
    for p in sorted((tree/'student_pilot').glob('*.py')):pin(p)
source=pin(RO/'sb_rowA/out/CAMERA_SOURCES.jsonl.gz');forms_path=CAM/'SOURCE_FORMS.json';pin(forms_path);forms=json.loads(forms_path.read_text())
assert source['sha256']==forms['source']['sha256']
build_path=CAM/'BUILD.json';pin(build_path);build=json.loads(build_path.read_text())
slice_pin=pin(CAM/'rows/camera_wording.jsonl');assert slice_pin['sha256']==build['rows']['sha256'];assert slice_pin['sha256'].startswith('e8cbda99')
rows=[];targets=[];mapping={r['source_qid']:r for r in forms['records']}
with gzip.open(source['path'],'rt') as f:
    for line in f:
        envelope=json.loads(line);row=json.loads(envelope['row']);m=mapping[row['qid']]
        assert hashlib.sha256(envelope['row'].encode()).hexdigest()==m['source_row_sha256']
        rows.append(row);targets.append(json.loads(envelope['target']))
items=[dict(row=json.loads(line),target={}) for line in Path(slice_pin['path']).read_text().splitlines()]
db=sqlite3.connect(':memory:');db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
for i,(row,target) in enumerate(zip(rows,targets,strict=True)):db.execute('INSERT INTO rows VALUES(?,?,?)',(i,json.dumps(row),json.dumps(target)))
db.commit();(root/'base.sqlite').write_bytes(db.serialize());db.close();dbpin=pin(root/'base.sqlite')
def write(name,value):
    p=root/name;p.write_text(json.dumps(value,sort_keys=True)+'\n');return pin(p)
base=write('base.json',dict(schema=ROUTING_SCHEMA,scene_role='train',heldout_overlap=0,database=dbpin,division=None,fixture_only=True,input_sha256={source['path']:source['sha256'],str(forms_path):inputs[str(forms_path)]}))
# Declaration schema forbids metadata keys; its authenticated pin is recorded here.
decl=write('declaration.json',dict(schema='r1-routing-slices-v1',bound=['camera_wording'],deferred={k:'controlled composition fixture: source omitted' for k in ROUTING_FAMILIES if k!='camera_wording'}))
intake=write('intake.json',dict(fixture_only=True,input_sha256={slice_pin['path']:slice_pin['sha256']}))
cfg=dict(r1_training=dict(routing_slice_declaration=decl));assert deferred(cfg) is False
spec=importlib.util.spec_from_file_location('student_pilot._camform2_baseline',baseline_tree/'student_pilot/r1_routing.py');baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)
def compose(module,output,config):
    observed=[]
    with patch.dict(EXTRA_PINS,{'camera_wording':slice_pin['sha256']}),patch.object(module,'Filters') as filters:
        def reason(row,stream):
            if 'r1_source' not in row:observed.append(hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest())
            return None
        filters.return_value.reason.side_effect=reason
        result=module.compose(base,{'camera_wording':slice_pin},[('camera_wording',slice_pin,items,intake)],config,output)
    assert observed==[hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest() for row in rows]
    return result
output=root/'same_path';first=compose(baseline,output,cfg)
old_hashes={p.name:file_pin(p)['sha256'] for p in output.iterdir() if p.is_file()};output.rename(root/'baseline_snapshot')
second=compose(new,output,cfg);new_hashes={p.name:file_pin(p)['sha256'] for p in output.iterdir() if p.is_file()}
assert first==second and old_hashes==new_hashes
policy=pin(TREE/'configs/r1_camera_trace_form_v1.json');enabled=compose(new,root/'enabled',dict(r1_training={**cfg['r1_training'],'camera_trace_form':policy}))
assert not enabled['refused'] and enabled['count']==len(rows)+len(items)
def stored(p):
    conn=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True)
    try:return [(json.loads(r),t) for r,t in conn.execute('SELECT row,target FROM rows ORDER BY i')]
    finally:conn.close()
old=stored(output/'rows.sqlite');fresh=stored(root/'enabled/rows.sqlite');counts=Counter();line_counts=Counter();rule_lines=Counter();unchanged=Counter();new_targets={r['qid']:r['target'] for r,t in fresh};old_targets={r['qid']:r['target'] for r,t in old};pairs=0;old_pairs=0
for (before,t0),(after,t1) in zip(old,fresh,strict=True):
    assert t0==t1
    if 'r1_source' in before:assert before==after;continue
    expected,ids=rewrite_row(before);assert after==expected
    if ids:counts[before['routing']['question_type']]+=1
    else:unchanged[before['routing']['question_type']]+=1
    for a,b in zip(before['routing']['events'],after['routing']['events'],strict=True):
        if a['kind'] in ('plan','canonical_text'):
            for x,y in zip(a['text'].splitlines(),b['text'].splitlines(),strict=True):
                if x!=y:
                    line_counts[before['routing']['question_type']]+=1
                    rule_lines.update(rewrite_text(x)[1])
    target,spans=render(after['routing']['events'],after['routing']['answer']);assert target==after['target']
    for x,y in zip(before['routing']['tool_output_spans'],after['routing']['tool_output_spans'],strict=True):assert before['target'][x['start']:x['end']]==after['target'][y['start']:y['end']]
    peer=mapping[before['qid']]['training_qid']
    if peer in new_targets:
        pairs+=1;assert after['target']==new_targets[peer];old_pairs+=before['target']==old_targets[peer]
receipt=enabled['camera_trace_form'];assert dict(counts)==receipt['rewritten_base_rows_by_type'];assert dict(line_counts)==receipt['changed_base_lines_by_type'];assert dict(rule_lines)==receipt['changed_base_lines_by_rule']
for p in (root/'baseline_snapshot/receipt.json',output/'receipt.json',root/'enabled/receipt.json'):pin(p)
result=dict(input_sha256=inputs,command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/compose_declaration.py '+label,baseline=label,scope='Declaration mode; exact real camera_wording bytes; Filters mocked to admit extract; EXTRA_PINS bound to delivered e8cbda99 source. Real Rows.row checks. Intake fixture is not production admission.',routing_deferred=False,source_pin=slice_pin,base_rows=len(rows),slice_rows=len(items),composed_rows=enabled['count'],absent_byte_identical=True,absent_file_sha256=old_hashes,enabled_rewrites=counts,changed_lines_by_type=line_counts,changed_lines_by_rule=rule_lines,unchanged_base=unchanged,slice_rows_unchanged=len(items),parallel_target_column_unchanged=len(fresh),filters_saw_original_base_rows=len(rows),base_slice_pairs=pairs,matching_pairs_on=pairs,matching_pairs_absent=old_pairs,enabled_receipt=receipt)
(ROOT/'out'/('COMPOSITION_'+label+'.json')).write_text(json.dumps(result,indent=2)+'\n')
(ROOT/'STATUS.md').write_text('Stage 4: Declaration-mode composition binds the exact delivered camera_wording source. Absent-field bytes match the comparison baseline at the same output path; enabled rows, rule counts, physical-line counts, counterpart targets, response spans and unchanged slice rows pass. Filters admit the controlled extract, so this is composition evidence, not production admission. Full CPU comparisons remain under review.\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('input_sha256','enabled_receipt')},indent=2),flush=True)
