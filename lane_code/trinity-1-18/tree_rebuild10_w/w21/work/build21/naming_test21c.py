from pathlib import Path
import base64,hashlib,json,sys,shutil,unittest
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];B=L/'work/build21';C=L/'work/build21c'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
from naming21 import scan_decoded
from jobtest import reseal
from launch_r2.build import capsule_json,bad_string

class Naming21c(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=C/'proofs/naming';cls.root.mkdir(parents=True,exist_ok=True)
        cls.kit=cls.root/'kit';shutil.copytree(B/'kits/q',cls.kit,dirs_exist_ok=True)
        cls.controls=[]

    def mutation(self,document,change,pattern):
        p=self.kit/document;saved=p.read_bytes()
        try:
            value=J.load(p);change(value);p.write_bytes(capsule_json(value));reseal(self.kit)
            with self.assertRaisesRegex(ValueError,pattern) as context:scan_decoded(self.kit)
            self.controls.append(dict(document=document,result='REFUSE',error=str(context.exception)))
        finally:p.write_bytes(saved);reseal(self.kit)

    def test_base_fails_exact_name(self):
        p=self.kit/'k/p.json';saved=p.read_bytes()
        try:
            p.write_bytes((L/'attic/build21c/kit/k/p.json').read_bytes())
            with self.assertRaisesRegex(ValueError,'k/benchmark_scene_exclusions.json'):scan_decoded(self.kit)
        finally:p.write_bytes(saved)

    def test_final_scan(self):
        scan=scan_decoded(self.kit)
        self.assertIn('k/p.json',scan['decoded_maps']);self.assertIn('k/l.json',scan['decoded_maps'])
        J.write(C/'SCAN.json',scan)

    def test_p_files_mutation(self):
        def change(v):v['p_files']['k/BeNcHmArK.json']='0'*64
        self.mutation('k/p.json',change,'INPUT_NAME:.*k/BeNcHmArK.json')

    def test_map_keys_and_relative_values(self):
        self.mutation('k/l.json',lambda v:v['tars'][0]['files'].update({'q/DATASET.bin':'0'*64}),'INPUT_NAME:.*DATASET')
        self.mutation('k/l.json',lambda v:v['staged_inputs']['files'][0].update(destination='q/Teacher.json'),'INPUT_NAME:.*Teacher')
        self.mutation('k/l.json',lambda v:v['bundle_parts'].update({'Student':['q/a']}),'INPUT_NAME:.*Student')
        self.mutation('k/p.json',lambda v:v['p_sources'].update({'k/a.json':'u/QWEN'}),'INPUT_NAME:.*QWEN')
        self.mutation('k/n.json',lambda v:v['benchmark_scene_exclusions'].update(path='u/benchmark.json',sha256='0'*64),'INPUT_NAME_UNMAPPED:.*benchmark.json')
        self.mutation('k/p.json',lambda v:v['pin_paths'].update({'0'*64:'u/Dataset.json'}),'INPUT_NAME:.*Dataset.json')

    def test_nested_capsule_and_unknown_map(self):
        def change(v):
            entry=next(iter(v['entries'].values()))
            raw=json.dumps({'files':{'k/DISTILL.json':'0'*64}}).encode()
            entry.update(payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())
        self.mutation('k/s.json',change,'INPUT_NAME:.*DISTILL')
        p=self.kit/'k/z9.json'
        p.write_bytes(capsule_json({'links':{'Qwen':'u/a'}}))
        try:
            with self.assertRaisesRegex(ValueError,'INPUT_NAME:.*Qwen'):scan_decoded(self.kit)
        finally:p.rename(self.root/'unknown_map.json')

    def test_capsule_authentication(self):
        p=self.kit/'k/p.json';saved=p.read_bytes()
        try:
            value=json.loads(saved);value['sha256']='0'*64;p.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError,'CAPSULE_HASH'):scan_decoded(self.kit)
        finally:p.write_bytes(saved)

    def test_result_archive_member_literal(self):
        p=self.kit/'b/o.py';saved=p.read_text()
        try:
            p.write_text(saved.replace("'q.log'","'Dataset.log'"))
            with self.assertRaisesRegex(ValueError,'INPUT_NAME:.*Dataset.log'):scan_decoded(self.kit)
        finally:p.write_text(saved)

    def test_opaque_staging_authentication(self):
        kit=self.kit;p=kit/'k/p.json';saved=p.read_bytes();spec=J.load(p)
        pool=self.root/'pool';pool.mkdir(exist_ok=True)
        q=pool/'p/ANON_OK.json';q.parent.mkdir(exist_ok=True);q.write_text('{}')
        h='3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970'
        alias='k/'+h[:8]+'.json';self.assertEqual(spec['p_files'][alias],h)
        uploaded=next(x for x in J.load(B/'UPLOADS.json')['files'] if x['opaque_name']=='u/'+h)
        source=pool/'n/u'/h;source.parent.mkdir(parents=True,exist_ok=True)
        source.write_bytes(Path(uploaded['local_path']).read_bytes())
        spec.update(pool=str(pool),p_root='p',n_root=str(pool/'n'),
            p_files={'ANON_OK.json':J.sha(q),alias:h},p_sources={alias:'u/'+h})
        spec.pop('local_map',None)
        p.write_bytes(capsule_json(spec));reseal(kit)
        resolved=self.root/'resolved.json';J.write(resolved,{})
        try:
            with patch.object(J,'stage_payload',return_value={}),patch.object(J.subprocess,'run',return_value=type('R',(),{'returncode':0})()):
                node=self.root/'node'
                self.assertEqual(J.bootstrap(kit,resolved,node),0)
                self.assertEqual(J.sha(node/'h'/alias),h)
                self.assertFalse((node/'h/k/benchmark_scene_exclusions.json').exists())
                source.write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError,'E10'):J.bootstrap(kit,resolved,self.root/'hash_bad')
                spec['p_files']['k/BENCHMARK.json']=h;p.write_bytes(capsule_json(spec));reseal(kit)
                with self.assertRaisesRegex(ValueError,'E48'):J.bootstrap(kit,resolved,self.root/'name_bad')
                self.assertFalse((self.root/'name_bad').exists())
        finally:p.write_bytes(saved);reseal(kit)
        J.write(C/'STAGING.json',dict(status='PASS',staged_name=alias,sha256=h,
            content_unchanged=True,bad_hash='E10',bad_name='E48',stage_payload='mocked; covered by Job20 and capacity staging'))

    def test_dynamic_names(self):
        guard=J.name_guard(self.kit)
        for name in ('e/k/QWEN.json','w/BENCHMARK.bin','Dataset.log'):
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'E48'):guard(name)
        self.assertEqual(guard('k/3119aa4a.json'),'k/3119aa4a.json')

    def test_runtime_decoded_metadata(self):
        host=self.root/'map_host';(host/'b').mkdir(parents=True,exist_ok=True);(host/'k').mkdir(exist_ok=True)
        (host/'b/s.py').write_bytes((L.parent/'ext/pwrap/b/s.py').read_bytes())
        source=self.root/'map_source/u/a/f';source.parent.mkdir(parents=True,exist_ok=True);source.write_bytes(b'abc')
        record=dict(schema='s1-mdg-raster-inputs-v1',count=1,bytes=3,
            files=[dict(destination='u/a/f',sha256=J.sha(source),bytes=3)])
        metadata=host/'k/m.json';J.write(metadata,record)
        plan=dict(schema='s1-staged-inputs-v1',packages=[],archives=[],files=[],
            directories=[dict(manifest=dict(file='k/m.json',sha256=J.sha(metadata)),source_root=str(self.root/'map_source'))])
        current=host/'k/0.json';J.write(current,dict(staged_inputs=plan))
        result=J.stage_inputs(self.kit,current,host,self.root/'map_node','full')
        self.assertEqual(result['status'],'PASS')
        self.assertEqual(J.sha(self.root/'map_node/aws/u/ap/8865619b/u/a/f'),J.sha(source))
        record['files'][0]['destination']='u/DATASET/f';J.write(metadata,record)
        plan['directories'][0]['manifest']['sha256']=J.sha(metadata);J.write(current,dict(staged_inputs=plan))
        with self.assertRaisesRegex(ValueError,'E48'):J.stage_inputs(self.kit,current,host,self.root/'map_bad','full')

    def test_hash_addressed_consumers(self):
        h='3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970'
        value={'path':'/old/benchmark.json','sha256':h}
        spec=J.load(self.kit/'k/p.json')
        self.assertEqual(spec['pin_paths'][h],spec['namespace']+'/u/'+h)
        row=next(x for x in J.load(B/'UPLOADS.json')['files'] if x['sha256']==h)
        from student_pilot.r1_persisted import scope
        from student_pilot.p3_provenance import pinned
        with scope({h:row['local_path']}):self.assertEqual(J.sha(pinned(value)),h)
        self.assertEqual(value['path'],'/old/benchmark.json')

    def test_source_map_authentication(self):
        p=self.kit/'k/p.json';saved=p.read_bytes();spec=J.load(p)
        resolved=self.root/'empty.json';J.write(resolved,{})
        try:
            spec['p_sources']['k/absent.json']='u/'+'0'*64
            p.write_bytes(capsule_json(spec));reseal(self.kit)
            with self.assertRaisesRegex(ValueError,'E49'):J.bootstrap(self.kit,resolved,self.root/'orphan')
            spec['p_sources'].pop('k/absent.json')
            alias=next(iter(spec['p_sources']));spec['p_sources'][alias]='u/'+'0'*64
            p.write_bytes(capsule_json(spec));reseal(self.kit)
            with self.assertRaisesRegex(ValueError,'E49'):J.bootstrap(self.kit,resolved,self.root/'wrong_source')
        finally:p.write_bytes(saved);reseal(self.kit)

    def test_resolver_map_and_snapshot_refusals(self):
        from jobtest import Job20,archive
        Job20.setUpClass();p=Job20.kit/'k/p.json';saved=p.read_bytes()
        try:
            spec=J.load(p);spec['pin_paths']={'0'*64:'/q/u/'+'0'*64}
            p.write_bytes(capsule_json(spec));reseal(Job20.kit)
            with self.assertRaisesRegex(ValueError,'E49'):Job20().resolve()
        finally:p.write_bytes(saved);reseal(Job20.kit)
        source=self.root/'x.tar';archive(source,{'a/snapshots/r/Dataset.json':b'{}'})
        with self.assertRaisesRegex(ValueError,'E48'):J.snapshot(source,J.sha(source),self.root/'snapshot_bad','r',self.kit)

    def test_invalid_source_inventory(self):
        p=self.kit/'k/c0.json';saved=p.read_bytes()
        try:
            value=J.load(p);value['files']['a.py']='bad';p.write_bytes(capsule_json(value))
            with self.assertRaisesRegex(ValueError,'SOURCE_INVENTORY'):scan_decoded(self.kit)
        finally:p.write_bytes(saved)

    @classmethod
    def tearDownClass(cls):
        if cls.controls:J.write(C/'MUTATIONS.json',cls.controls)
