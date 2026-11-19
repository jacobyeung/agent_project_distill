from pathlib import Path
from copy import deepcopy
import base64,hashlib,io,json,os,shutil,subprocess,sys,tarfile,unittest
L=Path(__file__).resolve().parents[2];B=L/'work/build21';sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
if os.environ.get('B20_JOB_MODULE'):
    import importlib.util
    spec=importlib.util.spec_from_file_location('qmut',os.environ['B20_JOB_MODULE']);J=importlib.util.module_from_spec(spec);spec.loader.exec_module(J)
from launch_r2.build import capsule_json

def rawcap(raw):return json.dumps(dict(encoding='base64',payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())).encode()
def archive(path,files):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tarfile.open(path,'w') as t:
        for name,raw in files.items():
            item=tarfile.TarInfo(name);item.size=len(raw);item.mode=0o755;t.addfile(item,io.BytesIO(raw))
    return dict(file=str(path),sha256=J.sha(path))
def reseal(kit):
    files={str(p.relative_to(kit)):J.sha(p) for p in kit.rglob('*') if p.is_file() and p.name not in ('SHA256SUMS.txt','BUILD.json')}
    (kit/'SHA256SUMS.txt').write_text(''.join(f'{h}  {n}\n' for n,h in sorted(files.items())))

class Job20(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=L/'work/build21/proofs/job';cls.root.mkdir(exist_ok=True)
        cls.kit=cls.root/'kit';shutil.copytree(B/'kits/q',cls.kit,dirs_exist_ok=True)
        cls.pool=cls.root/'pool';cls.pool.mkdir(exist_ok=True)
        cls.spec=J.load(cls.kit/'k/p.json');cls.spec.update(pool=str(cls.pool),n_root=str(cls.pool/'x_22c714e1'),p_files={},p_sources={},pin_paths={})
        cls.spec['uploads']=[];cls.spec.pop('local_map',None)
        cls.records={}
        def record(name,value):
            raw=(json.dumps(value,sort_keys=True)+'\n').encode();h=hashlib.sha256(raw).hexdigest()
            cls.records[h]=(name,raw);return dict(path='/opaque/'+name,sha256=h)
        config_file=record('base_config.json',{})
        model=record('model.json',dict(root='/opaque/model',files={'config.json':config_file['sha256']}))
        cls.spec['room_sha256']=model['sha256']
        routing=J.load(cls.kit/'k/n.json')['streams']['routing']
        streams={'routing':routing} if routing.get('sha256') else {}
        source=dict(streams=streams,s1_routing={},preparation_output='/opaque/p')
        cls.spec['p_kit_config']=record('kit.json',source)
        cls.spec['p_kit_identity']=cls.spec['p_runtime_identity']=J.export_identity(source)
        prep=record('prep.json',dict(model=model,streams={k:dict(receipt=v) for k,v in streams.items()},config_sha256=cls.spec['p_runtime_identity']))
        cfg=record('config.json',dict(source,preparation=prep))
        binding=record('binding.json',dict(preparation=prep,config_sha256=cls.spec['p_runtime_identity']))
        weights=b'weight';wh=hashlib.sha256(weights).hexdigest();heads=b'head';hh=hashlib.sha256(heads).hexdigest()
        index=record('model.safetensors.index.json',dict(weight_map={'a':'w.bin'}))
        from student_pilot.full_ft import EXPORT_SCHEMA
        full=record('full.json',dict(schema=EXPORT_SCHEMA,dtype='bfloat16',tensor_count=1,index=dict(name='model.safetensors.index.json',sha256=index['sha256']),files=[dict(name='w.bin',bytes=len(weights),sha256=wh)]))
        artifact=record('artifact.json',dict(step=400,config_sha256=cls.spec['p_runtime_identity'],full_weights=full,heads=dict(path='/opaque/h.pt',sha256=hh)))
        cls.run_pins=dict(config=cfg,binding=binding,preparation=prep)
        cls.spec['p_run']=cls.run_pins
        cls.receipt=dict(schema='p-export-only-v1',step=400,pins=dict(cls.run_pins,artifact=artifact,full_weights=full,heads=dict(path='/opaque/h.pt',sha256=hh),**{'export/w.bin':dict(path='/opaque/w.bin',sha256=wh)}))
        m=cls.pool/cls.spec['milestone'];m.mkdir(parents=True,exist_ok=True)
        J.write(m/'e.json',cls.receipt);J.write(m/'r.json',cls.run_pins);J.write(m/'DONE.json',dict(step=400,ok=1,checkpoint_overlap='no'))
        manifest=dict(schema='r7-handover-small-files-v1',run='6ed2c7aa',step=400,files=[dict(path='/opaque/'+n,bytes=len(raw),sha256=h,pin=h,match=True) for h,(n,raw) in cls.records.items()])
        archive(m/'s.tar',{'MANIFEST.json':json.dumps(manifest).encode(),**{'files/opaque/'+n:raw for n,raw in cls.records.values()}})
        a=cls.pool/'weights.tar';archive(a,{'e/h.pt':heads,'e/w.bin':weights})
        allbytes=a.read_bytes();parts=[]
        for i in range(4):
            raw=allbytes[len(allbytes)*i//4:len(allbytes)*(i+1)//4];p=cls.pool/f'part{i}';p.write_bytes(raw)
            parts.append(dict(name=f'q8/8865619b/6ed2c7aa_m400.tar.part{i:02d}-of-04',pool_path=str(p),bytes=len(raw),sha256=J.sha(p)))
        cls.parts=parts;cls.listing=cls.root/'listing.json';J.write(cls.listing,dict(objects=parts))
        mark=cls.pool/cls.spec['p_root']/'o/gcs_6ed2c7aa_m400.done';mark.parent.mkdir(parents=True,exist_ok=True)
        mark.write_text(f'q8/8865619b/6ed2c7aa_m400.tar {len(allbytes)} {J.sha(a)}\n')
        (cls.kit/'k/p.json').write_bytes(capsule_json(cls.spec));reseal(cls.kit)

    def resolve(self):return J.resolve(self.kit,self.pool,self.listing,self.root/'r.json')

    def test_resolver_and_payload(self):
        r=self.resolve();self.assertEqual(r['config']['r1_training']['proof_mode'],'q')
        self.assertEqual(r['config']['r2_identity']['init']['step'],544)
        request=J.stage_payload(self.kit,r,self.root/'node')
        self.assertEqual(request['milestone'],400)
        for pin in self.receipt['pins'].values():self.assertEqual(J.sha(self.root/'node/u'/pin['sha256']),pin['sha256'])
        from student_pilot.full_ft import read_export
        value,_=read_export(self.root/'node/w')
        self.assertEqual(value['tensor_count'],1)
        self.assertEqual(request['_paths'][self.receipt['pins']['full_weights']['sha256']],self.spec['namespace']+'/w/full_weights.json')
        for case in ('size','hash','parts','outside','marker','receipt','done','small','artifact','run','seal'):
            listing=deepcopy(self.parts);m=self.pool/self.spec['milestone'];restores=[]
            def altered(p,raw):restores.append((p,p.read_bytes()));p.write_bytes(raw)
            if case=='size':listing[0]['bytes']+=1
            if case=='hash':listing[0]['sha256']='0'*64
            if case=='parts':listing=listing[:-1]
            if case=='outside':listing[0]['pool_path']='/outside'
            if case=='marker':altered(self.pool/self.spec['p_root']/'o/gcs_6ed2c7aa_m400.done',b'bad')
            if case=='receipt':
                bad=deepcopy(self.receipt);bad['schema']='wrong';altered(m/'e.json',json.dumps(bad).encode())
            if case=='done':altered(m/'DONE.json',b'{"ok":0}')
            if case=='small':altered(m/'s.tar',b'bad')
            if case=='artifact':
                bad=deepcopy(self.spec);bad['p_runtime_identity']='0'*64;altered(self.kit/'k/p.json',capsule_json(bad));reseal(self.kit)
            if case=='run':altered(m/'r.json',b'{}')
            if case=='seal':altered(self.kit/'b/v.py',b'changed')
            J.write(self.listing,dict(objects=listing))
            try:
                with self.subTest(case=case),self.assertRaises((ValueError,tarfile.ReadError,KeyError)):self.resolve()
            finally:
                for p,raw in restores:p.write_bytes(raw)
                reseal(self.kit);J.write(self.listing,dict(objects=self.parts))
        p=self.root/'node/e/e/w.bin';p.write_bytes(b'bad')
        # A resolved input mismatch refuses before publication.
        r=self.resolve();r['archive']['sha256']='0'*64
        with self.assertRaises(ValueError):J.stage_payload(self.kit,r,self.root/'node')
        r=self.resolve();r['kit_sha256']='0'*64
        with self.assertRaises(ValueError):J.stage_payload(self.kit,r,self.root/'node')

    def test_shell_stage_and_namespace(self):
        pkit=self.pool/self.spec['p_root'];pkit.mkdir(exist_ok=True)
        E=L.parent/'ext/pwrap';pfiles={}
        def stage(name,raw):
            p=pkit/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);pfiles[name]=J.sha(p);return p
        for name in ('b/s.py','b/kitx.py','b/f2.py','b/sa/sitecustomize.py','b/sa/prestage_hooks.py','b/wh.json'):
            stage(name,(E/name).read_bytes())
        current={};cache=self.pool/'in';cache.mkdir(exist_ok=True)
        current['venv']=archive(cache/'v.tar',{'rwtrain_torch211_cu129/bin/torchrun':b'#!/bin/sh\nexit 0\n'})
        current['closure']=archive(cache/'c.tar',{'a':b'a'})
        current['trainer']=archive(cache/'t.tar',{'a':b'a'});current['commit']='a'*40
        current['model']=archive(cache/'m.tar',{'models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a/config.json':b'{}'})
        current['art']=archive(cache/'a.tar',{'lb/51f013139e77.npz':b'a'})
        current['np']=archive(cache/'n.tar',{'a':b'a'})
        record=stage('k/r.json',b'{}');current['record']=dict(file=str(record),sha256=J.sha(record))
        bw=cache/'bw';bw.write_text('#!/bin/sh\nexit 0\n');bw.chmod(0o755);current['bwrap']=dict(file=str(bw),sha256=J.sha(bw))
        AS='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung';AL=AS.replace('/scratch/','/lustre/')
        current['small']=archive(cache/'e00',{f'{prefix[1:]}/ap/244cdf20/k/{name}.json':b'{}' for prefix in (AS,AL) for name in ('932c0c4e','99e6eed6')})
        row=cache/'row';row.write_bytes(b'row');current['a1rows']=dict(dest=AS+'/ap/a/rows',parts=[str(row)],sha256=J.sha(row))
        current['extra']=[];current['tars']=[]
        overlay=b'a';oh=hashlib.sha256(overlay).hexdigest();manifest=(oh+'  a.py\n').encode()
        archive(cache/'d00',{'ebe69df8/p/a.py':overlay,'ebe69df8/m.sha':manifest})
        current['fla']=dict(file=AS+'/ap/7b30c1e4/u/ebe69df8/m.sha',sha256=hashlib.sha256(manifest).hexdigest())
        rgb=b'frame';h=hashlib.sha256(rgb).hexdigest();name='k6tk/'+h[:2]+'/'+h+'.png'
        current['f4']=archive(cache/'f.tar',{name:rgb});current['stores']={'f4':'k6tk'}
        frame=cache/'f.json';J.write(frame,[dict(path='/data2/'+name,sha256=h)])
        current['f4_manifest']=dict(file=str(frame),sha256=J.sha(frame))
        extra=archive(cache/'x.tar',{'ap/a/t':b't'})
        current['tars']=[dict(parts=[extra['file']],files={'ap/a/t':hashlib.sha256(b't').hexdigest()})]
        current['staged_inputs']=dict(schema='s1-staged-inputs-v1',packages=[],directories=[],
            files=[dict(source=str(row),destination='u/a/row',sha256=J.sha(row),bytes=3)],
            archives=[dict(source=current['f4']['file'],sha256=current['f4']['sha256'],bytes=(cache/'f.tar').stat().st_size,destination='data2root',members=1)])
        stage('k/0.json',json.dumps(current).encode());stage('ANON_OK.json',b'{}');stage('SHA256SUMS.txt',b'')
        spec=deepcopy(self.spec);spec['p_files']=pfiles
        (self.kit/'k/p.json').write_bytes(capsule_json(spec))
        shell=base64.b64decode(J.load_raw(self.kit/'k/j.json')['payload']).decode()
        shell=shell.replace('R=/project/community/jjyeung/okh7/l_94a76bda','R='+str(self.pool))
        shell=shell.replace('/tmp/jjyeung',str(self.root/'home'))
        shell=shell.replace('/usr/bin/python3',sys.executable)
        (self.kit/'k/j.json').write_bytes(rawcap(shell.encode()));reseal(self.kit)
        self.resolve()
        for p in [self.kit/'job.sh']:
            subprocess.run(['/bin/bash','-n',str(p)],check=True)
        script=self.root/'j.sh';script.write_text(shell);subprocess.run(['/bin/bash','-n',str(script)],check=True)
        binpath=self.root/'bin';binpath.mkdir(exist_ok=True)
        if not (binpath/'python3').exists():(binpath/'python3').symlink_to(sys.executable)
        env={**os.environ,'PATH':str(binpath)+':'+os.environ['PATH'],'SLURM_JOB_ID':'20','SLURM_TMPDIR':str(self.root),'Q_CAPTURE':'1'}
        with (B/'proofs/operator/shell.log').open('w') as log:
            r=subprocess.run(['/bin/bash',str(self.kit/'job.sh'),str(self.root/'r.json')],env=env,stdout=log,stderr=subprocess.STDOUT)
        self.assertEqual(r.returncode,0,'See proofs/operator/shell.log')
        node=self.root/'q_22c714e1_20';args=J.load(node/'args.json')
        self.assertIn(AS,args);self.assertIn(AL,args);self.assertIn(self.spec['namespace'],args)
        self.assertEqual(J.sha(node/'s/c7d31ddd/data2root'/name),h)
        J.write(B/'proofs/operator/NAMESPACE.json',dict(arguments=args,stand_ins=['Slurm allocation environment','bwrap invocation captured after genuine staging'],frame_hash=h))
        # Shell failures do not fall through to the proof.
        pin=node/'h/k/0.json';saved=pin.read_bytes()
        (self.kit/'k/p.json').write_bytes(capsule_json(self.spec));reseal(self.kit)

    def test_room_report(self):
        import sqlite3
        cfg=J.load(B/'kits/q/k/n.json')
        db=sqlite3.connect(':memory:');db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT)')
        rows=[dict(qid='room'+str(i),dataset='d1',scene='scene9997_00',canonical='scannet/scene9997_00',question_type='object_rel_direction_easy') for i in range(30)]
        db.executemany('INSERT INTO rows VALUES(?,?)',[(i,json.dumps(row)) for i,row in enumerate(rows)]);db.commit()
        path=self.root/'rooms.sqlite';path.write_bytes(db.serialize());db.close()
        cfg['streams']={'vqa':J.write(self.root/'rooms_receipt.json',dict(database=dict(path=str(path),sha256=J.sha(path))))}
        pin=J.room_report(cfg,B/'proofs/operator/ROOMS.json')
        value=J.load(pin['path']);self.assertTrue(value['report_only']);self.assertTrue(value['cells'])
        self.assertEqual(sum(x['rows'] for x in value['cells'].values()),30)
        self.assertTrue(all(len(x['examples'])<=20 for x in value['cells'].values()))
