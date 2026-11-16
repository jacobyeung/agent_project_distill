from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
from copy import deepcopy
import ast,sys,unittest,uuid
B=Path(__file__).resolve().parents[1];R=B.parents[1];sys.path.append(str(B/'code'))
from adapter import *
import engine,proof,budget,pixels,report,o
from boundary import Boundary
SPEC=dict(tree=str(R/'from113/work/tree'),artifact={'path':'fixture','sha256':digest('fixture')},config={'path':'fixture','sha256':digest('fixture')})
engine.initialize(SPEC)

class Fixes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=B/'work'/('b_'+uuid.uuid4().hex);cls.root.mkdir()
    def test_cpu_preparation_bit_equality(self):
        import geometry as G,gravity_guard as guard,geometry_refusals as GR
        import numpy as np,torch
        from student_pilot.tower_read import TowerState
        from student_pilot.geometry_profiles import GeometryError
        p=B/'work/raw_actual.npz'
        family=load(R/'work/c8r/FAMILY.json');asset=next(x for x in family['assets']['small_objects'] if x['role']=='geometry')
        member='g3s32/g3t/arkitscenes__42898635.npz';self.assertEqual(sha(p),asset['members'][member]['sha256'])
        state=TowerState.from_npz(p);c=dict(native='c0',anchor_indices=state.frame_indices[state.anchor_slots].tolist())
        row={'qid':'q0'};batch={'input_ids':torch.tensor([[1,2]])}
        class Head:
            def query(self,m,uv):return torch.full((32,51*51),2.,dtype=torch.float64)
        with np.load(p) as z:up=z['gravity_up'].copy()
        own=NS(depth_map=torch.ones(1),gravity=up,depth_head=Head())
        # Execute the exact original C8r nested function with synthetic checkpoint heads.
        original=R/'work/c8r/code/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py'
        tree=ast.parse(original.read_text());node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='prepare_one')
        diagnostics={};output=self.root/'old.npz'
        ctx=dict(vars(G),np=np,torch=torch,TowerState=TowerState,p=p,c=c,args=NS(device='cpu'),
                 processor=None,model=None,cfg={},runtime=NS(prompt_batch=lambda *a:batch),
                 trainer_row=lambda *a,**k:row,by_native={'c0':{}},row=row,output=output,diagnostics=diagnostics,
                 prefill=lambda *a,**k:NS(heads=own))
        exec(compile(ast.Module(body=[node],type_ignores=[]),str(original),'exec'),ctx)
        with guard.capture('cpu_old','c0'):old=GR.attempt(ctx['prepare_one'],GeometryError)
        other={}
        with guard.capture('cpu_new','c0'):
            new=GR.attempt(lambda:G.prepare_capture(p,c,row,self.root/'new.npz',lambda r:(own,batch),other),GeometryError)
        self.assertEqual(old,new);self.assertEqual(diagnostics,other)
        def record(value,diag,path):return dict(native='c0',status=value['status'],error=value['error'],diagnostics=diag,output=pin(path),**value['data'])
        check=proof.compare_geometry({'records':[record(new,other,self.root/'new.npz')]},{'records':[record(old,diagnostics,output)]},self.root/'G.json')
        self.assertEqual(check['identical'],1)
        with np.load(output) as a,np.load(self.root/'new.npz') as b:
            for key in ('scale','camera_to_world','K'):self.assertEqual(a[key].tobytes(),b[key].tobytes())
        g=guard.report();self.assertEqual(g['cpu_old'],g['cpu_new'])
        dump(B/'out/GEOMETRY_CPU.json',dict(passed=True,original=pin(original),new=pin(G.__file__),raw=pin(p),compared=['scale','camera_to_world','K','guard decision','prefill token digest','diagnostics'],synthetic_heads=True,raw_source=dict(archive_sha256=asset['sha256'],member=member,member_sha256=asset['members'][member]['sha256'])))
    def test_synthetic_video(self):
        import av,numpy as np
        from PIL import Image
        folder=self.root/'video';folder.mkdir();video=folder/'a.mp4'
        with av.open(str(video),'w') as container:
            stream=container.add_stream('libx264',rate=24);stream.width=32;stream.height=32;stream.pix_fmt='yuv420p';stream.options={'crf':'0'}
            for i in range(40):
                frame=av.VideoFrame.from_ndarray(np.full((32,32,3),i*5,dtype=np.uint8),format='rgb24')
                for packet in stream.encode(frame):container.mux(packet)
            for packet in stream.encode():container.mux(packet)
        indices=[i*39//31 for i in range(32)];frames=[]
        with av.open(str(video)) as container:
            for i,frame in enumerate(container.decode(video=0)):
                if i not in indices:continue
                p=folder/(str(i)+'.png');Image.fromarray(frame.to_ndarray(format='rgb24')).save(p)
                frames.append(dict(index=i,png=pin(p)))
        selection=folder/'selection.json';dump(selection,dict(frames=frames,total_num_frames=40))
        result=pixels.compare(video,selection,folder,sha(video));self.assertEqual(result['identical_frames'],32);self.assertEqual(result['decoded_frames'],40);self.assertEqual(result['fps'],24)
        p=Path(frames[0]['png']['path']);x=np.asarray(Image.open(p)).copy();x[0,0,0]+=1;Image.fromarray(x).save(p);frames[0]['png']=pin(p);dump(selection,dict(frames=frames,total_num_frames=40))
        changed=pixels.compare(video,selection,folder,sha(video));self.assertEqual(changed['identical_frames'],31);self.assertEqual(changed['frames'][0]['max_absolute_difference'],1);self.assertIsNotNone(changed['frames'][0]['psnr_db'])
        media=folder/'media.json';pins=folder/'pins.json'
        dump(media,{'scannet:a':{'frame_receipt':pin(selection)}});dump(pins,{'files':{'a':{'sha256':sha(video)}}})
        with patch.object(pixels,'SCENES',('a',)):
            actual=pixels.run(folder,folder.parent,media,pins,folder/'RESULT.json')
        self.assertEqual(actual['status'],'complete');self.assertEqual(actual['compared_frames'],32)
        dump(B/'out/RELEASE_CHECK_SYNTHETIC.json',dict(passed=True,identical=result,perturbed=changed,synthetic=True))
    def test_deadline_and_rates(self):
        b=budget.Budget('2026-11-16T16:15:00Z',return_seconds=300,clock=lambda:budget.timestamp('2026-11-16T16:07:00Z'))
        self.assertTrue(b.allows('camera_displacement'));self.assertTrue(b.allows('other'))
        b.observe('other',10);self.assertTrue(b.allows('other'));self.assertEqual(b.projected('other'),12.5);self.assertEqual(b.remaining(),180)
        with self.assertRaises(ValueError):budget.timestamp('2026-11-16T16:15:00')
        with self.assertRaises(ValueError):b.observe('other',-1)
    def test_resume_disjoint_and_pin_rejection(self):
        root=self.root/'resume';bound=prepare(R/'in/vsti/vstibench_repr_450_v3.json',R/'in/vsti/media.json',R/'in/vsti/frames_sample',root/'i',True)
        raw=engine.synthetic_tower(bound,root/'raw');geometry=engine.prepare_geometry(bound,SPEC,raw,root/'g',Boundary())
        refs=load(B/'work/proof_reference.json');proof.compare(refs,refs,refs,root/'P0.json',True)
        calls=iter([True]*3+[False])
        with patch.object(budget.Budget,'allows',side_effect=lambda k:next(calls)):
            first=engine.run(root/'i/BOUND.json',SPEC,geometry,root/'j0',boundary=Boundary(),proof_path=root/'P0.json')
        self.assertEqual(first['reason'],'deadline');self.assertEqual(len(first['keys']),3)
        second=engine.run(root/'i/BOUND.json',SPEC,geometry,root/'j1',boundary=Boundary(),resume=[root/'j0'])
        self.assertFalse(set(first['keys'])&set(second['keys']))
        merged=engine.merge(root/'i/BOUND.json',[root/'j0',root/'j1'],root/'MERGED.json');self.assertTrue(merged['complete'])
        with self.assertRaises(ValueError):engine.merge(root/'i/BOUND.json',[root/'j1',root/'j0'],root/'BAD.json')
        report.build(root/'MERGED.json',root/'report')
        b=deepcopy(merged);b['synthetic']=False;dump(root/'REAL.json',b)
        with self.assertRaisesRegex(ValueError,'requires the in-job'):report.build(root/'REAL.json',root/'bad')
        refs=load(B/'work/proof_reference.json');p=proof.compare(refs,refs,refs,root/'P.json');p['read_binding']=b['request_binding'];dump(root/'P.json',p)
        b['proof']=pin(root/'P.json');dump(root/'REAL.json',b)
        result=report.build(root/'REAL.json',root/'withproof',release_path=B/'out/RELEASE_CHECK.json')
        self.assertIn('10/10 identical',result['proof_summary']);self.assertIn('av 15.1',result['frames'])
        self.assertIn('Release-video pixel check: '+load(B/'out/RELEASE_CHECK.json')['status'],result['frames'])
    def test_refused_geometry_is_scored(self):
        import geometry_refusals as GR
        root=self.root/'refused';b=prepare(R/'in/vsti/vstibench_repr_450_v3.json',R/'in/vsti/media.json',R/'in/vsti/frames_sample',root/'i',True)
        raw=engine.synthetic_tower(b,root/'raw');g=engine.prepare_geometry(b,SPEC,raw,root/'g',Boundary())
        manifest=load(g);manifest['videos']={}
        for r in manifest['records']:r.update(status='REFUSED',output=None,error=dict(code=GR.NONFATAL_CODE,message=GR.NONFATAL_CODE,exception='GeometryError'))
        dump(root/'REFUSED.json',manifest)
        result=engine.run(root/'i/BOUND.json',SPEC,root/'REFUSED.json',root/'j',boundary=Boundary())
        self.assertFalse(result['missing']);self.assertTrue(all(r['score']==0 and r['no_final_answer'] for r in rows(root/'j/items.jsonl') if r['question_type'] in CAMERA));self.assertTrue(all(not r['no_final_answer'] for r in rows(root/'j/items.jsonl') if r['question_type'] not in CAMERA))
    def test_relocation_and_production_order(self):
        root=self.root/'relocate'
        b=prepare(R/'in/vsti/vstibench_repr_450_v3.json',R/'in/vsti/media.json',R/'in/vsti/frames_sample',root,True)
        updated=relocate_input(root,'/i');self.assertEqual(updated['frames_root'],'/i/store')
        for p in updated['inputs'].values():self.assertTrue(p['path'].startswith('/i/'))
        # Production validation checks fixed ordering independently of pixel staging.
        tasks=[dict(id='q'+str(t['id']),question_type=t['question_type']) for t in load(R/'in/vsti/vstibench_repr_450_v3.json')]
        target=self.root/'tasks.jsonl';target.write_text(''.join(json.dumps(t)+'\n' for t in tasks))
        canary,post=order(tasks);b.update(synthetic=False,canary=canary,post_canary=post,keys=canary+post,inputs={'TASKS.jsonl':pin(target)})
        b['binding']=digest({k:v for k,v in b.items() if k!='binding'});dump(self.root/'B.json',b)
        self.assertFalse(validate_bound(self.root/'B.json')['synthetic'])
    def test_complete_primary_cluster_interval(self):
        data=[dict(scene=str(i),room=str(i),question_type=t,score=1. if i%2 else 0.) for t in report.TYPES for i in range(6)]
        value=report.interval(data,list(report.TYPES));self.assertLessEqual(value['low'],.5);self.assertGreaterEqual(value['high'],.5)
        self.assertEqual(report.estimate(data,list(report.TYPES)),.5)
    def test_complete_journal_return_archive(self):
        _,_,transport,_,_=o.imports()
        root=self.root/'return';root.mkdir();(root/'j0').mkdir();(root/'cell/g/scaled').mkdir(parents=True)
        (root/'j0/items.jsonl').write_text('{"key":"q0"}\n');(root/'cell/g/scaled/a.npz').write_bytes(b'fixture array')
        dump(root/'COMPLETE.json',dict(complete=True,plan_sha256='a'*64,synthetic=False))
        original=transport.S.members
        with patch.object(transport,'identity',return_value=self.root/'pool'),patch.object(transport,'pool_operation',return_value=dict(verified=True)),patch.object(transport,'upload',return_value=dict(verified=True)):
            result=o.publish_read(transport,root,'123456789abcdef012345678','a'*64,0)
        self.assertTrue(result['complete']);self.assertIs(transport.S.members,original)
        import tarfile
        with tarfile.open(Path(result['local_return'])/'result.tar.gz') as archive:
            self.assertIn('j0/items.jsonl',archive.getnames());self.assertIn('cell/g/scaled/a.npz',archive.getnames())
        dump(B/'out/RETURN_CPU.json',dict(passed=True,synthetic=True,remote_channels='mocked; not executed',archive=pin(Path(result['local_return'])/'result.tar.gz')))
    def test_primary_packet(self):
        family=load(B/'out/FAMILY.json');records=deepcopy(family['added'])
        for key,row in records.items():
            row.update(sha256=row['sha256'] or 'a'*64,bytes=row['bytes'] or 100,generation='123',verified=True)
        path=self.root/'receipts.json';dump(path,records)
        dest=self.root/'packet'
        config=o.packet(B/'out/FAMILY.json',path,dest,'123456789abcdef012345678',time_limit='03:30:00')
        batch=(dest/'a.sh').read_text();self.assertIn('--gres=gpu:h100:1',batch);self.assertIn('--partition=general',batch)
        self.assertIn('--job-name=a15_cot_ap123456789abcdef012345678',batch)
        self.assertEqual(config['family']['parent_config']['assets'],family['parent_config']['assets'])
        self.assertIsNone(config['resume'])
    def test_proof_type_counts(self):
        from collections import Counter
        refs=load(B/'work/proof_reference.json')
        self.assertEqual(Counter(r['question_type'] for r in refs),{'camera_displacement':3,'camera_movement_direction':3,'camera_rotation':4})
    def test_addition_pins(self):
        records={k:dict(path=o.PREFIX+k+'.tar',name=o.CLOUD+k+'.tar',sha256='a'*64,bytes=100,generation='123',verified=True) for k in 'abcd'}
        self.assertEqual(o.validate_additions(records),records)
        for field,value in [('generation',None),('sha256','bad'),('verified',False),('path','bad')]:
            bad=deepcopy(records);bad['a'][field]=value
            with self.assertRaises(ValueError):o.validate_additions(bad)

if __name__=='__main__':unittest.main(verbosity=2)
