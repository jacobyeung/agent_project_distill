from pathlib import Path
import copy, gzip, hashlib, json, sqlite3, sys, unittest, time
from collections import Counter
from unittest.mock import patch

L = Path(__file__).resolve().parents[2]
D = Path(__file__).resolve().parent
sys.path[:0] = [str(L/'out/rcj'), str(L/'out/kit_qd/b'), str(L/'work/tree_r1c')]
import nd, x, ch, z
from student_pilot.extent_receipt import required
from student_pilot.p3_provenance import file_pin
R = L.parent/'work/d173817/173817'
contract = nd.load(L/'out/rcj/f.json')

def write(name, value):
    (D/name).write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')

def replay():
    old = nd.load(R/'nd.json'); chain = nd.load(R/'chain.json'); timing = nd.load(R/'timings.json')
    assert (timing['post_returncode'], timing['rdiff_returncode'], old['task_i']) == (1, 1, 'FAIL')
    assert chain['extent_scope']['tests']['cases']['other']['origin'] == 'sealed_reference'
    # The old publisher compared all fields lexically. Its complete leaf-path census
    # distinguishes descendant changes from copied siblings. Zero changes under a
    # field, plus the enclosing exact-field counter where available, proves identity.
    counts = {}
    for path in contract['content_field_paths']:
        changed = {p:n for p,n in old['paths'].items() if nd.in_path(p,path) or nd.in_path(path,p)}
        if changed: counts[path] = sum(changed.values())
    assert not counts, counts
    unclassified = {p:dict(count=n) for p,n in old['paths'].items()
        if not nd.category(p,contract) and not any(nd.in_path(p,k) for k in contract['content_field_paths'])
        and p not in ('/row_text','/target_text')}
    assert not unclassified, unclassified
    classes = Counter({k:v['path_differences'] for k,v in old['metadata_classes'].items()})
    rows = Counter({k:v['rows'] for k,v in old['metadata_classes'].items()})
    criteria = nd.decision(old['N_rows'],old['matched_rows'],old['N_without_P'],0,counts,
        unclassified,classes,rows,contract,chain,old['database_sha256'])
    assert [criteria[k]['status'] for k in ('a','b','c','d')] == ['PASS','PASS','PASS','DEFERRED_TO_DISCOVERY']
    after = copy.deepcopy(timing)
    after['task_a'] = dict(status='PASS',task_i='PASS',task_ii=old['task_ii'],task_iii=old['task_iii'],criteria=criteria)
    assert nd.load(R/'proc_check.json')['status'] == 'PASS'
    assert x.mode_r_status(after) == 0
    result = dict(status='PASS', source=str(R), source_sha256=nd.load(D/'inputs.json'),
        before=dict(post_returncode=1,rdiff_returncode=1,task_i='FAIL',ordinal_rows=39892,copied_rows=11663,other_origin='sealed_reference'),
        after=dict(decision_returncode=0,criteria=criteria),
        scope='Offline decision replay from authenticated published full-population counters and the real chain; no SQL-store or CPU-job rerun.',
        next_job='Recompute full SQL comparisons, staged-store census/control selection, and publish the actual process exit status.',
        literal=dict(role='information; superseded by ANSWER 1226Z',field_counts=old['content_field_counts'],metadata_classes=old['metadata_classes']))
    write('REPLAY173817.json',result)
    return after, criteria

class Tests(unittest.TestCase):
    def test_real_decision(self):
        replay()

    def test_every_encode_field_fails_exactly(self):
        for field in contract['content_field_paths']:
            if field == '/target':
                a,b=(0,'{}','{}'),(0,'{}','{ }')
            else:
                row={}; target=row
                parts=field.split('/')[2:]
                for part in parts[:-1]: target=target.setdefault(part,{})
                target[parts[-1]]='before'; a=(0,json.dumps(row),'{}')
                target[parts[-1]]='after'; b=(0,json.dumps(row),'{}')
            self.assertIn(field,[v[0] for v in nd.exact_fields(a,b,contract)],field)
        for a,b in [('1','1.0'),('"a"','"\\u0061"'),('null','{}')]:
            self.assertTrue(nd.exact_fields((0,'{"student_input":'+a+'}','{}'),(0,'{"student_input":'+b+'}','{}'),contract))
        self.assertTrue(nd.exact_fields((0,'{}','{}'),(0,'{"student_input":null}','{}'),contract))

    def test_metadata_is_not_encode_content(self):
        a=(0,json.dumps(dict(question='old',s1_source=dict(frame_binding=dict(fps_source='old')))),'{}')
        b=(42,json.dumps(dict(question='new',s1_source=dict(frame_binding=dict(fps_source='new')))),'{}')
        self.assertEqual(nd.exact_fields(a,b,contract),[])

    def test_each_required_result_controls_exit(self):
        after,criteria=replay()
        for field,value in [('returncode',7),('proc_returncode',1),('routing_types','FAIL')]:
            v=copy.deepcopy(after);v[field]=value;self.assertEqual(x.mode_r_status(v),1)
        for k in ('a','b','c'):
            v=copy.deepcopy(after);v['task_a']['criteria'][k]['status']='FAIL';self.assertEqual(x.mode_r_status(v),1)
        v=copy.deepcopy(after);v['rdiff_returncode']=1;self.assertEqual(x.mode_r_status(v),0)
        v['task_a']['criteria']['d']['status']='DEFERRED_TO_DISCOVERY';self.assertEqual(x.mode_r_status(v),0)

    def test_chain_requires_complete_same_database(self):
        old=nd.load(R/'nd.json');chain=nd.load(R/'chain.json')
        for change in ['pin','count','keys','refusal','missing']:
            c=copy.deepcopy(chain);r=c['streams']['routing']
            if change=='pin':r['databases'][0]['sha256']='0'*64
            if change=='count':r['rows_checked']-=1
            if change=='keys':r['checked_key_set_sha256']='0'*64
            if change=='refusal':r['refused_rows']=1
            if change=='missing':c={}
            got=nd.decision(43101,43101,0,0,{}, {},Counter(),Counter(),contract,c,old['database_sha256'])
            self.assertEqual(got['c']['status'],'FAIL',change)

    def test_real_staged_rows_preferred_and_census_complete(self):
        cfg=dict(extent_receipt=file_pin(D/'c072905b.json'),r1_training=dict(extent_pool_sources=nd.load(D/'SOURCES.json')['names']))
        rows=[json.loads(v['row']) for v in nd.load(D/'published/p_sample.json')['rows']]
        real=nd.load(D/'a0_pool_abs_distance_reworded_row.json')
        source=file_pin(D/'a0_pool_abs_distance_reworded_row.json')
        result=ch.scope_tests(cfg,rows,[(source,iter([real]))])
        self.assertEqual(result['status'],'PASS')
        self.assertEqual(result['cases']['other']['origin'],'database')
        self.assertEqual(result['cases']['other']['source_store'],source)
        self.assertEqual(result['stores'][-1]['rows'],1)
        self.assertEqual(result['stores'][-1]['other_rows'],1)
        self.assertEqual(result['stores'][0]['rows'],len(rows))
        write('CONTROL_REAL_STORE.json',result)

    def test_staged_store_authentication(self):
        root=D/('store_check_'+str(time.time_ns()));root.mkdir()
        row=nd.load(D/'a0_pool_abs_distance_reworded_row.json')
        p=root/'a';p.write_text(json.dumps(row)+'\n');pin=file_pin(p)
        found=ch.staged_stores({},root,{pin['sha256']:str(p)})
        self.assertEqual(len(found),1);self.assertEqual(list(found[0][1]),[row])
        with self.assertRaisesRegex(ValueError,'E99:pin'):ch.staged_stores({},root,{'0'*64:str(p)})
        database=root/'b'
        with sqlite3.connect(database) as c:
            c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
            c.execute('INSERT INTO rows VALUES(0,?,?)',((D/'a0_pool_abs_distance_reworded_row.json').read_text(),'{}'))
        pin=file_pin(database)
        cfg=dict(r1_training=dict(row_slice_inputs=dict(a=dict(path='/absent/a',sha256=pin['sha256']))))
        found=ch.staged_stores(cfg,root,{pin['sha256']:str(database)})
        self.assertEqual(len(found),1)
        self.assertEqual(found[0][0]['format'],'sql')
        self.assertEqual(list(found[0][1]),[row])

    def test_publisher_reports_encode_and_sql_mutations(self):
        from student_pilot.row_removals import Removals
        from student_pilot.s1_exclusions import Exclusions
        rules=(Removals([]),Exclusions(None),{})
        for name in ('prompt','frame','event','answer','sql'):
            root=D/('mutation_'+name+'_'+str(time.time_ns()));root.mkdir();(root/'scratch').mkdir()
            row=dict(qid='q',dataset='d1',scene='fixture_safe',student_input=dict(question='Q',frames=[]),
                routing=dict(question_type='camera_rotation',events=[],answer='A'))
            other=copy.deepcopy(row);target='{}'
            if name=='prompt':other['student_input']['question']='different'
            if name=='frame':other['student_input']['frames']=[dict(path='x',sha256='0'*64)]
            if name=='event':other['routing']['events']=[dict(kind='canonical_text',text='different')]
            if name=='answer':other['routing']['answer']='B'
            if name=='sql':target='{ }'
            for side,value,t in [('p',row,'{}'),('n',other,target)]:
                with sqlite3.connect(root/(side+'.sqlite')) as c:
                    c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
                    c.execute('INSERT INTO rows VALUES(0,?,?)',(json.dumps(value),t))
            p,n=root/'p.sqlite',root/'n.sqlite'
            with patch.object(nd,'GATE',z.sha(p)),patch.object(nd,'native_rules',return_value=rules):
                nd.publish(p,n,root/'missing',root/'rd0',root/'out',root/'scratch')
            value=nd.load(root/'out/nd.json')
            self.assertEqual(value['criteria']['a']['status'],'FAIL',name)
            self.assertEqual(value['criteria']['a']['differing_rows'],1,name)
            self.assertTrue(value['content_examples'],name)
            self.assertTrue((root/'out/nl.json.gz').is_file())

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    write('DECISION_TESTS.json',dict(status='PASS' if result.wasSuccessful() else 'FAIL',tests=result.testsRun,failures=[str(v) for v in result.failures],errors=[str(v) for v in result.errors]))
    raise SystemExit(not result.wasSuccessful())
