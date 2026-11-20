import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import ast, copy, gzip, importlib.util, math, sqlite3, unittest
from unittest.mock import patch
from types import SimpleNamespace

def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
nd=module('nd_test',L/'out/rcj/nd.py')
x=module('x_test',L/'out/rcj/x.py')
old=module('old_x_test',L/'attic/build24m4o/out/rcj/x.py')
f0=module('f0_test',kit('qd')/'b/f0.py')
F=D/'fixtures';F.mkdir()

def db(path, rows, native=False):
    path.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(path) as c:
        c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
        c.executemany('INSERT INTO rows VALUES (?,?,?)',rows)
        if native:
            c.execute('CREATE TABLE candidates(k INTEGER PRIMARY KEY,qid TEXT,origin TEXT)')
            c.execute('CREATE TABLE membership(i INTEGER PRIMARY KEY,k INTEGER)')
            c.execute('CREATE TABLE pool_qids(qid TEXT PRIMARY KEY)')
    return path

def fixture(name):
    root=F/name;root.mkdir();out=root/'o';out.mkdir();scratch=root/'s';scratch.mkdir()
    source=dict(dataset='d1',scene='v0',qid='q0',s1_source={'name':'U_Faithful'},
                a={'b':[1,2],'x':None},target='abc',text='x'*250)
    p=[(0,json.dumps(source),'{}')]
    nrow=copy.deepcopy(source);nrow['a']['b']=[1,3,4];nrow['a'].pop('x');nrow['a']['y']=None;nrow['text']='z'*250;nrow['target']='def'
    n=[(10,json.dumps(nrow),'{}')]
    for i in range(1,6):
        r=dict(dataset='d1',scene='v0',qid='q'+str(i),routing={'question_type':'k'})
        p.append((i,json.dumps(r),'{}'))
    p.append((6,json.dumps(dict(dataset='d1',scene='v0',qid='q6')),'plain'))
    n.append((11,json.dumps(dict(dataset='d1',scene='v0',qid='q6')),'changed'))
    pdb=db(root/'p.sqlite',p);ndb=db(root/'selection/rows.sqlite',n,True)
    with sqlite3.connect(ndb) as c:
        c.execute("INSERT INTO candidates VALUES(0,'q2','legacy')")
        c.execute("INSERT INTO pool_qids VALUES('q2')")
    write(ndb.parent/'materialization.json',dict(contract_deferred_qids={'contract_x':dict(count=1,qids=['q3'])}))
    request=root/'request.json';write(request,dict(schema='p_sample_request_v1',uniform_positions=[0,1,2,3,4,5,6]))
    rd=out/'rd0';rd.mkdir()
    absent=[dict(key=nd.key(json.loads(r[1])),i=r[0],removal_list_sha256s=['a'*64] if r[0]==1 else []) for r in p if r[0] in range(1,6)]
    (rd/'rdiff.json.gz').write_bytes(gzip.compress(nd.raw(dict(P_absent=absent)),mtime=0))
    write(rd/'rdiff_summary.json',dict(inputs=dict(P=dict(sha256=z.sha(pdb)),N=dict(sha256=z.sha(ndb))),rdiff_sha256=z.sha(rd/'rdiff.json.gz')))
    return root,pdb,ndb,request,rd,out,scratch

class Tests(unittest.TestCase):
    def run_fixture(self,name,**kw):
        v=fixture(name)
        with patch.object(nd,'GATE',z.sha(v[1])):
            result=nd.publish(*v[1:])
        return v,result

    def test_full_fields_keys_counts_and_recorded_reasons(self):
        v,result=self.run_fixture('full')
        root,pdb,ndb,req,rd,out,scratch=v
        ns=nd.load(out/'n_sample.json');diff=nd.load(out/'nd.json')
        self.assertEqual(diff['matched_rows'],2)
        self.assertEqual(diff['paths'],{'/i':2,'/row/a/b/1':1,'/row/a/b/2':1,'/row/a/x':1,'/row/a/y':1,'/row/target':1,'/row/text':1,'/target':1})
        self.assertEqual(ns['requested'],13)  # Seven uniform, one source, five absent picks.
        self.assertEqual(len(ns['rows']),3);self.assertEqual(len(ns['absent']),10)
        self.assertEqual(ns['rows'][0]['i'],10);self.assertEqual(ns['rows'][0]['P_i'],0)
        self.assertEqual(ns['rows'][0]['row'],sqlite3.connect(ndb).execute('SELECT row FROM rows WHERE i=10').fetchone()[0])
        self.assertTrue(all(len(s[side].get('value',''))<=200 for r in diff['samples'] for s in r.get('changes',[]) for side in ('P','N')))
        bypath={v['path']:v for v in diff['samples'][0]['changes']}
        self.assertFalse(bypath['/row/a/x']['N']['present']);self.assertEqual(bypath['/row/a/x']['P']['value'],'null')
        na=json.loads(gzip.decompress((out/'na.json.gz').read_bytes()))['rows']
        self.assertEqual({r['key'][2]:r['rule'] for r in na},{'q2':'pool_qid_wins','q3':'contract_x','q4':'unknown','q5':'unknown'})
        self.assertEqual(diff['absent_unlisted'],4)
        self.assertLess(result['bytes'],5_000_000)
        self.assertEqual(sum((out/n).stat().st_size for n in result['files']),result['bytes'])
        self.assertEqual(z.sha(pdb),ns['P_database_sha256']);self.assertEqual(z.sha(ndb),ns['database_sha256'])

    def test_native_failure_without_materialization_keeps_unknown(self):
        v=fixture('refusal');p=v[2].parent/'materialization.json';p.rename(p.with_name('saved.json'))
        with patch.object(nd,'GATE',z.sha(v[1])):nd.publish(*v[1:])
        rows=json.loads(gzip.decompress((v[5]/'na.json.gz').read_bytes()))['rows']
        self.assertEqual(next(r for r in rows if r['key'][2]=='q3')['rule'],'unknown')

    def test_missing_rdiff_has_explicit_unknown_listing(self):
        v=fixture('no_rd');v[4].rename(v[0]/'saved_rd')
        with patch.object(nd,'GATE',z.sha(v[1])):nd.publish(*v[1:])
        d=nd.load(v[5]/'nd.json');self.assertIsNone(d['absent_unlisted']);self.assertEqual(d['absent_listing_unknown'],5)
        self.assertEqual(nd.load(v[5]/'n_sample.json')['requested'],8)

    def test_wrong_gate_and_inherited_override_refuse(self):
        v=fixture('gate')
        with patch.dict(os.environ,PS_GATE=z.sha(v[1])):
            self.assertEqual(nd.reader().GATE,nd.GATE)
            with self.assertRaisesRegex(SystemExit,'PS_GATE_FAILED'):nd.publish(*v[1:])
        self.assertFalse((v[5]/'n_sample.json').exists())

    def test_stale_rdiff_refuses(self):
        v=fixture('stale');p=v[4]/'rdiff_summary.json';d=nd.load(p);d['inputs']['N']['sha256']='0'*64;write(p,d)
        with patch.object(nd,'GATE',z.sha(v[1])),self.assertRaisesRegex(ValueError,'E96:rd'):nd.publish(*v[1:])
        self.assertFalse((v[5]/'nd.json').exists())

    def test_cap_checks_combined_bytes_before_output(self):
        v=fixture('cap')
        with patch.object(nd,'GATE',z.sha(v[1])),patch.object(nd,'LIMIT',1),self.assertRaisesRegex(ValueError,'E96:size'):nd.publish(*v[1:])
        self.assertFalse((v[5]/'n_sample.json').exists())

    def test_type_pointer_and_serialization(self):
        self.assertEqual([r[0] for r in nd.changes({'a/b':{'~':True}}, {'a/b':{'~':1}}, '/row')],['/row/a~1b/~0'])
        self.assertEqual([r[0] for r in nd.fields((0,'{"a":1}','{}'),(0,'{ "a": 1 }','{ }'))],['/row_text','/target_text'])
        self.assertEqual(list(nd.changes({}, {}, '/row')),[])

    def test_pinned_scene_state_matches_native_on_all_job_keys(self):
        from student_pilot.s1_exclusions import Exclusions
        from student_pilot.p3_provenance import file_pin
        root=F/'state';(root/'selection').mkdir(parents=True);(root/'u').mkdir()
        dev=T/'student_pilot/r2_dev_merged.json'
        bench=L/'work/build24m4n/inputs/3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970'
        cfg={}
        for label,path in [('dev_scene_exclusions',dev),('benchmark_scene_exclusions',bench)]:
            h=z.sha(path);(root/'u'/h).write_bytes(path.read_bytes());cfg[label]=dict(path='u/'+h,sha256=h)
        write(root/'n.json',cfg)
        rules,pins=nd.scene_state(root/'selection/rows.sqlite',nd.reader())
        self.assertEqual(len(pins),3)
        native=Exclusions(file_pin(dev),file_pin(bench))
        rd=json.loads(gzip.decompress((E/'rd0/rdiff.json.gz').read_bytes()))
        absent=0;absent_keys={tuple(r['key']) for r in rd['P_absent']}
        for record in rd['N']+rd['P_absent']:
            row=dict(dataset=record['key'][0],scene=record['key'][1],qid=record['key'][2])
            self.assertEqual(nd.scene_matches(row,rules),[k for k,v in native.matches(row).items() if v])
            if tuple(record['key']) in absent_keys and not record['removal_list_sha256s']:
                self.assertEqual(nd.scene_matches(row,rules),['dev']);absent+=1
        self.assertEqual(absent,4768)
        h=cfg['dev_scene_exclusions']['sha256'];(root/'u'/h).rename(root/'saved')
        self.assertNotIn('dev',nd.scene_state(root/'selection/rows.sqlite',nd.reader())[0])

    def test_empty_n_store_and_extra_n_rows(self):
        v=fixture('empty');v[2].rename(v[0]/'saved.sqlite');db(v[2],[])
        d=nd.load(v[4]/'rdiff_summary.json');d['inputs']['N']['sha256']=z.sha(v[2]);write(v[4]/'rdiff_summary.json',d)
        v[4].rename(v[0]/'saved_rd')
        with patch.object(nd,'GATE',z.sha(v[1])):nd.publish(*v[1:])
        d=nd.load(v[5]/'nd.json');self.assertEqual(d['N_rows'],0);self.assertEqual(d['matched_rows'],0)

    def test_nonfinite_strict_loader_and_no_mutation(self):
        from student_pilot.p3_provenance import load as native_load
        row=dict(stream='vqa',loss=float('nan'),finite=False,calls=[],components={'a':float('inf'),'b':float('-inf')})
        cleaned=f0.finite_record(row)
        self.assertTrue(math.isnan(row['loss']));self.assertEqual(cleaned['loss'],'NaN')
        self.assertEqual(cleaned['nonfinite_values'],['/loss','/components/a','/components/b'])
        self.assertEqual(cleaned['components'],{'a':'Infinity','b':'-Infinity'})
        self.assertFalse(cleaned['finite'])
        p=F/'finite.json';write(p,dict(streams=f0.grouped([cleaned])))
        self.assertEqual(native_load(p)['streams']['vqa']['loss'],['NaN'])
        finite=dict(row,loss=1.25,components={'a':0.5});self.assertEqual(f0.finite_record(finite),finite)

    def test_only_publication_changes_x_and_b_is_unchanged(self):
        a=ast.parse((L/'attic/build24m4o/out/rcj/x.py').read_bytes());b=ast.parse((L/'out/rcj/x.py').read_bytes())
        before={n.name:ast.dump(n) for n in a.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        after={n.name:ast.dump(n) for n in b.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        self.assertEqual([n for n in before if before[n]!=after[n]],['publish'])
        self.assertEqual(set(after)-set(before),{'nsample'})
        fn=next(n for n in b.body if isinstance(n,ast.FunctionDef) and n.name=='publish')
        fn.body=[n for n in fn.body if not (isinstance(n,ast.If) and any(isinstance(t,ast.Call) and isinstance(t.func,ast.Name) and t.func.id=='nsample' for t in ast.walk(n)))]
        self.assertEqual(ast.dump(fn),before['publish'])
        self.assertEqual(z.sha(L/'out/rcj/rcj.sh'),z.load(D/'BASELINE.json')['rcj']['rcj.sh'])

    def test_publish_success_refusal_and_helper_failure_preserve_status(self):
        import ep
        for rc,rdrc,gate,fail in [(0,0,True,False),(1,1,True,False),(0,0,True,True),(1,1,False,True)]:
            root=F/('pub_'+str(rc)+str(rdrc)+str(gate)+str(fail));root.mkdir()
            native=root/'dr/p/q';native.mkdir(parents=True)
            for part in ('base','selection'):db(native/part/'rows.sqlite',[])
            write(root/'mode.json',dict(mode='r'))
            remote=root/'remote';events=[]
            def read(p):
                if str(p).endswith('k/p.json'):return dict(n_root=str(remote))
                return z.load(p)
            def sha(p):
                if Path(p)==native/'base/rows.sqlite':return x.DB if gate else '0'*64
                return z.sha(p)
            Z=SimpleNamespace(load=read,sha=sha,write=z.write)
            def rd(*a):events.append('rd');return rdrc
            def ns(*a):
                events.append('ns')
                if fail:raise ValueError('fixture')
                return dict(status='PASS',files=[],bytes=0)
            def proc(*a,**kw):write(root/'proc_check.json',dict(status='PASS'));return 0
            with patch.object(x,'attach',return_value=Z),patch.object(ep,'artifact_entries',return_value=[]),patch.object(x,'rdiff',side_effect=rd),patch.object(x,'nsample',side_effect=ns),patch.object(x,'launch',side_effect=proc):
                actual=x.publish(kit('qd'),root,'123',str(rc))
            self.assertEqual(actual,int(bool(rdrc and gate)))
            self.assertEqual(events,['rd','ns'] if gate else ['ns'])
            self.assertEqual(z.load(remote/'o/123/timings.json')['returncode'],rc)

suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
r=unittest.TextTestRunner(verbosity=2).run(suite)
write(D/'TESTS.json',dict(status='PASS' if r.wasSuccessful() else 'FAIL',tests=r.testsRun,errors=[str(x) for x in r.errors],failures=[str(x) for x in r.failures],production_rows=False))
raise SystemExit(not r.wasSuccessful())
