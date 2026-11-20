"""Round-three regression, receipt, paired-score, package, and worker tests."""
import contextlib
import copy
import gzip
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import build
ROOT=build.ROOT
sys.path.insert(0,str(ROOT))
from gpkg.score_ceiling import score,run_receipt
from gpkg.runtime.c import Writer
from gpkg.dense_build import rebuild_legacy


def temp():return Path(tempfile.mkdtemp(prefix='r3_',dir=ROOT/'work/tests'))
def receipt(path):return dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size)
def refs():return json.loads((ROOT/'kit2/kit/rerun2/items544.json').read_text())['items']
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))


def bound(ref):
    anchors=ref['source_indices'];n=ref['mapping']['dense_count']
    # Synthetic native indices keep the real anchors and add one unused index
    # per interval, with an extra final frame. Never used as real RGB evidence.
    indices=anchors if n==32 else sorted(anchors+[a+1 for a in anchors])
    if len(set(indices))!=n:raise ValueError('synthetic dense fixture collided')
    return dict(frames=dict(native_frames=[None]*n,dense_indices=indices,
                           anchor_indices=anchors,anchor_slots=[indices.index(a) for a in anchors]))


class Round3Tests(unittest.TestCase):
    def test_sparse100_and_authenticated_kill_receipt(self):
        root=temp();path=root/'capture.gz';rows=refs();writer=Writer(path)
        for ref in rows:
            writer.append(dict(schema='ground-capture-v1',item_id=ref['item_id'],capture=ref['capture'],
                               source_indices=ref['source_indices'],pass_index=0,arm='points',calls=ref['calls'],objects=[]))
        writer.close();fallback=root/'fallback.json'
        write(fallback,dict(trusted=False,items=0,expected=150,failure='worker did not finish its receipt'))
        cut=root/'cut.gz';cut.write_bytes(path.read_bytes()[:-8])
        result=score(ROOT/'kit2/kit/rerun2/items544.json',cut,receipt(cut),point_run_receipt=fallback)
        self.assertEqual(result['sparse_denominator'],93);self.assertEqual(result['sparse_lt3_denominator'],100)
        self.assertEqual(result['sparse_lt3_manifest_items'],100)
        self.assertEqual(result['statistics']['groups']['sparse_lt3']['items'],100)
        extra=[r for r in result['rows'] if r['sparse_lt3'] and not r['sparse93']]
        self.assertEqual(len(extra),7)
        for row in extra:self.assertEqual(set(row['sparse_lt3_visibility']),set(row['null_ground_names']))
        self.assertTrue(result['capture_read']['points']['salvaged'])
        self.assertEqual(result['run_receipt']['receipt_status'],'incomplete')
        self.assertFalse(result['complete_paired_population'])
        with self.assertRaisesRegex(ValueError,'SHA256'):
            score(ROOT/'kit2/kit/rerun2/items544.json',cut,dict(sha256='0'*64),point_run_receipt=fallback)
        for change in (dict(capture_sha256='0'*64),dict(mode='dense64'),dict(failure='unrecognized')):
            write(fallback,dict(trusted=False,items=0,failure='worker did not finish its receipt',**{k:v for k,v in change.items() if k!='failure'}))
            if 'failure' in change:write(fallback,dict(trusted=False,**change))
            with self.assertRaises(ValueError):run_receipt(fallback,result['capture_read']['points'],'points')
        write(ROOT/'out3/SYNTHETIC_SPARSE_SCORE.json',result)

    def test_dense_primary_scoring_and_frame_identity(self):
        from gpkg.dense_runtime.d import binding_record
        root=temp();path=root/'dense.gz';rows=refs();records=[]
        for pass_id,selected in ((0,rows),(1,[r for r in rows if r['calls']][:10])):
            for ref in selected:
                records.append(dict(schema='ground-capture-v1',item_id=ref['item_id'],capture=ref['capture'],
                                    source_indices=ref['source_indices'],pass_index=pass_id,
                                    arm='dense64' if pass_id==0 else 'dense64_noise',calls=ref['calls'],objects=[],
                                    **binding_record(bound(ref),ref)))
        path.write_bytes(gzip.compress(('\n'.join(map(json.dumps,records))+'\n').encode()))
        t1=root/'t1.gz';writer=Writer(t1)
        for row in records[:150]:
            value={k:v for k,v in row.items() if k not in ('arm',)};writer.append(value)
        writer.close()
        result=score(ROOT/'kit2/kit/rerun2/items544.json',path,receipt(path),t1,receipt(t1),mode='dense64')
        self.assertTrue(result['complete_paired_population']);self.assertEqual(len(result['arm_noise']),10)
        groups=result['statistics']['groups']
        self.assertEqual(groups['dense64_primary']['items'],104);self.assertEqual(groups['unchanged32']['items'],46)
        for name,group in groups.items():
            if not group['items']:continue
            for metric in ('dense64_minus_baseline','dense64_minus_T1'):
                self.assertEqual(group['metrics'][metric]['ci95'],[0.,0.])
        self.assertEqual(result['statistics']['resampled_rooms'],46)
        self.assertEqual(result['statistics']['seed'],20261120)
        self.assertEqual(result['statistics']['draws'],10000)
        self.assertTrue(all(r['difference']==0 for r in result['arm_noise']))
        write(ROOT/'out3/SYNTHETIC_DENSE_SCORE.json',result)
        records[0]['ground_source_indices'][0]+=1
        bad=root/'bad.gz';bad.write_bytes(gzip.compress((json.dumps(records[0])+'\n').encode()))
        with self.assertRaisesRegex(ValueError,'binding'):
            score(ROOT/'kit2/kit/rerun2/items544.json',bad,receipt(bad),mode='dense64')

    def test_old_deliveries_identical_and_dense_seals(self):
        root=temp();legacy=rebuild_legacy(root/'legacy',ROOT)
        self.assertEqual(legacy['delivery_sha256'],'f4509a4ad19b8e2bd2f9f5fd3fe7c32130ab13c10db5aa00407a84582fdb8d00')
        points=build.build(root/'points',points='/scratch/jjyeung/orch_n30/nvkey1/work/c0/POINTS_gpt-6.2-astra.json')
        self.assertEqual(points['delivery_sha256'],'0d547179098249f9d4e34e87b99ab015d69fbed6fb5904852d8d5232be19cc58')
        fixed=build.build(root/'fixed')
        self.assertEqual(fixed['delivery_sha256'],'ef9575f1eb53d4b603592d6cd94e0bdd07e0a83e69c720c97b4191dadbe4542e')
        info=build.build(root/'dense',dense=True)
        self.assertNotIn(info['token'],[legacy['token'],points['token'],fixed['token']])
        outer={m.name:v for m,v in build.read_tar((root/'dense/delivery.tgz').read_bytes())}
        pf={m.name:v for m,v in build.read_tar(outer['0.tgz'])}
        parent={m.name:v for m,v in build.read_tar((ROOT/'parent/0.tgz').read_bytes())}
        for name,raw in parent.items():
            if name.startswith(('tree/','b/','h1eval/','items/')):self.assertEqual(pf[name],raw,name)
        plan=json.loads(pf['9.json'])
        for name,pin in plan['payload_pins'].items():self.assertEqual(pin['sha256'],build.sha(pf[name]))
        for name,pin in json.loads(pf['g/8.json']).items():self.assertEqual(pin,build.sha(pf[name]))
        for name,pin in json.loads(outer['PACKAGE.json'])['files'].items():self.assertEqual(pin,build.sha(outer[name]))
        bundle={m.name:v for m,v in build.read_tar(build.bundle_of(outer['BATCH.sh'])[1])}
        self.assertEqual(bundle['0.json'],outer['0.json']);self.assertEqual(bundle['7.py'],outer['a/6.py'])
        self.assertIn(b'from g.dw import run',pf['orchard_h10/entry.py'])
        self.assertEqual(outer['a/1.json'],(ROOT/'parent/a/1.json').read_bytes())
        self.assertEqual(outer['a/export.json'],(ROOT/'parent/a/export.json').read_bytes())
        from import_smoke import smoke
        result=smoke(root/'dense/delivery.tgz');self.assertEqual(result['returncode'],0,result)
        # Exercise installation from the delivered g/, under the actual entry paths.
        p=Path(result['extraction'])/'p'
        child=subprocess.run([sys.executable,'-B','-I','-c',
             "import sys;from pathlib import Path;p=Path(sys.argv[1]);sys.path[:0]=[str(p/'b'),str(p/'tree'),str(p)];from g.w import bind_reader_root;bind_reader_root();from g import dw,d;\nwith d.installed(): print('dense install passed')",str(p)],
             capture_output=True,text=True,timeout=60)
        self.assertEqual(child.returncode,0,child.stderr)
        write(ROOT/'out3/REBUILD_AND_IMPORT.json',dict(legacy=legacy,points=points['delivery_sha256'],fixed=fixed['delivery_sha256'],dense=info['delivery_sha256'],imports=result,dense_install=child.stdout))

    def test_production_producers_in_isolated_cpu_process(self):
        result=subprocess.run([sys.executable,'-B',str(ROOT/'gpkg/dense_checks.py')],
                              capture_output=True,text=True,timeout=180)
        (ROOT/'out3/PRODUCERS_FINAL.txt').write_text(result.stdout+result.stderr)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_worker_fresh_repeats_and_partial_first_item_record(self):
        pkg=types.ModuleType('dense_worker_test');pkg.__path__=[str(ROOT/'gpkg/dense_runtime'),str(ROOT/'gpkg/runtime')]
        sys.modules[pkg.__name__]=pkg;dw=importlib.import_module(pkg.__name__+'.dw')
        rows=refs()
        def mod(name,**kw):m=types.ModuleType(name);m.__dict__.update(kw);return m
        for limit in (None,-1):
            root=temp();settings=dict(stage1_select_rule='candidates_argmax',perception_memo='verify',perception_memo_modules=['g3t'],
                save_own_depth=False,export_dir='e',artifact_manifest='b',frames_json='0',dense_manifest='1')
            memo=types.SimpleNamespace(modules=frozenset(['g3t']));gen=types.SimpleNamespace(perception=types.SimpleNamespace(memo=memo))
            factory=types.SimpleNamespace(generator=gen,load_info=dict(export=dict(step=544)))
            caps={r['task']['native']:dict(pin=r['mapping']['frame_binding_sha256']) for r in rows}
            dense={r['task']['native']:dict(frames=[None]*r['mapping']['dense_count']) for r in rows}
            byid={r['task']['id']:r for r in rows}
            parity=mod('e2e_reader.parity',FRAMES='0',DENSE='1',_captures=lambda x:caps if x=='0' else dense,
                       bind_item=lambda task,settings:bound(byid[task['id']]))
            adapter=mod('h1eval.h10.parity_adapter',settings_for=lambda *a:settings,prepare_runtime=lambda *a:None,
                        artifact_spec=lambda *a:{},make_capped_real=lambda *a,**k:factory)
            cuda=types.SimpleNamespace(synchronize=lambda:None,reset_peak_memory_stats=lambda:None,
                   max_memory_allocated=lambda:11,max_memory_reserved=lambda:22,mem_get_info=lambda:(100,200),
                   get_device_properties=lambda index:types.SimpleNamespace(name='NVIDIA H100 80GB HBM3'))
            modules={'orchard_h10':mod('orchard_h10'),'orchard_h10.common':mod('orchard_h10.common',write=write),
                     'h1eval':mod('h1eval'),'h1eval.h10':mod('h1eval.h10'),'h1eval.h10.parity_adapter':adapter,
                     'h1eval.items':mod('h1eval.items',digest=lambda v:v['anchors']['pin'] if 'anchors' in v else build.canonical(v)),
                     'e2e_reader':mod('e2e_reader',parity=parity),'e2e_reader.parity':parity,'torch':mod('torch',cuda=cuda)}
            seen=[]
            def replay(g,b,ref):
                self.assertEqual(memo.modules,frozenset() if len(seen)>=150 else frozenset(['g3t']))
                seen.append(ref['item_id'])
                return dict(schema='ground-capture-v1',item_id=ref['item_id'],capture=ref['capture'],source_indices=ref['source_indices'],
                            calls=ref['calls'],objects=[],geometry=None,timings=dict(g3t_s=1.))
            cfg=dict(output=str(root/'r'),stop_file=str(root/'r/metadata/STOP'),settings='0')
            if limit is not None:cfg['first_item_max_seconds']=limit
            with patch.dict(sys.modules,modules),patch.object(dw.d,'installed',lambda:contextlib.nullcontext({})),\
                 patch.object(dw.w,'bind_reader_root'),patch.object(dw.w,'assert_reader_root'),\
                 patch.object(dw.w,'load_rows',return_value=rows),patch.object(dw.w,'replay',side_effect=replay):
                result=dw.run(cfg,1000,clock=lambda:0)
            self.assertEqual(len(seen),160 if limit is None else 1)
            self.assertEqual(result['complete'],limit is None)
            self.assertTrue((root/'r/metadata/8_64.json').is_file())
            run=json.loads((root/'r/metadata/PARITY.json').read_text())
            self.assertEqual(run['mode'],'dense64');self.assertFalse(run['parity_gate_applies'])
            if limit is None:self.assertEqual(len(run['arm_noise']),10)


if __name__=='__main__':unittest.main()
