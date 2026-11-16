import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
from PIL import Image

KIT=Path(os.environ.get('DEVS1_KIT',Path(__file__).resolve().parents[1]/'kit')).resolve()
sys.path.insert(0,str(KIT))
from devs1_anchors import build,uniform,verify_frames,sha,save,path_for,select_dense,validate_capture
from devs1_heads import heads
from devs1_run import free_card,free_disk,checkpoints,guarded,merge_anchors,preflight
from rk.g3t import manifest_entries,load_images

TMP=Path(os.environ['TMPDIR'])
REF=KIT/'fixtures/geo'

def temp():return Path(tempfile.mkdtemp(dir=TMP))

def fixture(n=128):
    root=temp();frames=root/'frames';pins=[]
    for i in range(n):
        image=np.zeros((12,16,3),np.uint8);image[:]=[i%256,(i*3)%256,(i*7)%256]
        f=io.BytesIO();Image.fromarray(image).save(f,format='PNG');raw=f.getvalue();s=hashlib.sha256(raw).hexdigest();p=frames/s[:2]/(s+'.png');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        pins.append(dict(index=i*3,path=str(p.relative_to(frames)),sha256=s))
    anchors=[p['index'] for p in (pins[::4] if n==128 else pins)];dense,slots=select_dense(pins,anchors);k=len(dense)
    capture=dict(scene='scannet/fixture',group='g3s'+str(k),dense=dense,anchor_slots=slots,anchor_indices=anchors,hw=[12,16],total_num_frames=n*3)
    plan=dict(captures=[capture],files=pins);save(root/'PLAN.json',plan)
    return root,frames,plan

def stub(root,plan):
    c=plan['captures'][0];n=len(c['dense']);slots=np.array(c['anchor_slots'],np.int64);indices=np.array([p['index'] for p in c['dense']],np.int64)
    raw=np.zeros((n,9),np.float64);raw[:,6]=1;raw[:,0]=np.arange(n)/10;raw[:,7:]=[1,1.2]
    shape=(32,51,51);depth=np.ones(shape,np.float32);conf=np.arange(np.prod(shape),dtype=np.float32).reshape(shape);uv=np.linspace(0,1000,51,dtype=np.float32)
    g=root/'g3t';v=root/'own';g.mkdir();v.mkdir()
    np.savez(g/'scannet__fixture.npz',raw_pose=raw,raw_pose32=raw[slots],frame_indices=indices,anchor_slots=slots,source_hw=np.array([12,16],np.int64),depth_grid=depth,depth_conf_grid=conf,grid_uv=uv,gravity_up=np.array([0.,-1.,0.]))
    own=raw[slots].copy();own[:,:3]+=999;own[:,7:]=.5
    np.savez(v/'scannet__fixture.npz',raw_pose=own,frame_indices=indices[slots],depth_grid=depth*2,grid_uv=uv,gravity_up=np.array([0.,-2.,0.]))
    return g,v,raw,slots

class Anchors(unittest.TestCase):
    def test_registry_identity_and_interleaving(self):
        r,f,p=fixture();c=p['captures'][0];validate_capture(c)
        self.assertEqual([c['dense'][i]['index'] for i in c['anchor_slots']],list(range(0,384,12)))
        self.assertEqual(c['anchor_slots'],list(range(0,64,2)))
        self.assertEqual(len(c['dense']),64)
    def test_anchor_manifest_e0_reader_and_resume(self):
        r,f,p=fixture();build(p,f,r/'anchors');a=merge_anchors(r,p,'g3s64');entry=next(iter(manifest_entries(a/'A_MANIFEST.json').values()));images,hw=load_images(entry,f)
        self.assertEqual((len(images),hw),(32,(12,16)))
        before={x.name:(sha(x),x.stat().st_mtime_ns) for x in a.glob('*.json')};build(p,f,r/'anchors');merge_anchors(r,p,'g3s64')
        self.assertEqual(before,{x.name:(sha(x),x.stat().st_mtime_ns) for x in a.glob('*.json')})
    def test_g3s32_separate(self):
        r,f,p=fixture(32);build(p,f,r/'anchors');self.assertFalse((r/'anchors/g3s64').exists());self.assertIsNotNone(merge_anchors(r,p,'g3s32'))
    def test_missing_frame(self):
        r,f,p=fixture(32);p['files'].append(dict(path='absent.png',sha256='0'*64))
        with self.assertRaisesRegex(ValueError,'Missing frame'):verify_frames(p,f)
    def test_wrong_sha(self):
        r,f,p=fixture(32);(f/p['files'][0]['path']).write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError,'sha256 mismatch'):verify_frames(p,f)
    def test_traversal(self):
        with self.assertRaisesRegex(ValueError,'escapes'):path_for(temp(),dict(path='../outside'))
    def test_frame_total(self):
        r,f,p=fixture(32);self.assertEqual(verify_frames(p,f),sum((f/x['path']).stat().st_size for x in p['files']))

class Heads(unittest.TestCase):
    def test_end_to_end_exact_real_contract(self):
        for n in [32,128]:
            r,f,p=fixture(n);build(p,f,r/'anchors');g,v,raw,slots=stub(r,p);group=p['captures'][0]['group']
            result=heads(g,v,r/'out',group);self.assertEqual(result,dict(completed=1,resumed=0))
            for suffix,refdir in [('', 'heads_g3s64'),('_vcd','heads_g3s64_vcd')]:
                with np.load(r/'out'/('heads_'+group+suffix)/'scannet__fixture.npz') as z, np.load(REF/refdir/'scannet__scene0651_00.npz') as real:
                    self.assertEqual(set(z.files),set(real.files))
                    for k in real.files:self.assertEqual((z[k].shape,z[k].dtype),(real[k].shape,real[k].dtype),k)
                    self.assertEqual(str(z['layout']),'per_frame');self.assertEqual(str(z['gravity_source']),'own');self.assertEqual(float(z['scale']),2)
                    np.testing.assert_array_equal(z['anchor_frame_indices'],p['captures'][0]['anchor_indices'])
                    np.testing.assert_array_equal(z['raw_pose'][:,:3],raw[slots,:3]*2);np.testing.assert_array_equal(z['fov_hw'],raw[slots,7:]);np.testing.assert_allclose(z['depth_grid'],2)
                    np.testing.assert_array_equal(z['grid_uv'],np.linspace(0,1000,51,dtype=np.float32));np.testing.assert_allclose(z['t_grav'][:,0],-raw[slots,0]*2)
                    np.testing.assert_allclose(np.linalg.det(z['r_grav']),1);np.testing.assert_allclose(z['r_grav'][0]@np.array([0.,-1.,0.]),[0,0,1],atol=1e-12)
            rec=json.loads((r/'out/receipts'/group/'scannet__fixture.json').read_text());self.assertEqual(rec['scale_rule_outside_fitted_format'],n==32)
    def test_resume_and_corrupt_output_refusal(self):
        r,f,p=fixture(32);g,v,_,_=stub(r,p);heads(g,v,r/'out','g3s32');dest=r/'out/heads_g3s32/scannet__fixture.npz';before=dest.stat().st_mtime_ns
        self.assertEqual(heads(g,v,r/'out','g3s32')['resumed'],1);self.assertEqual(dest.stat().st_mtime_ns,before)
        dest.write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError,'corrupt'):heads(g,v,r/'out','g3s32')
    def test_resume_changed_input_refusal(self):
        r,f,p=fixture(32);g,v,_,_=stub(r,p);heads(g,v,r/'out','g3s32');(v/'scannet__fixture.npz').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'inputs changed'):heads(g,v,r/'out','g3s32')
    def test_anchor_mismatch_refusal(self):
        r,f,p=fixture(32);g,v,_,_=stub(r,p);dest=v/'scannet__fixture.npz'
        with np.load(dest) as z:values=dict(z)
        values['frame_indices']+=1;np.savez(dest,**values)
        with self.assertRaisesRegex(ValueError,'frame indices differ'):heads(g,v,r/'out','g3s32')
    def test_real_input_regression(self):
        key='scannet__scene0651_00.npz';g=REF.parent/'g3t/n64'/key;v=KIT/'fixtures/own'/key
        self.assertTrue(g.is_file());self.assertTrue(v.is_file());r=temp();(r/'g').mkdir();(r/'v').mkdir();(r/'g'/key).symlink_to(g);(r/'v'/key).symlink_to(v)
        heads(r/'g',r/'v',r/'out','g3s64')
        for folder in ['heads_g3s64','heads_g3s64_vcd']:
            with np.load(r/'out'/folder/key) as a,np.load(REF/folder/key) as b:
                for k in b.files:
                    if b[k].dtype.kind in 'US':np.testing.assert_array_equal(a[k],b[k])
                    else:np.testing.assert_allclose(a[k],b[k],rtol=1e-12,atol=1e-12,err_msg=k)

class Preflight(unittest.TestCase):
    def test_free_card(self):free_card('0',lambda cmd,**kw:'GPU-test, 0, 0\n' if '--query-gpu=uuid,memory.used,utilization.gpu' in cmd else '')
    def test_busy_card(self):
        for gpu,apps in [('GPU-test, 900, 0',''),('GPU-test, 0, 1',''),('GPU-test, 0, 0','GPU-test, 123')]:
            with self.assertRaisesRegex(ValueError,'busy'):free_card('0',lambda cmd,**kw:gpu if '--query-gpu=uuid,memory.used,utilization.gpu' in cmd else apps)
    def test_multiple_cards(self):
        with self.assertRaisesRegex(ValueError,'one card'):free_card('0,1')
    def test_disk_refusal(self):
        with self.assertRaisesRegex(ValueError,'free disk'):free_disk(temp(),usage=lambda p:SimpleNamespace(free=1))
    def test_disk_accept(self):free_disk(temp(),usage=lambda p:SimpleNamespace(free=101*1024**3))
    def test_checkpoint_missing(self):
        r=temp()
        with self.assertRaisesRegex(ValueError,'Missing checkpoint'):checkpoints(r/'bundle',r/'config',str(r/'artifact')+'@'+'0'*64,r/'g3t',r/'mdg')
    def test_bundle_shard_missing(self):
        r=temp();(r/'g').mkdir();(r/'m').mkdir()
        for n in ['config','artifact','g/config.json','g/model.safetensors','m/mdg.json','m/mdg.pt']:(r/n).write_text('{}')
        save(r/'BUNDLE.json',dict(schema='mdg-t0-bundle-v1',files={'absent.safetensors':'0'*64}))
        with self.assertRaisesRegex(ValueError,'Missing bundle checkpoint'):checkpoints(r/'BUNDLE.json',r/'config',str(r/'artifact')+'@'+sha(r/'artifact'),r/'g',r/'m')
    def test_head_node_refusal(self):
        with patch('devs1_run.socket.gethostname',return_value='trinity'):
            with self.assertRaisesRegex(ValueError,'Head node'):preflight(None,None)

class Guard(unittest.TestCase):
    def test_stall_stops_child(self):
        r=temp();start=time.monotonic()
        with self.assertRaisesRegex(RuntimeError,'STALL'):guarded([sys.executable,'-c','import time;time.sleep(5)'],r/'progress',r/'log',timeout=.15,poll=.02)
        self.assertLess(time.monotonic()-start,3)
    def test_stage_failure_no_retry(self):
        r=temp()
        with self.assertRaisesRegex(RuntimeError,'exited 7'):guarded([sys.executable,'-c','raise SystemExit(7)'],r/'p',r/'log',timeout=2,poll=.02)
    def test_progress_extends_guard(self):
        r=temp();source=r/'journal'
        code='import time\nfrom pathlib import Path\np=Path('+repr(str(source))+')\nfor i in range(8):\n p.write_text(str(i))\n time.sleep(.05)\n'
        guarded([sys.executable,'-c',code],r/'p',r/'log',[source],timeout=.2,poll=.01)
        self.assertIn('worker_progress',(r/'p').read_text())

class Integration(unittest.TestCase):
    def test_membership_with_actual_export_reader(self):
        sys.path.insert(0,str(KIT/'mdg_source'))
        from student_pilot import mdg_eval
        r,f,p=fixture(32);build(p,f,r/'anchors');a=merge_anchors(r,p,'g3s32')
        entries=mdg_eval.manifest_entries(a/'A_MANIFEST.json');groups=mdg_eval.groups_for([a/'MEMBERSHIP.json'],entries)
        self.assertEqual(list(groups.values()),[['floor']])
    def test_actual_e0_g3t_resume_with_stub_model(self):
        from contextlib import contextmanager
        from e0k import g3t_dense as E
        r,f,p=fixture(32);build(p,f,r/'anchors');a=merge_anchors(r,p,'g3s32');g,v,_,_=stub(r,p)
        with np.load(g/'scannet__fixture.npz') as z:values=dict(z)
        values.update(peak_allocated_bytes=np.array(0),peak_reserved_bytes=np.array(0))
        calls=[]
        class N:
            def __init__(self,*args):pass
            def extract(self,*args):calls.append(1);return dict(values)
        @contextmanager
        def vendor():yield SimpleNamespace(N1=N)
        weights=r/'weights';weights.mkdir();(weights/'config.json').write_text('{}');(weights/'model.safetensors').write_bytes(b'stub')
        with patch.dict(sys.modules,{'torch':SimpleNamespace(cuda=SimpleNamespace(OutOfMemoryError=MemoryError))}), patch.object(E.R,'vendor_source',vendor), patch.object(E.R,'CONFIG_SHA256',sha(weights/'config.json')), patch.object(E.R,'WEIGHTS_SHA256',sha(weights/'model.safetensors')):
            first=E.run(a/'DENSE.json',weights,'cpu',0,1,r/'actual_g3t')
            second=E.run(a/'DENSE.json',weights,'cpu',0,1,r/'actual_g3t')
        self.assertEqual(first['completed'],1);self.assertEqual(second['resumed'],1);self.assertEqual(calls,[1])
        heads(r/'actual_g3t',v,r/'out','g3s32')
    def test_pricing_reader_and_join_refusal(self):
        from devs1_pricing import tower_raw
        r,f,p=fixture(32);g,v,raw,slots=stub(r,p);heads(g,v,r/'out','g3s32');indices=[q['index'] for q in p['captures'][0]['dense']]
        D,c,K=tower_raw(r/'out','scannet','fixture','g3s32','vcd',indices,hw=(12,16))
        self.assertEqual(D.shape,(32,12,16));self.assertEqual(c.shape,(32,4,4));self.assertEqual(K.shape,(32,3,3));np.testing.assert_allclose(D,2)
        with self.assertRaisesRegex(ValueError,'anchor indices differ'):tower_raw(r/'out','scannet','fixture','g3s32','vcd',np.arange(32))
    def test_bundle_artifact_dir(self):
        r=temp();(r/'g').mkdir();(r/'m').mkdir();(r/'export').mkdir()
        for n in ['config','export/artifact.json','export/heads.pt','g/config.json','g/model.safetensors','m/mdg.json','m/mdg.pt']:(r/n).write_text('{}')
        save(r/'BUNDLE.json',dict(schema='mdg-t0-bundle-v1',artifact_dir=str(r/'export'),files={'artifact/artifact.json':sha(r/'export/artifact.json'),'artifact/heads.pt':sha(r/'export/heads.pt')}))
        result=checkpoints(r/'BUNDLE.json',r/'config',str(r/'export/artifact.json')+'@'+sha(r/'export/artifact.json'),r/'g',r/'m')
        self.assertEqual(result,r/'BUNDLE.json')

class RegistryAnchors(unittest.TestCase):
    def test_missing_anchor_refused(self):
        pins=[dict(index=i) for i in range(128)]
        with self.assertRaisesRegex(ValueError,'missing'):
            select_dense(pins,list(range(31))+[999])

    def test_duplicate_or_reordered_registry_refused(self):
        pins=[dict(index=i) for i in range(128)]
        for ids in [list(range(31))+[30],list(reversed(range(32))),list(range(31))]:
            with self.assertRaisesRegex(ValueError,'unique ordered'):select_dense(pins,ids)

    def test_uneven_grid_and_endpoint_anchors(self):
        pins=[dict(index=i*i) for i in range(133)]
        ids=[pins[i]['index'] for i in list(range(0,124,4))+[132]]
        dense,slots=select_dense(pins,ids)
        self.assertEqual(len(dense),64)
        self.assertEqual([dense[i]['index'] for i in slots],ids)
        self.assertTrue(all(b-a>=2 for a,b in zip(slots,slots[1:])))
        self.assertEqual(select_dense(pins,ids),(dense,slots))

    def test_no_interleaving_candidate_refused(self):
        with self.assertRaisesRegex(ValueError,'interleave'):
            select_dense([dict(index=i) for i in range(128)],list(range(32)))

    def test_g3s32_exact_registry(self):
        r,f,p=fixture(32);c=p['captures'][0]
        self.assertEqual(c['anchor_indices'],[x['index'] for x in c['dense']])
        self.assertEqual(c['anchor_slots'],list(range(32)))

    def test_build_refuses_changed_slots_before_reading_frames(self):
        r,f,p=fixture();p['captures'][0]['anchor_slots'][1]+=1
        with self.assertRaisesRegex(ValueError,'identity'):build(p,r/'absent',r/'anchors')

    def test_preflight_refuses_missing_containment(self):
        r,f,p=fixture();p['captures'][0]['anchor_indices'][-1]=9999
        with self.assertRaisesRegex(ValueError,'containment'):verify_frames(p,r/'absent')

    def test_all_delivered_captures_match_stored_registry(self):
        p=json.loads((KIT/'PLAN.json').read_text());reg=json.loads((KIT/'ANCHOR_REGISTRY.json').read_text())
        self.assertEqual(len(p['captures']),152)
        for c in p['captures']:
            validate_capture(c)
            self.assertEqual(c['anchor_indices'],reg[c['native']]['frame_indices'])
            for authority in reg[c['native']]['authorities']:
                self.assertEqual(c['anchor_indices'],authority['frame_indices'])
        self.assertEqual(set(p['excluded_no_anchor_registry']),{'d3/42444806','d3/42898633'})

    def test_staging_is_exact_dense_union(self):
        p=json.loads((KIT/'PLAN.json').read_text())
        expected={(x['path'],x['sha256']) for c in p['captures'] for x in c['dense']}
        self.assertEqual(expected,{(x['path'],x['sha256']) for x in p['files']})
        self.assertEqual([x['path'] for x in p['files']],(KIT/'FRAMES_TAR.txt').read_text().splitlines())
        self.assertEqual([x['sha256']+'  '+x['path'] for x in p['files']],(KIT/'FRAMES_BY_SHA.txt').read_text().splitlines())

    def test_gt_coverage_and_question_join(self):
        import gzip
        report=json.loads((KIT/'GT_COVERAGE.json').read_text())
        with gzip.open(KIT/'QIDS.jsonl.gz','rt') as f:qs=[json.loads(l) for l in f]
        cs={c['native']:c for c in report['captures']}
        self.assertEqual(len(cs),224)
        self.assertEqual({r['label'] for r in report['roots_searched']},{'T0','T1_half1','T1_half2','ARKit'})
        for c in cs.values():
            present=[g for g in c['gt_candidates'] if g['present']]
            expected=c['group'] is not None and any(g['frame_indices']==c['anchor_indices'] and g['geometry_schema_ok'] for g in present)
            self.assertEqual(c['priceable'],expected)
            if c['gt_present']:self.assertTrue(c['anchor_indices_match'])
            else:self.assertIsNotNone(c['build_gt'])
        for t,counts in report['by_question_type'].items():
            eligible=[q for q in qs if q['type']==t and cs[q['native']]['priceable']]
            self.assertEqual(counts['priceable_captures'],len({q['native'] for q in eligible}))
            self.assertEqual(counts['priceable_distinct_qids'],len({q['qid'] for q in eligible}))
        self.assertEqual(report['totals']['priceable_captures'],93)

if __name__=='__main__':unittest.main(verbosity=2)
