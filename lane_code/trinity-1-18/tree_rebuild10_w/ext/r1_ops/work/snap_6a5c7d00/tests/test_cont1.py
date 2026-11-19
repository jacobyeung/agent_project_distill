"""Continuation admission, native checkpoint restore, and sampler regression."""
import copy,contextlib,hashlib,importlib.util,json,os,random,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import torch
from rebind import ROOT,load,sha,write
import continuation as c
sys.path[:0]=[str(ROOT/'work/tree'),str(ROOT/'work/tree/generator/derivgen_v7')]
from student_pilot import carrier_c1_run as run,carrier_c1_data as data,full_ft,type_mix

SNAP=Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_9dd2fbb7')
def temp():return Path(tempfile.mkdtemp(prefix='cont1_',dir=ROOT/'work'))

class Continuation(unittest.TestCase):
    def fixture(self):
        parent=load(SNAP/'out/config.json');base=temp()/'f'
        result,source,donor=c.fixture(base,parent,load(ROOT/'out/records/c.json'))
        self.assertEqual(result['status'],'PASS')
        return base,source,donor,parent

    def test_config_delta_and_frozen_inputs(self):
        a=load(SNAP/'out/config.json');b=load(ROOT/'out/config.json');c.policy(b,a)
        from rebind import diff
        self.assertEqual({d['field'] for d in diff(a,b)},
            {'continuation','h1.stop_after_step','recipe.milestones','milestones','output','preparation_output'})
        for k in ('streams','remove_files','s1_routing','readout','type_mix','scheduled_sampling','code','checkpoint_disk_guard'):
            self.assertEqual(a[k],b[k],k)
        self.assertEqual(sha(ROOT/'out/r1p_code.tar'),sha(SNAP/'out/r1p_code.tar'))
        self.assertEqual(load(ROOT/'out/BINDING.json')['record_key'],'69d2930d')
        self.assertNotEqual(load(ROOT/'out/BINDING.json')['store_key'],'69d2930d')

    def test_pointer_refusals(self):
        for key,value in (('run','00000000'),('config','0'*64),('step',199)):
            with self.subTest(key=key):
                _,_,d,parent=self.fixture();r=load(d/'0.json');r[key]=value;write(d/'0.json',r)
                with self.assertRaises(ValueError):c.verify(d,parent)
        _,_,d,parent=self.fixture();(d/'checkpoint_000200/shards/rank000.pt').write_bytes(b'changed')
        with self.assertRaises(ValueError):c.verify(d,parent)

    def test_slot_refusals(self):
        for mutation in ('run','step','sha','archive','manifest','binding'):
            with self.subTest(mutation=mutation):
                base,s,_,parent=self.fixture()
                if mutation=='run':write(s/'RUN.json',dict(run='00000000'))
                elif mutation=='binding':(s/'binding.json').write_text('{}')
                elif mutation=='sha':(s/'A.sha256').write_text('0'*64)
                elif mutation=='archive':
                    raw=bytearray((s/'A.tar').read_bytes());raw[-1]=1;(s/'A.tar').write_bytes(raw)
                else:
                    r=load(s/'A.json');r['step' if mutation=='step' else 'manifest_sha256']=199 if mutation=='step' else '0'*64;write(s/'A.json',r)
                with self.assertRaises(ValueError):c.extract(s,base/'bad',parent,ROOT/'out/records/c.json')

    def test_missing_optimizer_refused(self):
        for payload in (dict(schema=full_ft.SHARD_SCHEMA,tensors={'x':1}),
                dict(schema=full_ft.SHARD_SCHEMA,tensors={'x':1},optimizer=dict(state={},param_groups=[])),
                dict(schema=full_ft.REPLICATED_SCHEMA,tensors={'x':1}),
                dict(schema=full_ft.REPLICATED_SCHEMA,tensors={'x':1},optimizer_state={0:dict(step=200)})):
            with self.subTest(payload=payload),self.assertRaises(ValueError):c.optimizer_payload(payload)

    def test_cells_rebind_requires_explicit_config_mode(self):
        parent=load(SNAP/'out/config.json');cfg=load(ROOT/'out/config.json');changed=copy.deepcopy(cfg)
        cells=changed['type_mix']['streams']['vqa']['cells'];cells['room']['cents']+=1;cells['direction']['cents']-=1
        with self.assertRaises(ValueError):c.policy(changed,parent)
        changed['continuation']['rows']='rebind';c.policy(changed,parent)
        run.validate(changed);self.assertNotEqual(c.identity(cfg),c.identity(changed))

    def test_default_cells_draws_201_600(self):
        a=load(SNAP/'out/config.json');b=load(ROOT/'out/config.json')
        self.assertEqual(load(ROOT/'configs/cont1_cells.json'),{s:v['cells'] for s,v in a['type_mix']['streams'].items()})
        # Production-equal quotas with synthetic admitted populations for every
        # family, plus the real local VQA population below.
        populations={};effective={};counts={s:50000 for s in ('pose','vqa','pointing','routing')}
        for s,policy in a['type_mix']['streams'].items():
            offset=0;populations[s]={};effective[s]={}
            for n,v in policy['cells'].items():
                if not v['cents']:continue
                size=max(100,(v['cents']*10+3)//4);populations[s][n]=list(range(offset,offset+size));offset+=size;effective[s][n]=v
            counts[s]=offset
        value=dict(spec=a['type_mix'],effective=effective,populations=populations)
        def plans(cfg,start):return list(data.mixed_indices(counts,600,start_step=start,seed=cfg['recipe']['seed'],
                training_mode=cfg['training_mode'],mix=cfg['recipe']['mix'],world=4,type_mix=value))
        full=plans(a,0);tail=plans(b,200);self.assertEqual(full[200:],tail)
        prepared=load(SNAP/'out/proof/local_prepared.json');v=load(Path(prepared['type_mix_population']['path']))
        base=lambda:data.mixed_indices({'vqa':prepared['streams']['vqa']['count']},600,seed=17,training_mode='final',mix=['vqa'],world=4)
        self.assertEqual(list(type_mix.plans(base(),v,17))[200:],list(type_mix.plans(base(),v,17,200)))
        write(ROOT/'out/proof/CONT1_ROWS.json',dict(status='PASS',steps=[201,600],all_family_plans=400,
            equality='exact',real_vqa_population=True,other_populations='synthetic'))

    def test_native_state_lr_rng_continuity(self):
        torch.set_num_threads(1)
        class Model(torch.nn.Module):
            def __init__(self):
                super().__init__();self.base=torch.nn.Linear(3,2);self.auxiliary_heads=torch.nn.Linear(2,1)
                self.trace_program_version='3.14'
            def forward(self,x):return self.auxiliary_heads(torch.tanh(self.base(x)))
        def init():
            torch.manual_seed(17);np.random.seed(17);random.seed(17)
            m=Model();o=torch.optim.AdamW(m.parameters(),lr=.01);return m,o
        cfg=load(ROOT/'out/config.json');plans=list(data.mixed_indices(dict(pose=101,vqa=103,pointing=107,routing=109),206,
                seed=17,training_mode='final',mix=cfg['recipe']['mix'],world=4))
        def steps(m,o,start,end):
            history=[]
            for step in range(start+1,end+1):
                rate=run.learning_rate(step,{**cfg['recipe'],'learning_rate':.01})
                for g in o.param_groups:g['lr']=rate
                plan=plans[step-1];x=torch.randn(3,3)+np.random.rand()+random.random()+sum(plan[0][1])*.001
                o.zero_grad();m(x).square().sum().backward();o.step();history.append((step,rate,plan))
            return history
        m,o=init();whole=steps(m,o,0,206);expected=copy.deepcopy(m.state_dict());optim=copy.deepcopy(o.state_dict())
        m,o=init();steps(m,o,0,200)
        base,_,d,parent=self.fixture();ck=d/'checkpoint_000200'
        # Write fresh immutable payloads in a new checkpoint fixture.
        ck2=base/'native';ck2.mkdir();named=full_ft.named_trainable(m);layout=run.digest(full_ft.shard_layout(named));pins={}
        for rank in range(4):
            result=full_ft.write_rank_shard(ck2,rank,named,o,layout,buffers=full_ft.named_buffers(m))
            for pin in result.values():pins[pin['name']]={k:v for k,v in pin.items() if k!='name'}
            rng=run.rng_state();n=rng['numpy'];rng['numpy']=(n[0],torch.from_numpy(n[1].astype(np.int64)),*n[2:])
            pins[f'rng{rank:03d}.pt']=full_ft._write_payload(ck2/f'rng{rank:03d}.pt',rng)
        bound=load(d/'binding.json');manifest=dict(schema='c1-checkpoint-v1',binding=bound,step=200,
            files=pins,layouts=[layout]*4,trace_program_version='3.14')
        write(ck2/'complete.json',manifest);pin=dict(path=str(ck2/'complete.json'),sha256=sha(ck2/'complete.json'))
        m2,o2=init()
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(run.dist,'get_rank',return_value=0))
            stack.enter_context(patch.object(run.dist,'get_world_size',return_value=1))
            stack.enter_context(patch.object(run.dist,'all_gather_object',side_effect=lambda out,value:out.__setitem__(0,value)))
            stack.enter_context(patch.object(run.dist,'broadcast_object_list',return_value=None))
            stack.enter_context(patch.object(full_ft,'_broadcast',return_value=None))
            native=full_ft._verified_load
            stack.enter_context(patch.object(full_ft,'_verified_load',side_effect=lambda *args:c.optimizer_payload(native(*args))))
            start=run.restore(pin,m2,o2,bound)
        self.assertEqual(start,200);tail=steps(m2,o2,start,206);self.assertEqual(whole[200:],tail)
        for k,v in m2.state_dict().items():self.assertTrue(torch.equal(v,expected[k]),k)
        for i,state in o2.state_dict()['state'].items():
            for k,v in state.items():self.assertTrue(torch.equal(v,optim['state'][i][k]),k)
        self.assertEqual(o2.state_dict()['param_groups'],optim['param_groups'])
        write(ROOT/'out/proof/CONT1_STATE.json',dict(status='PASS',N=206,k=200,state='bit-exact',optimizer='bit-exact',
            lr='exact',rows='exact',rng='torch/numpy/python exact',collectives='single-rank fixture',native_shard_restore=True))

    def test_pass_only_gate_and_time(self):
        script=(ROOT/'out/operator/s.sh').read_text();wrapper=(ROOT/'out/operator/jb.sh').read_text()
        self.assertNotIn('170956',script);self.assertIn("assert go.get('canary') is not True",script)
        self.assertIn("get('resume_pointer',{}).get('status')=='PASS'",script)
        for value in (script,wrapper):self.assertIn('24:00:00',value);self.assertNotIn('13:00:00',value)
        b=load(ROOT/'out/BINDING.json');self.assertEqual(b['proof_partition'],'general')
        for old in ('x_69d2930d','i_69d2930d','a_673bc60f','/r/673bc60f'):self.assertNotIn(old,wrapper)

    def test_runtime_adapter_selects_donor_and_binds_new_output(self):
        base,_,donor,parent=self.fixture()
        # The native restore test above checks payload semantics; this boundary
        # test checks the exact adapter calls made by w.py, including new binding.
        import types
        prep=load(donor/'inputs/p0.json');write(base/'p.json',prep)
        cfg=load(ROOT/'out/config.json');cfg['output']=str(base);cfg['preparation']=dict(path=str(base/'p.json'),sha256=sha(base/'p.json'))
        fake=types.SimpleNamespace(load=load,pinned=run.pinned,full_ft=types.SimpleNamespace(_verified_load=lambda *a:None),
            restore=lambda p,m,o,b: b,latest_resume=lambda *a:None,
            bind_output=lambda out,b,**kw:dict(output=out,binding=b,**kw))
        c.install(fake,cfg,parent)
        selected=fake.latest_resume(base,{'config_sha256':'C'})
        restored=fake.restore(selected,None,None,{'config_sha256':'C'})
        self.assertEqual(restored,load(donor/'binding.json'))
        bound=fake.bind_output(base,{'config_sha256':'C'},resume=True)
        self.assertFalse(bound['resume']);self.assertEqual(bound['binding']['config_sha256'],'C')
        with self.assertRaises(ValueError):fake.restore(dict(path='foreign'),None,None,{})
        changed=copy.deepcopy(prep);changed['streams']['vqa']={'count':1};write(base/'p.json',changed)
        cfg['preparation']['sha256']=sha(base/'p.json')
        with self.assertRaises(ValueError):c.install(fake,cfg,parent)

    def test_derived_resume_chooser(self):
        base,_,donor,parent=self.fixture();kit=Path(load(ROOT/'out/proof/DERIVATION.json')['fixture_paths'][0])
        spec=importlib.util.spec_from_file_location('_cont_r8',kit/'b/r8.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        with patch.dict(sys.modules,{'c0':c}),patch.dict(os.environ,{'TK_KIT_HOME':str(kit)}):
            self.assertEqual(m.main(base,base.parent/'slots','12345'),'u')
        self.assertEqual(load(base.parent/'slots/RUN.json')['run'],base.name)

    def test_proof_fixture_and_pass_gate(self):
        kit=Path(load(ROOT/'out/proof/DERIVATION.json')['fixture_paths'][0])
        spec=importlib.util.spec_from_file_location('_cont_proof',ROOT/'out/proof/p.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
        base=temp();self.assertEqual(p.resume_fixture(kit,base)['status'],'PASS')
        k=base/'k';b=base/'b'
        for path in (k/'k',k/'o',k/'b',b):path.mkdir(parents=True,mode=0o700)
        ids=load(ROOT/'out/operator/ids.json');write(b/'ids.json',ids);(b/'jb.sh').write_bytes((ROOT/'out/operator/jb.sh').read_bytes())
        (k/'b/a.py').write_text('def main(k):pass\n');(k/'SHA256SUMS.txt').write_text('fixture')
        launch=dict(config=dict(file='k/c.json',sha256='a'*64));write(k/'k/launch.json',launch)
        go=dict(production_go_granted=True,config_sha256=ids['identity'],admission_contract_sha256=ids['contract'],
            wrapper_sha256=sha(b/'jb.sh'),manifest_sha256=sha(k/'SHA256SUMS.txt'));write(b/'go.json',go)
        required=load(ROOT/'out/proof/inputs.json')['required_checks']
        proof=dict(status='PASS',rc=0,job='12345',config_identity=ids['identity'],contract_sha256=ids['contract'],
            config=launch['config'],manifest_sha256=go['manifest_sha256'],wrapper_sha256=go['wrapper_sha256'],cuda_visible_devices='',
            effective_config_verified=True,first_batch_executed=False,training_executed=False,admission_result={'status':'PREPARED'},
            prepared_seals={'fixture':True},real_job_reuse=False,checks={key:{'status':'PASS'} for key in required})
        body=(ROOT/'out/operator/s.sh').read_text().split("<<'P'\n",1)[1].split('\nP\n',1)[0]
        for mutation in ('valid','pointer','status','canary'):
            value=copy.deepcopy(proof);g=copy.deepcopy(go)
            if mutation=='pointer':value['checks']['resume_pointer']['status']='FAIL'
            if mutation=='status':value['status']='RUNNING'
            if mutation=='canary':g['canary']=True
            write(k/'o/12345.proof.json',value);write(b/'go.json',g)
            result=subprocess.run([sys.executable,'-I','-B','-',str(k),str(b)],input=body,text=True,
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={**os.environ,'PROOF_JOB':'12345'})
            self.assertEqual(result.returncode==0,mutation=='valid',result.stderr)

if __name__=='__main__':unittest.main(verbosity=2)
