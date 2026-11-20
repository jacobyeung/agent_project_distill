import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
os.environ['CUDA_VISIBLE_DEVICES']=''
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE))
import contextlib
import hashlib
import importlib.util
import json
import runpy
import tempfile
import types
import unittest
from unittest.mock import patch
import numpy as np
import relift as R
import depth_format as D


def temp():return Path(tempfile.mkdtemp(dir=HERE/'tests',prefix='case_'))


class ReliftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):R.dependencies()

    def test_format_exact_and_half(self):
        rng=np.random.default_rng(42);depth=rng.uniform(.1,12,(32,51,51))
        g=types.SimpleNamespace(depth_grid=depth,grid_uv=np.linspace(0,1000,51))
        row=D.encode(g,{'capture':'test'});actual,uv=D.decode(row)
        self.assertTrue(np.array_equal(depth,actual));self.assertTrue(np.array_equal(uv,g.grid_uv))
        self.assertTrue(np.array_equal(D.decode(row,half_only=True)[0],depth.astype('float16').astype('float64')))
        p=temp()/'0.gz';w=D.Writer(p);w.append(row);w.close()
        import gzip
        with gzip.open(p,'rt') as f:self.assertEqual(json.loads(f.readline()),row)
        w=D.Writer(temp()/'0.gz',cap=64)
        with self.assertRaisesRegex(ValueError,'return cap'):w.append(row)
        w.close();self.assertLessEqual(w.bytes,64)

    def test_gt_mask_known_box(self):
        # All four mask-pixel centers lift through the actual deployed bestspread
        # and min-area functions, with a known tilted depth plane.
        def lift(frame,uv,mode):
            p=np.c_[uv/1000,1+uv[:,0]/1000+uv[:,1]/1000]
            return p,p,np.zeros(len(p))
        g=types.SimpleNamespace(C=np.repeat(np.eye(4)[None],32,0),has=lambda f:True,lift=lift)
        masks=np.zeros((32,4,4),bool);masks[:3,1:3,1:3]=True
        obj=R.grounding.lift_bestspread('x',masks,g)
        b=R.grounding.min_area_box(np.asarray(obj['points']['1']))
        np.testing.assert_allclose(b['centroid'],[.5,.5,2.])
        np.testing.assert_allclose(np.sort(b['axesLengths']),[.25,.25,.5])
        self.assertEqual(obj['best'],1);self.assertEqual(obj['frames'],[1,2,3])

    def test_voted_box_extends_best_with_multiview_support(self):
        def lift(frame,uv,mode):
            p=np.c_[uv/1000,1+uv[:,0]/1000+uv[:,1]/1000]
            if frame>1:p[:,0]+=.5
            return p,p,np.zeros(len(p))
        rotation=np.array([[1.,0.,0.],[0.,0.,1.],[0.,-1.,0.]])
        g=types.SimpleNamespace(C=np.repeat(np.eye(4)[None],32,0),has=lambda f:True,lift=lift,cam=lambda f:(rotation,np.zeros(3)))
        masks=np.zeros((32,4,4),bool);masks[:3,1:3,1:3]=True
        value=R.voted_box('x',masks,g)
        np.testing.assert_allclose(np.sort(value['lengths']),[.25,.5,.75])
        np.testing.assert_allclose(value['centre'],[.75,2.,.5])
        # With only one shifted view there is no cross-view support outside
        # the tied largest view, so the vote must retain the original box.
        masks[2]=False
        value=R.voted_box('x',masks,g)
        np.testing.assert_allclose(np.sort(value['lengths']),[.25,.25,.5])

    def test_pose_transport_same_reference(self):
        pts=np.array([[1.,2.,3.],[0.,0.,0.]])
        c=np.eye(4);c[:3,3]=[1,2,3]
        np.testing.assert_allclose(R.pose.transport(pts,c,c),pts)

    def test_gt_pose_replaces_relative_translation(self):
        rotation=np.array([[1.,0.,0.],[0.,0.,1.],[0.,-1.,0.]])
        served=np.repeat(np.eye(4)[None],32,0);served[:,:3,:3]=rotation
        served[1,0,3]=10.
        cameras=served.copy();cameras[1,0,3]=2.
        def lift(frame,uv,mode):
            pc=np.c_[uv[:,0]/1000,1+uv[:,0]/1000,2+uv[:,1]/1000]
            p=pc@rotation.T+served[frame-1,:3,3]
            return p,pc,np.zeros(len(p))
        g=types.SimpleNamespace(C=served,has=lambda f:True,lift=lift,cam=lambda f:(rotation,served[f-1,:3,3]))
        masks=np.zeros((32,4,4),bool);masks[1,1:3,1:3]=True
        old,_=R.fit_lift('x',masks,g)
        new,_=R.fit_lift('x',masks,g,gt_cameras=cameras)
        same,_=R.fit_lift('x',masks,g,gt_cameras=served)
        np.testing.assert_allclose(new['centre']-old['centre'],[-8,0,0])
        np.testing.assert_allclose(new['lengths'],old['lengths'])
        np.testing.assert_allclose(same['centre'],old['centre'])

    def test_paired_room_bootstrap_all_cells_and_dataset_splits(self):
        refs={str(i):{'task':{'room':str(i)}} for i in range(3)}
        rows=[dict(item_id=str(i),room=str(i),dataset=d,**{k:0. if k=='a' else 10. for k in 'abcdefg'})
              for i,d in enumerate(('ARKit','ScanNet/ScanNet++'))]
        result=R.stats(rows,refs)
        self.assertEqual([x['dataset'] for x in result],['all','ARKit','ScanNet/ScanNet++'])
        for cell in result:
            self.assertEqual(set(cell['cells']),set('abcdefg'))
            self.assertEqual(cell['versus_a']['e']['ci95'],[10.,10.])
            self.assertEqual(cell['reading'],'grounding binds; arm A opens')
            self.assertEqual(cell['versus_a']['e']['defined_draws']+cell['versus_a']['e']['undefined_draws'],10000)

    def test_low_score_proposals_use_deployed_producers(self):
        from gpkg.runtime.c import rle
        from student_pilot import routed_features as F
        cameras=np.repeat(np.eye(4)[None],32,0)
        cameras[:,:3,:3]=np.array([[1.,0.,0.],[0.,0.,1.],[0.,-1.,0.]])
        K=np.repeat(np.array([[320.,0.,320.],[0.,240.,240.],[0.,0.,1.]])[None],32,0)
        A=np.repeat(np.diag([.64,.48,1.])[None],32,0)
        g=R.geometry.from_arrays(K=K,canvas_to_source=A,camera_to_world=cameras,scale=1.,
            depth_grid=np.full((32,51,51),4.),grid_uv=np.linspace(0,1000,51),anchor_frame_indices=list(range(32)))
        mask=np.zeros((480,640),bool);mask[100:200,100:200]=True
        obj=dict(name='x',proposals=[dict(frame=1,score=.2,presence=1.,mask=rle(mask))])
        grids=F.candidates.lift_grid(g)
        pool,diag=R.relaxed_pool(obj,g,grids)
        self.assertEqual(diag['raw_below_score_gate'],1);self.assertEqual(len(pool),1)
        np.testing.assert_array_equal(pool[0][1][0],mask[::2,::2])
        raw=[[dict(mask=mask,score=.2,presence=1.)]]+[[] for _ in range(31)]
        original,_=F.candidates.lift(F.cache_for('x',raw),'x',g,floor=.3,grids=grids,phrase='x')
        self.assertEqual(original,[])

    def test_oracles_and_gate(self):
        truth=np.zeros((32,240,320),bool);truth[0,10:30,20:40]=1
        part=truth.copy();part[0,20:]=0
        chosen,info=R.oracle([('part',part),('whole',truth)],truth)
        self.assertEqual(info['id'],'whole');self.assertTrue(np.array_equal(chosen,truth))
        chosen,info=R.oracle([('first',truth),('second',truth)],truth);self.assertEqual(info['id'],'first')
        z=lambda m,l,h:dict(mean=m,ci95=[l,h])
        self.assertEqual(R.registered(z(8,1,12),z(6,1,9)),'grounding binds; arm A opens')
        self.assertEqual(R.registered(z(8,1,12),z(5,1,9)),'grounding binds; completeness binds')
        self.assertEqual(R.registered(z(4,-1,7),z(0,-1,1)),'grounding does not limit this half')
        self.assertEqual(R.registered(z(7,1,12),z(6,1,9)),'undecided until rank 5')

    def test_real_t1_depth_free_twenty(self):
        refs={r['item_id']:r for r in json.loads((R.KIT/'items544.json').read_text())['items']}
        rows=R.read_records(R.BASE/'cap/t1.gz',refs)
        checks=R.depth_free_parity(rows,refs,limit=20)
        self.assertEqual(len(checks),20);self.assertTrue(all(c['match'] for c in checks))
        R.dump(HERE/'out/REAL_PARITY_20.json',dict(tolerance_m=0.,checks=checks,passed=True))


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import build_depth as BD
        cls.BD=BD;cls.B=BD.B
        cls.info=json.loads((HERE/'out/BUILD.json').read_text())
        cls.root=temp();cls.package=cls.root/'package';cls.payload=cls.root/'p'
        cls.B.extract((HERE/'out/delivery.tgz').read_bytes(),cls.package)
        cls.B.extract((cls.package/'0.tgz').read_bytes(),cls.payload)
        sys.path[:0]=[str(cls.payload/'b'),str(cls.payload/'tree'),str(cls.payload)]
        import l
        l.install(cls.payload)

    def test_package_pins_and_resource_argv(self):
        info=self.info
        for n,h in info['files'].items():self.assertEqual(R.sha(self.package/n),h)
        for n,h in info['payload_files'].items():self.assertEqual(R.sha(self.payload/n),h)
        from orchard_h10.common import submit_argv
        argv=submit_argv(info['token'],1,'00:50:00')
        for arg in ('--exclude=orchard-community-4','--mem=200G','--partition=general','--gres=gpu:1','--cpus-per-task=16'):self.assertIn(arg,argv)
        plan=json.loads((self.payload/'9.json').read_text());self.assertEqual(plan['stop_margin'],270)
        for n in info['changed_payload']:
            if n.endswith('.py'):compile((self.payload/n).read_bytes(),n,'exec')
        for n,v in info['layout']['sources'].items():self.assertEqual(R.sha(self.payload/n),v['sha256'])

    def test_operator_entry_check_stub_weights(self):
        # Execute the delivered operator rehearsal, including real StageOne
        # selection with its CPU stub weights and the dump round-trip check.
        from g import w
        root=temp();settings=root/'0.json'
        settings.write_text(json.dumps(dict(tree=str(self.payload/'tree'),perception_memo='off',perception_memo_modules=['g3t'],perception_memo_verify_ids=[])))
        op=runpy.run_path(str(self.package/'a/6.py'))
        cfg=dict(package=str(self.payload),output=str(root/'r'),settings=str(settings),python=sys.executable,
          plan_sha256=self.info['plan_sha256'],inputs_sha256='1'*64,operator_sha256=R.sha(self.package/'a/6.py'),
          export_pin='0.json',export='e',binding='b',device='cpu',prefix=[])
        # Previous tests intentionally import the pinned same reader from its
        # source tree. The fresh-process check separately enforces provenance.
        with patch.object(w,'bind_reader_root',return_value=self.payload/'b'):
            result=op['rehearsal'](cfg)
        self.assertEqual(result[0]['expected'],150)
        self.assertTrue(op['memory_probe'](cfg)['fits'])
        # Exercise the existing-file comparison as well as the first copy.
        with patch.object(w,'bind_reader_root',return_value=self.payload/'b'):
            self.assertEqual(op['rehearsal'](cfg),result)
        import j
        import layout
        def check(value, name):
            hits=[word for word in layout.DENY if word in value.lower()]
            self.assertEqual(hits,[],str(name))
        def strings(value):
            if isinstance(value,str):yield value
            elif isinstance(value,dict):
                for key,item in value.items():yield key;yield from strings(item)
            elif isinstance(value,list):
                for item in value:yield from strings(item)
        files=[]
        for path in sorted((root/'r').rglob('*')):
            name=path.relative_to(root/'r')
            check(str(name),name)
            if not path.is_file():continue
            data=path.read_bytes()
            check(data.decode('utf-8',errors='replace'),name)
            if path.suffix=='.json':
                # Decode JSON escapes with the unpatched parser. The a0 value
                # remains opaque on disk; its logical contents retain provenance.
                for value in strings(j.wire_loads(data)):check(value,name)
            files.append(dict(path=str(name),bytes=len(data),sha256=R.sha(path)))
        copied=root/'r/metadata/a/3.json'
        source=self.payload/self.info['layout']['paths']['items/devs1_routed.json']
        self.assertEqual(copied.read_bytes(),source.read_bytes())
        self.assertEqual(set(j.wire_loads(copied.read_bytes())),{'a0'})
        self.assertEqual(j.loads(copied.read_bytes()),j.loads(source.read_bytes()))
        R.dump(HERE/'out/CPU_ENTRY_STUB.json',dict(passed=True,stub_weights=True,actual_operator_rehearsal=True,
           delivery_sha256=self.info['delivery_sha256'],delivery_bytes=self.info['delivery_bytes'],
           entries=result,payload=self.info['payload_sha256'],plan=self.info['plan_sha256'],
           output_scan=dict(passed=True,raw=True,decoded_json=True,deny=list(layout.DENY),files=files),
           item_copy_exact=True,repeated_rehearsal=True))

    def test_numeric_entry_dispatch_stub_weights(self):
        from g import w
        import orchard_h10.common as common
        root=temp();config=root/'30.json'
        config.write_text(json.dumps(dict(action=3,package=str(self.payload),config={},stop_at=1)))
        called=[]
        def worker(cfg,stop_at):
            self.test_capture_one_real_geometry_stub_prefill()
            called.append(True)
            return dict(failure=None)
        from orchard_h10.runner import control
        entry=control(dict(package=str(self.payload),output=str(root/'r')))/'5.py'
        with patch.object(common,'install_process_guard'),patch.object(w,'run',side_effect=worker),patch.object(sys,'argv',[str(entry),str(config)]):
            with self.assertRaises(SystemExit) as end:runpy.run_path(str(entry),run_name='__main__')
        self.assertEqual(end.exception.code,0);self.assertEqual(called,[True])

    def test_failed_parity_preserves_complete_return(self):
        import torch
        from g import w
        import h1eval.h10.parity_adapter as adapter
        from e2e_reader import parity
        import h1eval.items as items
        refs=w.load_rows();reference=json.loads((self.payload/'g/8.json').read_text())
        manifests={r['task']['native']:r['mapping']['frame_binding_sha256'] for r in refs}
        original_digest=items.digest
        def digest(v):return v['anchors'] if 'anchors' in v else original_digest(v)
        def one(gen,bound,ref,**kw):
            md=dict(reference['geometry'][ref['item_id']]['geometry'])
            md['scale']+=1.
            return dict(metadata=dict(capture=ref['capture'],geometry=md),timings={})
        root=temp();cfg=dict(output=str(root/'r'),settings='0.json',stop_file=str(root/'stop'))
        settings=dict(save_own_depth=False,perception_memo_modules=['g3t'],export_dir='e',artifact_manifest='a')
        factory=types.SimpleNamespace(load_info={'export':{'step':544}},generator=types.SimpleNamespace(perception=types.SimpleNamespace(memo=None)))
        with patch.object(w,'start_tower',return_value=(None,{})),patch.object(torch.cuda,'reset_peak_memory_stats'),patch.object(torch.cuda,'max_memory_allocated',return_value=0),patch.object(w,'bind_reader_root',return_value=self.payload/'b'),patch.object(w,'assert_reader_root'),patch.object(adapter,'settings_for',return_value=settings),patch.object(adapter,'prepare_runtime'),patch.object(adapter,'artifact_spec',return_value=None),patch.object(adapter,'make_capped_real',return_value=factory),patch.object(parity,'_captures',return_value=manifests),patch.object(parity,'bind_item',return_value={}),patch.object(items,'digest',side_effect=digest),patch.object(w,'capture_one',side_effect=one),patch.object(torch.cuda,'get_device_name',return_value='H100'),patch.object(torch.cuda,'synchronize'):
            result=w.run(cfg,100.,clock=lambda:0.)
        receipt=json.loads((root/'r/metadata/PARITY.json').read_text())
        self.assertTrue(result['complete']);self.assertEqual(result['completed'],60)
        self.assertFalse(receipt['trusted']);self.assertEqual(receipt['capture_records'],60)
        self.assertTrue((root/'c/0.gz').is_file())

    def test_capture_one_real_geometry_stub_prefill(self):
        import torch
        from g import w
        from e2e_reader.generate import Perception
        from e2e_reader.real import own_gravity
        from student_pilot import carrier_c1_decode,ground_context
        from e2e_reader import artifact
        model=torch.nn.Linear(1,1,bias=False)
        wrapper=types.SimpleNamespace(model=types.SimpleNamespace(language_model=model))
        state=types.SimpleNamespace(heads=types.SimpleNamespace(gravity=np.array([0.,-1.,0.])))
        def prepare(*a,**kw):model(torch.ones((1,1)));return state
        raw=np.zeros((32,9));raw[:,6]=1;raw[:,7:]=1.2
        tower=dict(raw_pose9=raw,anchor_slots=np.arange(32),frame_indices=np.arange(32),
                   depth_grid=np.full((32,51,51),2.),grid_uv=np.linspace(0,1000,51),source_hw=(480,640))
        perception=Perception(lambda f:tower,own_gravity,lambda t:torch.tensor(np.log(2.)),socket=lambda *a:(_ for _ in ()).throw(AssertionError('socket called')))
        gen=types.SimpleNamespace(model=wrapper,processor=None,device='cpu',perception=perception,
               prompt_batch=lambda *a:{},artifact=None)
        frames=dict(anchor_indices=list(range(32)),dense_indices=list(range(32)),anchor_slots=list(range(32)),
                    native_frames=[types.SimpleNamespace(height=480,width=640)]*32)
        ref=dict(item_id='0',capture='0',source_indices=list(range(32)),mapping=dict(dense_count=32,frame_binding_sha256='a'*64))
        @contextlib.contextmanager
        def audit(*a):yield types.SimpleNamespace(entries=0)
        with patch.object(carrier_c1_decode,'_prepare_decode',prepare),patch.object(ground_context,'closed_adapters',side_effect=lambda f:f),patch.object(artifact,'Audit',audit):
            row=w.capture_one(gen,dict(frames=frames,row={}),ref)
        d,_=D.decode(row)
        self.assertEqual(row['prefills'],1);self.assertEqual(row['decode_steps'],0)
        self.assertEqual(d.shape,(32,51,51));self.assertTrue(np.all(d==4.))
        self.assertTrue(w.compare(row['metadata']['geometry'],row['metadata']['geometry'],{'scale':0.})['trusted'])
        x=dict(row['metadata']['geometry'],scale=3.)
        self.assertFalse(w.compare(x,row['metadata']['geometry'],{'scale':0.})['trusted'])


if __name__=='__main__':unittest.main(verbosity=2)
