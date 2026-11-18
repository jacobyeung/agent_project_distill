import copy,hashlib,itertools,json,os,sqlite3,sys
from pathlib import Path
from collections import Counter
L=Path(__file__).resolve().parents[2];B=L/'work/build10';P=L/'work/build12/proofs/extent_admission';P.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
from monitor9 import Monitor
monitor=Monitor(L/'work/tree_r1')
os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(P))
from student_pilot.p3_provenance import file_pin,digest
from student_pilot.extent_receipt import Extents
from student_pilot.r2_adapters import normalize
from student_pilot.row_text_audit import reasons
from student_pilot.carrier_c1_run import Rows
from student_pilot.r2_intake import intake
from tests.test_r2_build9_recovery import envelope,TinyProcessor
pin=file_pin(B/'inputs/extents.json');extents=Extents(pin)
def norm(raw):
    p=raw.get('provenance',{});si=raw.get('student_input',{})
    indices=si.get('frame_indices') or raw.get('frame_indices') or p['frame_indices']
    frames={raw['qid']:dict(fps=si.get('fps') or p.get('fps_source',{}).get('value') or 24.,total_num_frames=indices[-1]+1,
        frames=[dict(path='/unavailable-rgb/'+str(i),sha256='a'*64,source_index=i) for i in indices])}
    return normalize(raw,frames)
sources=json.loads((B/'inputs/row_sources.json').read_text());results={};sizes=[]
for family in ('recovery','absolute_distance','units'):
    folder=P/family;folder.mkdir(exist_ok=True);counts=Counter();refusals=Counter();admitted_units=Counter();admitted_statuses=Counter();admitted_datasets=Counter()
    reader=Rows(dict(streams={},extent_receipt=pin),TinyProcessor())
    conn=sqlite3.connect(':memory:');reader.connections['routing']=conn
    conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
    with Path(sources[family]['source']['path']).open('rb') as f:
        for batch,lines in enumerate(iter(lambda:list(itertools.islice(f,200)),[])):
            before=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file());assert before<=200_000_000
            rows=[]
            for i,line in enumerate(lines):
                row=norm(json.loads(line));extents.check(row,'routing');assert not reasons(row)
                row.update(answer_form='routed',response_heads=['pose','depth'])
                conn.execute('INSERT OR REPLACE INTO rows VALUES(?,?,?)',(i,json.dumps(row),'{}'))
                got,_=reader.row('routing',i);assert got['target']==row['target'];counts['reader']+=1
                rows.append(row)
            path=envelope(folder,rows,'routing',family);m=json.loads(path.read_text());m['extent_receipt']=pin;path.write_text(json.dumps(m))
            accepted,rep=intake(path);counts['intake']+=len(accepted);counts['source']+=len(rows)
            for item in accepted:
                g=item['row']['ground_record'];admitted_units[g.get('unit','meters')]+=1
                admitted_datasets[g['canonical'].split('/')[0]]+=1
                printed='\n'.join(e['response'] for e in g['events'])
                admitted_statuses['box unavailable' if 'box unavailable' in printed else 'not seen' if 'not seen' in printed else 'no failure']+=1
            refusals.update(r['reason'] for r in rep['refusals'])
            (folder/'intake.json').write_text(json.dumps(rep,indent=2))
            assert all(r['reason'].startswith(('excluded:','r0_room_refused:','R2 fallback calls again after a failed response')) for r in rep['refusals']),dict(refusals)
            if batch==0:
                samples=rows[:5];(folder/'samples.json').write_text(json.dumps(samples))
            after=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file());assert after<=200_000_000
            sizes.append(dict(family=family,batch=batch,before=before,after=after))
            print(family,batch,dict(counts),flush=True)
    # A changed box and a copied repair claim never inherit the recorded verdict.
    bad=copy.deepcopy(samples[0]);bad['ground_record']['program_audit']['independent_ordered_boxes'][0]['axesLengths'][0]/=2
    for item in (bad,dict(samples[0],qid='unaudited')):
        try:extents.check(item,'routing')
        except ValueError as e:assert 'UNAUDITED' in str(e)
        else:raise AssertionError('Unknown box admitted')
        conn.execute('INSERT OR REPLACE INTO rows VALUES(0,?,?)',(json.dumps(item),'{}'))
        try:reader.row('routing',0)
        except ValueError as e:assert 'EXTENT_' in str(e)
        else:raise AssertionError('Reader accepted changed geometry')
        path=envelope(folder,[item],'routing',family);m=json.loads(path.read_text());m['extent_receipt']=pin;path.write_text(json.dumps(m))
        accepted,rep=intake(path);assert not accepted
    reader.close();results[family]=dict(counts=counts,refusals=refusals,admitted_units=admitted_units,admitted_statuses=admitted_statuses,admitted_datasets=admitted_datasets,source=sources[family]['source'])
    (folder/'RESULT.json').write_text(json.dumps(results[family],indent=2)+'\n')
# Every old row whose box audit contains half is outside the repaired receipt.
old={name:Counter() for name in ('build9_recovery','build9_units','build9_pool_abs_distance_reworded')}
with Path('/scratch/jjyeung/orch_n30/rows_r1/out/extent_audit/ROW_AUDIT.jsonl').open() as f:
    for line in f:
        row=json.loads(line)
        if row['family'] in old and 'half' in row['box_statuses']:
            assert row['qid'] not in extents.receipt['rows'] or extents.receipt['rows'][row['qid']]['repair_sha256'] is None
            old[row['family']]['half_rows']+=1
from student_pilot.routing_requirements import blockers
from student_pilot.r2_mix import table
pop=json.loads((L/'work/build12/proofs/extents/RESULT.json').read_text())['families']
unit_counts=results['units']['admitted_units'];training=dict(recovery=results['recovery']['counts']['intake'],units={u:unit_counts[name] for u,name in [('cm','centimeters'),('ft','feet'),('in','inches')]})
assert not blockers(table(),training)
for bad in (None,{},dict(training,recovery=0),dict(training,units={'cm':1,'ft':1,'in':0})):
    assert blockers(table(),bad)
(P/'RESULT.json').write_text(json.dumps(dict(families=results,old_half_counts=old,routing_counts=training,
    scope='Real normalize/intake/Rows.row; metadata-only frame pins, no RGB/head forward; no full store materialized.'),indent=2)+'\n')
(P/'temporary_sizes.json').write_text(json.dumps(sizes))
monitor.save(P)
