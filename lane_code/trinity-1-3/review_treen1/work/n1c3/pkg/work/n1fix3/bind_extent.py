"""Stream audited row populations; retain only identities and bounded examples."""
from pathlib import Path
import collections,copy,hashlib,json,os,sys
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3';P=B/'proofs/extents';P.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.p3_provenance import digest,file_pin
from student_pilot.extent_receipt import content
from student_pilot.r2_adapters import normalize
R=Path('/scratch/jjyeung/orch_n30/rows_r1/out')
audit_paths=[R/'extent_audit/ROW_AUDIT.jsonl',R/'vehN_units/ROW_AUDIT_units_full.jsonl']
pins=[file_pin(p) for p in audit_paths]
assert pins[0]['sha256']=='7f820591af60dcbccea0ab5d0c84a1408ad6985c2d32f4c89004357126cd2918'
assert pins[1]['sha256']=='ab9cfc549bc2352f55f3ea82623e150a0abd7d800d762162993d9fbb8855dd30'
audits={};box_status={}
for p in audit_paths:
    with p.open() as f:
        for line in f:
            a=json.loads(line);audits[(a['family'],a['qid'])]=a
            for key,status in zip(a['box_keys'],a['box_statuses'],strict=True):
                seen=box_status.setdefault(key,set());seen.add(status)
                if {'half','full'} <= seen:raise ValueError('Conflicting decisive box verdict '+key)
sources=[('recovery','recovery_v3/rows.jsonl','58389a67f9a5b51abbc06e5953937b35541ef5effc4e70e6a35092d14f288473',994,'recovery_v2'),
 ('absolute_distance','vehN_pool_abs_distance/repaired/rows.jsonl','1b6bc0cee9831da378234f5cfb9e35352d5b30cf7cb5325f9fb7d6a135b53220',1579,'build9_pool_abs_distance_reworded'),
 ('units','vehN_units/repaired/rows_slice.jsonl','aa1432cde2aa3612e0d0e287c94aaa0aeb37dc175485a3ad044bca71f3e5ce9c',8577,'units_full')]
def boxkey(can,b):return hashlib.sha256(json.dumps([can,b],sort_keys=True,separators=(',',':')).encode()).hexdigest()[:24]
def norm(raw):
    p=raw.get('provenance',{});si=raw.get('student_input',{})
    indices=si.get('frame_indices') or raw.get('frame_indices') or p['frame_indices']
    frames={raw['qid']:dict(fps=si.get('fps') or p.get('fps_source',{}).get('value') or 24.,total_num_frames=indices[-1]+1,
        frames=[dict(path='/unavailable-rgb/'+str(i),sha256='a'*64,source_index=i) for i in indices])}
    return normalize(raw,frames)
receipt=dict(schema='full-extent-receipt-v1',audits=pins,rows={});summary={}
with (B/'DECISIONS.md').open('a') as f:
    f.write('\n- Audit evidence: an unknown result in the smaller audit and a full result in the full-unit audit are not conflicting decisive verdicts. Each family binds its named per-row audit; any half/full conflict refuses. Unknown rows in that family still refuse.\n')
row_sources=json.loads((B/'inputs/row_sources.json').read_text())
for family,relative,expected,count,audit_family in sources:
    p=R/relative;folder=P/family;folder.mkdir(exist_ok=True)
    totals=collections.Counter();units=collections.Counter();statuses=collections.Counter();datasets=collections.Counter();h=hashlib.sha256();sample=[]
    with p.open('rb') as f:
        for line in f:
            h.update(line);raw=json.loads(line);row=norm(raw);g=row.get('ground_record',row)
            repair=row.get('provenance',{}).get('repair');qid=row['qid'];can=g.get('canonical') or row['provenance']['canonical']
            source_qid=repair.get('source_qid',qid[:-3]) if repair else qid
            a=audits[(audit_family,source_qid)]
            boxes=g['program_audit']['independent_ordered_boxes'];assert len(boxes)==len(a['box_keys']) and boxes
            assert all(s in ('half','full') for s in a['box_statuses'])
            if not repair:assert all(s=='full' for s in a['box_statuses'])
            else:assert qid==source_qid+'_x2'
            for box,key,status in zip(boxes,a['box_keys'],a['box_statuses'],strict=True):
                original=copy.deepcopy(box)
                if status=='half':original['axesLengths']=[v/2 for v in box['axesLengths']]
                assert boxkey(can,original)==key,(family,qid,key)
            entry=dict(content_sha256=digest(content(row)),source_line_sha256=hashlib.sha256(line).hexdigest(),
                box_statuses=['full']*len(boxes),audit_family=audit_family,audit_qid=source_qid,
                audit_row_sha256=digest(a),repair_sha256=digest(repair) if repair else None)
            assert qid not in receipt['rows'];receipt['rows'][qid]=entry
            totals['rows']+=1;totals['repaired' if repair else 'full']+=1
            units[g.get('unit','meters')]+=1;datasets[can.split('/')[0]]+=1
            printed='\n'.join(e['response'] for e in g.get('events',[]) if isinstance(e.get('response'),str))
            status='box unavailable' if 'box unavailable' in printed else 'not seen' if 'not seen' in printed else 'no failure'
            statuses[status]+=1
            if len(sample)<200:sample.append(dict(qid=qid,source_line_sha256=entry['source_line_sha256'],content_sha256=entry['content_sha256']))
    assert h.hexdigest()==expected and totals['rows']==count,(family,totals,h.hexdigest())
    summary[family]=dict(source=dict(path=str(p),sha256=expected),counts=totals,units=units,statuses=statuses,datasets=datasets)
    (folder/'EXAMPLES.json').write_text(json.dumps(sample,indent=2)+'\n')
    row_sources[family]=dict(source=dict(path=str(p),sha256=expected),variant='repaired',remote_source=None,
        status='Extent-certified source; complete scene admission and remote staging remain required')
    print(family,dict(totals),dict(statuses),flush=True)
# Filtered inputs remain selectable without adding any unaudited row to the receipt.
for family,relative in [('recovery','recovery_v2x/rows.jsonl'),('absolute_distance','vehN_pool_abs_distance/filtered/rows.jsonl'),('units','vehN_units/filtered/rows_slice.jsonl')]:
    p=R/relative
    row_sources[family]['filtered_source']=file_pin(p)
path=B/'inputs/extents.json';path.write_text(json.dumps(receipt,separators=(',',':'))+'\n')
(B/'inputs/row_sources.json').write_text(json.dumps(row_sources,indent=2)+'\n')
(P/'RESULT.json').write_text(json.dumps(dict(families=summary,receipt=file_pin(path),audits=pins,
    scope='Per-box keys replayed against supplied independent audit; no rasters reloaded. Normalized supervision SHA binds text, geometry and repair; frame joins remain separately gated.'),indent=2)+'\n')
