"""Published text through native admission and SQLite reader; no production bindings claimed."""
from collections import Counter
from copy import deepcopy
import hashlib, itertools, json, os, sqlite3, unittest
from pathlib import Path
from student_pilot.p3_provenance import digest, file_pin, load
from student_pilot.r2_adapters import normalize
from student_pilot.r2_intake import intake
from student_pilot.row_text_audit import reasons, check
from student_pilot.carrier_c1_run import Rows
from tests.test_r2_data_path import LANE, PROOFS, RECORDS, SOURCES, TinyProcessor


def write(path,value):
    path.write_text(json.dumps(value,indent=2)+'\n')


def envelope(folder,rows,stream,family):
    from student_pilot.r2_contract import CONTRACT
    from student_pilot.r2_grammar import SHARED_SHA256
    path=folder/'rows.jsonl';path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    pins={role:file_pin(RECORDS/name) for role,name in SOURCES.items()}
    write(folder/'coverage.json',dict(exclusions=pins,rows_sha256=file_pin(path)['sha256'],rows={
        r['qid']:dict(status='known',names=list({r['dataset']+'/'+r['scene'],r['provenance']['canonical']})) for r in rows}))
    result=dict(schema='r2-family-manifest-v1',family=family,stream=stream,count=len(rows),
        trace_contract=CONTRACT,validator_sha256=SHARED_SHA256,rows=file_pin(path),
        row_bindings={r['qid']:digest(r) for r in rows},scene_coverage=file_pin(folder/'coverage.json'),
        exclusions=pins,upstream_receipts=[],routing_policy='both-path-20261116',artifact_heads=['pose','depth'])
    write(folder/'MANIFEST.json',result)
    return folder/'MANIFEST.json'


class RecoveryAdmission(unittest.TestCase):
    def test_status_scope(self):
        for status in ('not seen','box unavailable','unresolved'):
            for field in ('target','suffix','response','trace'):
                self.assertIn('runtime_box_status',reasons({field:'<tool_response>\n'+status+'\n</tool_response>'}))
                for text in (status,'<tool_response>'+status,
                             '<tool_response>'+status+'</tool_response>\n'+status):
                    self.assertIn('runtime_box_status',reasons({field:text}))
        self.assertIn('runtime_box_status',reasons({'target':'<tool_response>not seen','trace':'</tool_response>'}))
        for phrase,reason in (('heading unavailable','heading_threshold_status'),
                              ('gravity guard','gravity_guard'),('tower_scale_rule','tower_scale_rule')):
            self.assertIn(reason,reasons({'target':'<tool_response>'+phrase+'</tool_response>'}))
        self.assertIn('tower_scale_provenance_not_from_head',reasons({'ground_record':{'geometry_mode':'tower'}}))
        with self.assertRaisesRegex(ValueError,'runtime_box_status'):
            check({'target':'<think>The object is not seen.</think><answer>A</answer>'},'synthetic')

    def test_real_slices_native_admission_and_reader(self):
        output=PROOFS/'recovery_rows';output.mkdir(parents=True,exist_ok=True)
        expected={'a0_recovery':1532,'a0_pool_abs_distance_reworded':2000,'a0_units':2000,'a0_room':476}
        rates=load(LANE/'work/kit07ca49df_meta/m/k/frame_rates.json')['by_scene']
        from student_pilot.carrier_c1_routing import alias_of
        results={}
        for family,total in expected.items():
            folder=output/family;folder.mkdir(exist_ok=True)
            lane=Path(os.environ.get('R2_LANE_ROOT',Path(__file__).resolve().parents[3]))
            source=lane/'work/rows_slices/slices_final'/(family+'.jsonl')
            stream='vqa' if family=='a0_room' else 'routing'
            counts=Counter();examples=[];source_hash=hashlib.sha256();refusals=Counter();reader_refusals=Counter()
            # At most 200 example rows are retained; each subsequent chunk overwrites them.
            with source.open('rb') as handle:
                remaining=iter(itertools.islice(handle,2000))
                while lines:=list(itertools.islice(remaining,200)):
                    rows=[]
                    for line in lines:
                        source_hash.update(line);raw=json.loads(line)
                        p=raw.get('provenance',{});si=raw.get('student_input',{})
                        indices=si.get('frame_indices') or raw.get('frame_indices') or p['frame_indices']
                        alias=p.get('alias') or (raw['dataset']+'/'+raw['scene'] if raw.get('dataset') else alias_of(raw['canonical']))
                        fps=si.get('fps') or p.get('fps_source',{}).get('value') or rates.get(alias,24.)
                        frames={raw['qid']:dict(fps=fps,total_num_frames=indices[-1]+1,
                            frames=[dict(path='/unavailable-rgb/'+str(i),sha256='a'*64,source_index=i) for i in indices])}
                        row=normalize(raw,frames)
                        self.assertEqual(row['target'],raw.get('target',raw.get('suffix')))
                        check(row,family);counts['text_admitted']+=1
                        row.update(answer_form='direct' if stream=='vqa' else 'routed',
                                   response_heads=[] if stream=='vqa' else ['pose','depth'])
                        rows.append(row);counts['read']+=1
                        if len(examples)<200:examples.append(dict(qid=raw['qid'],source_row_sha256=hashlib.sha256(line).hexdigest(),target_sha256=digest(row['target'])))
                    mp=envelope(folder,rows,stream,family)
                    admitted,report=intake(mp)
                    counts['admitted']+=len(admitted)
                    for refused in report['refusals']:
                        refusals[refused['reason']]+=1
                        self.assertTrue(refused['reason'].startswith(('excluded:','r0_room_refused:','EXTENT_')),refused)
                    # The native reader executes its b7 input audit on actual SQLite rows.
                    reader=Rows({'streams':{},'b7_inputs':{'fixture_binding':True}},TinyProcessor())
                    conn=sqlite3.connect(':memory:');reader.connections[stream]=conn
                    conn.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
                    for i,row in enumerate(rows):
                        conn.execute('INSERT INTO rows VALUES (?,?,?)',(i,json.dumps(row),'{}'))
                    try:
                        for i,item in enumerate(rows):
                            try:row,_=reader.row(stream,i)
                            except ValueError as error:
                                self.assertTrue(str(error).startswith(('r0_room_refused:','EXTENT_')));reader_refusals[str(error)]+=1
                            else:
                                self.assertEqual(row['target'],item['target']);counts['reader']+=1
                        if stream=='routing':
                            bad=deepcopy(rows[0]);bad['target']+='\nThe object is not seen.'
                            conn.execute('UPDATE rows SET row=? WHERE i=0',(json.dumps(bad),))
                            with self.assertRaisesRegex(ValueError,'runtime_box_status'):reader.row(stream,0)
                    finally:reader.close()
            results[family]=dict(counts=counts,refusals=refusals,reader_refusals=reader_refusals,source=str(source),sha256=source_hash.hexdigest(),examples=examples)
            write(folder/'RESULT.json',results[family])
            self.assertEqual(counts['read'],total)
            self.assertEqual(counts['text_admitted'],total)
            self.assertEqual(counts['admitted']+sum(refusals.values()),total)
            self.assertEqual(counts['reader']+sum(reader_refusals.values()),total)
        write(output/'RESULT.json',dict(families={k:{a:b for a,b in v.items() if a!='examples'} for k,v in results.items()},
            scope='Native admission and Rows.row; published text unchanged. Metadata-only RGB pins, fixture FPS 24 when absent from the supplied FPS map, and explicit pose/depth fixture binding; no RGB forward or production head/store binding claim.',
            exclusions='Every sealed exclusion record and withheld-room check executes unchanged. Coverage names use published alias/canonical metadata; independent full inventory remains unavailable.'))
