from pathlib import Path
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import hashlib,importlib.util,io,json,sys,tarfile,unittest
L=Path(__file__).resolve().parents[2];D=L/'work/build24';O=L/'work/build24m4p/proofs/resolver600_v2'
O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(Path(__file__).resolve().parent), '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24p/work/tree_r1c']
sys.path[:0]=[str(Path(__file__).resolve().parent), '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24p/work/tree_r1c']
import joblib as J
from kit import cap,reseal
from fill_m600 import fill

def write(p,v):return J.write(p,v)
def data(p,raw):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);return dict(path=str(p),sha256=J.sha(p))
def fixture():
    root=O/'f';root.mkdir(exist_ok=True);pool=root/'pool';a=pool/'h_6ed2c7aa/m600';b=pool/'pb_a5416871'
    a.mkdir(parents=True,exist_ok=True);b.mkdir(exist_ok=True);runroot=root/'6ed2c7aa';runroot.mkdir(exist_ok=True)
    modelroot=root/'model';modelroot.mkdir(exist_ok=True)
    data(modelroot/'config.json',b'{}\n');data(modelroot/'tokenizer.json',b'{}\n')
    model=write(root/'model.json',dict(root=str(modelroot),files={p.name:J.sha(p) for p in modelroot.iterdir()}))
    db=data(root/'base.bin',b'fixture rows\n');division=write(root/'division.json',dict(train_scenes=['fixture'],heldout_scenes=[]))
    routing=write(root/'routing.json',dict(schema='c1-routing-stream-v1',database=db,division=division,heldout_overlap=0,scene_role='train'))
    streams={name:routing if name=='routing' else write(root/(name+'.json'),dict(stream=name,database=db)) for name in ('pose','vqa','routing','pointing')}
    config=dict(streams=streams,preparation_output=str(runroot/'prepare'),output=str(runroot),s1_routing=dict(schema='s1-routing-inputs-v1',selection=routing))
    source=write(root/'source.json',config);identity=J.export_identity(config)
    prep=write(runroot/'preparation.json',dict(config_sha256=identity,model=model,streams={k:dict(receipt=v) for k,v in streams.items()}))
    config['preparation']=prep;cpin=write(runroot/'config.json',config)
    bound=dict(config_sha256=identity,preparation=prep,world_size=4,trainer_commit='sha256:'+'a'*64)
    bp=write(runroot/'binding.json',bound)
    cpdir=runroot/'checkpoint_000600_fixture';cpdir.mkdir(exist_ok=True)
    files={}
    for name in ['replicated.pt',*[f'rng{i:03d}.pt' for i in range(4)],*[f'shards/rank{i:03d}.pt' for i in range(4)]]:
        p=data(cpdir/name,('fixture '+name).encode());files[name]=dict(p,bytes=Path(p['path']).stat().st_size)
    cpp=write(cpdir/'complete.json',dict(schema='c1-checkpoint-v1',step=600,binding=bound,files=files,layouts={'fixture':1}))
    exp=runroot/'m600';exp.mkdir(exist_ok=True);weights=exp/'full_weights';weights.mkdir(exist_ok=True)
    shard=data(weights/'model.safetensors',b'fixture tensor bytes');index=write(weights/'model.safetensors.index.json',dict(weight_map={'x':'model.safetensors'}))
    wf=write(weights/'full_weights.json',dict(index=dict(name=Path(index['path']).name,sha256=index['sha256'],bytes=Path(index['path']).stat().st_size),
        files=[dict(name=Path(shard['path']).name,sha256=shard['sha256'],bytes=Path(shard['path']).stat().st_size)]))
    heads=data(exp/'heads.pt',b'fixture heads')
    ap=write(exp/'artifact.json',dict(step=600,config_sha256=identity,heads=heads,full_weights=wf))
    run=dict(config=cpin,binding=bp,preparation=prep,checkpoint=cpp)
    pins=dict(artifact=ap,heads=heads,full_weights=wf,**run)
    pins.update({'checkpoint/'+n:{k:p[k] for k in ('path','sha256')} for n,p in files.items()})
    pins.update({'export/'+Path(p['path']).name:p for p in (index,shard)})
    pins.update({'stream/'+n:p for n,p in streams.items()})
    receipt=dict(schema='p-handover-v1',step=600,job_id='fixture',trainer_commit=bound['trainer_commit'],pins=pins)
    for directory in (a,b):write(directory/'h.json',receipt);write(directory/'RP.json',run)
    write(a/'DONE.json',dict(step=600,ok=1,checkpoint_overlap='yes'))
    write(b/'pb_report.json',dict(step=600,verdict='PASS',run='6ed2c7aa',files={n:J.sha(b/n) for n in ('h.json','RP.json')}))
    spec=J.load(D/'kits/n/k/p.json');spec.pop('m4',None);spec.update(step=600,p_kit_identity=identity,p_runtime_identity=identity,p_kit_config=source,p_run=run)
    metadata_entries=[dict(path=str(p),pool_path=str(p),sha256=J.sha(p),bytes=p.stat().st_size) for p in modelroot.iterdir()]
    lv=dict(metadata=metadata_entries)
    values,metadata=J.local_metadata(spec,receipt,lv)
    manifest=dict(schema='r7-handover-small-files-v1',run='6ed2c7aa',step=600,files=[])
    with tarfile.open(a/'s.tar','w') as t:
        for h,v in values.items():
            p=Path(v['path']);raw=p.read_bytes();name='files'+str(p)
            item=tarfile.TarInfo(name);item.size=len(raw);t.addfile(item,io.BytesIO(raw))
            manifest['files'].append(dict(path=str(p),sha256=h,pin=h,bytes=len(raw),match=True))
        raw=json.dumps(manifest).encode();item=tarfile.TarInfo('MANIFEST.json');item.size=len(raw);t.addfile(item,io.BytesIO(raw))
    export=pool/'6ed2c7aa_m600.tar'
    with tarfile.open(export,'w') as t:
        for label,p in pins.items():
            if label.startswith('export/') or label in ('heads','full_weights'):
                t.add(p['path'],arcname='e/'+Path(p['path']).name,recursive=False)
    name='q8/8865619b/6ed2c7aa_m600.tar'
    lv.update(objects=[dict(name=name,pool_path=str(export),sha256=J.sha(export),bytes=export.stat().st_size)],
        export=dict(names=[name],sha256=J.sha(export),bytes=export.stat().st_size))
    listing=root/'l.json';write(listing,lv)
    import shutil
    template=root/'n';shutil.copytree(D/'kits/n',template,dirs_exist_ok=True,copy_function=lambda a,b: shutil.copyfile(a,b) if Path(a).suffix!='.tar' else __import__('os').link(a,b))
    cap(template,'k/p.json',spec)
    cfg=J.load(template/'k/n.json');cfg['r1_training'].pop('init_policy',None);cfg['streams']['routing']=routing;cfg['s1_routing']=config['s1_routing'];cap(template,'k/n.json',cfg);reseal(template)
    return dict(root=root,pool=pool,a=a,b=b,template=template,receipt=receipt,run=run,values=values,metadata=metadata,listing=listing,spec=spec)

class Resolver24(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.f=fixture()
    def test_01_fill_and_resolve_A_and_B(self):
        for plan in ('A','B'):
            f=self.f;record=fill(f['template'],f[plan.lower()],f['listing'],O/('filled_'+plan),plan)
            self.assertFalse(record['GO']);self.assertEqual(len(record['filled']['checkpoint']),10)
            result=J.load(O/('filled_'+plan+'_resolved.json'))
            self.assertEqual(result['request']['milestone'],600)
            self.assertEqual(result['config']['r1_training']['proof_mode'],'train')
            self.assertEqual(result['config']['r2_identity']['init']['step'],544)
            self.assertEqual(result['config']['r1_training']['routing_slices'],'deferred_first_boundary')
            self.assertEqual(result['config']['remove_files'],J.load(f['template']/'k/n.json')['remove_files'])
    def test_02_real_200_refuses_by_name(self):
        witness=J.load('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24p/work/build24/WITNESS200.json');h=deepcopy(self.f['receipt']);h.update(schema=witness['schema'],step=witness['step'])
        with self.assertRaisesRegex(ValueError,'^E56:200$'):J.receipt600(h,self.f['run'])
    def test_03_receipt_mutations(self):
        for field,value,error in (('step',400,'E56'),('step',200,'E56'),('step',600.0,'E56'),('schema','p-export-only-v1','E58'),('job_id','','E58'),('trainer_commit','','E58')):
            h=deepcopy(self.f['receipt']);h[field]=value
            with self.subTest(field=field,value=value),self.assertRaisesRegex(ValueError,error):J.receipt600(h,self.f['run'])
        h=deepcopy(self.f['receipt']);h['pins']['artifact']['sha256']='bad'
        with self.assertRaisesRegex(ValueError,'E60:artifact'):J.receipt600(h,self.f['run'])
        run=deepcopy(self.f['run']);run.pop('checkpoint')
        with self.assertRaisesRegex(ValueError,'E59'):J.receipt600(self.f['receipt'],run)
        run=deepcopy(self.f['run']);run['binding']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'E22:binding'):J.receipt600(self.f['receipt'],run)
        h=deepcopy(self.f['receipt']);run=deepcopy(self.f['run']);run['checkpoint']['path']=str(self.f['root']/'checkpoint_000200/complete.json');h['pins']['checkpoint']=run['checkpoint']
        with self.assertRaisesRegex(ValueError,'E61'):J.receipt600(h,run)
    def test_04_closure_mutations(self):
        f=self.f;pins=f['receipt']['pins']
        for mode,error in (('step','E62'),('binding','E62'),('layouts','E63'),('path','E65'),('escape','E64'),('extra','E66'),('export','E65')):
            h=deepcopy(f['receipt']);m=deepcopy(f['metadata']);complete=m[pins['checkpoint']['sha256']]
            if mode=='step':complete['step']=400
            elif mode=='binding':complete['binding']={}
            elif mode=='layouts':complete['layouts']={}
            elif mode=='path':h['pins']['checkpoint/rng000.pt']['path']=str(f['root']/'rng000.pt')
            elif mode=='escape':complete['files']['../x']=next(iter(complete['files'].values()))
            elif mode=='extra':h['pins']['extra']=pins['artifact']
            else:h['pins']['export/model.safetensors']['path']=str(f['root']/'model.safetensors')
            with self.subTest(mode=mode),self.assertRaisesRegex(ValueError,error):J.checkpoint600(h,f['run'],f['values'],m)
    def test_05_exact_path(self):
        with self.assertRaisesRegex(ValueError,'E57'):J.exact_path('relative.json')
        with self.assertRaisesRegex(ValueError,'E57'):J.exact_path(str(self.f['root'])+'/../other.json')
    def test_06_identity_checks_unchanged(self):
        f=self.f
        J.identities(f['spec'],f['run'],f['receipt']['pins'],f['values'],f['metadata'])
        for key,error in (('p_kit_identity','E52'),('p_runtime_identity','E23')):
            spec=deepcopy(f['spec']);spec[key]='0'*64
            with self.assertRaisesRegex(ValueError,error):J.identities(spec,f['run'],f['receipt']['pins'],f['values'],f['metadata'])
    def test_07_old_resolver_refuses_600(self):
        s=importlib.util.spec_from_file_location('old24','/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24p/work/build24m4p/old24.py');old=importlib.util.module_from_spec(s);s.loader.exec_module(old)
        with self.assertRaisesRegex(ValueError,'^E20$'):old.resolve(O/'filled_A',self.f['pool'],self.f['listing'],O/'old.json')
    def test_08_control_and_export_mutations(self):
        for plan,key,value,error in (('A','step',400,'E20'),('A','ok',0,'E20'),('B','step',200,'E71'),('B','verdict','FAIL','E71'),('B','run','other','E71'),('B','files',{},'E72')):
            k=O/('filled_'+plan);spec=J.load(k/'k/p.json');h=deepcopy(spec);name='DONE.json' if plan=='A' else 'pb_report.json';p=Path(h['handover']['files'][name]['path']);control=J.load(p);control[key]=value
            original=J.load
            with patch.object(J,'load',side_effect=lambda q:control if Path(q)==p else original(q)),self.subTest(plan=plan,key=key),self.assertRaisesRegex(ValueError,error):
                J.resolve(k,self.f['pool'],self.f['listing'],O/'bad.json')
        for key,value,error in (('handover',None,'E68'),('milestone','other','E70')):
            k=O/'filled_A';spec=J.load(k/'k/p.json');spec[key]=value;original=J.load
            with patch.object(J,'load',side_effect=lambda q:spec if Path(q)==k/'k/p.json' else original(q)),self.assertRaisesRegex(ValueError,error):J.resolve(k,self.f['pool'],self.f['listing'],O/'bad.json')
    def test_09_plan_parts_and_hash_mutations(self):
        for mode,error in (('plan','E69'),('names','E27'),('bytes','E29'),('sha256','E29'),('pin_paths','E49'),('base','E55')):
            k=O/'filled_A';sp=deepcopy(J.load(k/'k/p.json'));cfg=deepcopy(J.load(k/'k/n.json'));original=J.load
            if mode=='plan':sp['handover']['plan']='C'
            elif mode=='names':sp['handover']['export']['names']=[]
            elif mode in ('bytes','sha256'):sp['handover']['export'][mode]=0 if mode=='bytes' else '0'*64
            elif mode=='pin_paths':sp['pin_paths']={}
            else:cfg['streams']['routing']['sha256']='0'*64
            def load(p):
                return sp if Path(p)==k/'k/p.json' else cfg if Path(p)==k/'k/n.json' else original(p)
            with patch.object(J,'load',side_effect=load),self.subTest(mode=mode),self.assertRaisesRegex(ValueError,error):
                J.resolve(k,self.f['pool'],self.f['listing'],O/'bad.json')
    def test_10_archive_step_is_exact(self):
        for step in (400,200):
            with self.assertRaisesRegex(ValueError,'E15'):J.small_archive(self.f['a']/'s.tar',step)
    def test_11_fill_only_named_fields(self):
        before=J.load(self.f['template']/'k/n.json');after=J.load(O/'filled_A/k/n.json')
        for key in before:
            if key not in ('streams','s1_routing','init_artifact','r1_training'):self.assertEqual(before[key],after[key])
        self.assertEqual(J.load(self.f['template']/'k/a.json'),J.load(O/'filled_A/k/a.json'))
        allowed={'k/p.json','k/n.json','k/c.json','k/r.json','SHA256SUMS.txt','BUILD.json'}
        for p in self.f['template'].rglob('*'):
            if p.is_file() and str(p.relative_to(self.f['template'])) not in allowed:
                self.assertEqual(J.sha(p),J.sha(O/'filled_A'/p.relative_to(self.f['template'])))

    def test_13_metadata_limit_and_checkpoint_step_prefix(self):
        big=self.f['root']/'big.json'
        with big.open('wb') as f:f.seek(30_000_000);f.write(b' ')
        pin=dict(path=str(big),sha256=J.sha(big))
        with self.assertRaisesRegex(ValueError,'E67'):
            J.local_metadata(dict(p_kit_config=pin),dict(pins={}),{})
        h=deepcopy(self.f['receipt']);run=deepcopy(self.f['run'])
        run['checkpoint']['path']=str(self.f['root']/'checkpoint_0006000/complete.json')
        h['pins']['checkpoint']=run['checkpoint']
        with self.assertRaisesRegex(ValueError,'E61'):J.receipt600(h,run)

    def test_14_fill_input_refusals(self):
        f=self.f;out=O/'unwritten'
        with self.assertRaisesRegex(ValueError,'FILL_OUTPUT_EXISTS'):fill(f['template'],f['a'],f['listing'],O/'filled_A','A')
        with self.assertRaisesRegex(ValueError,'FILL_PLAN_INVALID'):fill(f['template'],f['a'],f['listing'],out,'C')
        with self.assertRaisesRegex(ValueError,'FILL_DIRECTORY_INVALID'):fill(f['template'],f['root'],f['listing'],out,'A')
        original=J.load
        for mode,error in (('step','FILL_STEP600_TEMPLATE_REQUIRED'),('export','FILL_EXPORT_PIN_REQUIRED'),('parts','FILL_EXPORT_PARTS_DIFFER'),('name','FILL_EXPORT_NAME')):
            sp=deepcopy(original(f['template']/'k/p.json'));lv=deepcopy(original(f['listing']))
            if mode=='step':sp['step']=400
            elif mode=='export':lv['export']=None
            elif mode=='parts':lv['export']['names']=[]
            else:lv['export']['names']=['wrong'];lv['objects'][0]['name']='wrong'
            def load(p):return sp if Path(p)==f['template']/'k/p.json' else lv if Path(p)==f['listing'] else original(p)
            with patch.object(J,'load',side_effect=load),self.subTest(mode=mode),self.assertRaisesRegex(ValueError,error):fill(f['template'],f['a'],f['listing'],out,'A')

    def test_15_pool_and_model_metadata_checks(self):
        k=O/'filled_A';f=self.f;original=J.load;lv=deepcopy(original(f['listing']))
        lv['objects'][0]['pool_path']=str(f['root']/'outside.tar')
        with patch.object(J,'load',side_effect=lambda p:lv if Path(p)==f['listing'] else original(p)),self.assertRaisesRegex(ValueError,'E12'):
            J.resolve(k,f['pool'],f['listing'],O/'bad.json')
        small=J.small_archive
        for mode,error in (('absent_config','E31'),('absent_file','E41')):
            values,metadata=small(f['a']/'s.tar',600)
            prep=metadata[f['receipt']['pins']['preparation']['sha256']];model=metadata[prep['model']['sha256']]
            if mode=='absent_config':model['files'].pop('config.json')
            else:model['files']['absent.json']='0'*64
            with patch.object(J,'small_archive',return_value=(values,metadata)),self.subTest(mode=mode),self.assertRaisesRegex(ValueError,error):
                J.resolve(k,f['pool'],f['listing'],O/'bad.json')
    def test_12_stage_checkpoint_payload_A_and_B(self):
        for plan in ('A','B'):
            kit=O/('filled_'+plan);result=J.load(O/('filled_'+plan+'_resolved.json'))
            original=J.load
            def local(path):
                value=original(path)
                if Path(path)==kit/'k/p.json':value['uploads']=[]
                return value
            # External N input staging has its own inherited kit tests. This fixture
            # checks the exact donor closure through native payload staging.
            with patch.object(J,'load',side_effect=local):
                result['_namespace']=J.load(kit/'k/p.json')['namespace']
                J.copy_resolved_payload(kit,result,O/('stage_'+plan))
                request=result['request']
            self.assertEqual(request['milestone'],600)
            self.assertTrue((O/('stage_'+plan)/'w/full_weights.json').is_file())
            self.assertEqual(J.load(O/('stage_'+plan)/'e.json')['schema'],'p-handover-v1')
            for label,pin in self.f['receipt']['pins'].items():
                if label.startswith('checkpoint/rng'):
                    self.assertEqual(J.sha(O/('stage_'+plan)/'u'/pin['sha256']),pin['sha256'])

    def test_12_step400_still_passes_real_metadata(self):
        import resolver21e as R
        R.K=D/'kits/q';R.D=O/'legacy400';R.D.mkdir(exist_ok=True)
        f=R.fixture()
        original=J.load;sp=deepcopy(original(R.K/'k/p.json'))
        with tarfile.open(f['m']/'s.tar') as archive:sp['m4']['v']=hashlib.sha256(archive.extractfile('MANIFEST.json').read()).hexdigest()
        tokens=(f['pool']/sp['p_root']/'o/gcs_6ed2c7aa_m400.done').read_text().split();sp['m4'].update(t=tokens[2],b=int(tokens[1]))
        with R.external_boundary(f),patch.object(J,'load',side_effect=lambda p:deepcopy(sp) if Path(p)==R.K/'k/p.json' else original(p)):
            result=J.resolve(R.K,f['pool'],f['listing'],O/'real400.json')
        self.assertEqual(result['request']['milestone'],400)
        self.assertEqual(result['config']['streams']['vqa'],J.load(R.K/'k/n.json')['streams']['vqa'])

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Resolver24))
    write(O/'RESOLVER_TESTS.json',dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),successful=result.wasSuccessful()))
    raise SystemExit(not result.wasSuccessful())
