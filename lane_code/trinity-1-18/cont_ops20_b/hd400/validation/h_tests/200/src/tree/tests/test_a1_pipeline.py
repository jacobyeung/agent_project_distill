"""CPU contracts for division extension, opaque aliases, exact frames and range scans."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from student_pilot import a1_pipeline as a, a1_scan as scan, recording_pose as rp
from student_pilot import all_frame_bank as bank32, all_frame_readout as readout
from student_pilot.compact_label_bank import read_bank
from tests.test_recording_pose import fixture, staged_fixture, save

W=Path(__file__).resolve().parents[2]
OUT=Path(os.environ['B2_TEST_OUTPUT'])


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


class PipelineTests(unittest.TestCase):
    def directory(self):return Path(tempfile.mkdtemp(prefix='a1_',dir=OUT))

    def test_division_extends_training_only_and_closes_repeat_scans(self):
        root=self.directory();request=fixture(root)
        old=json.loads(rp.read_pin(request['authorities']['division']))
        old.update(schema='diagnostic-whole-scene-division-v1',training_only=True,
                   heldout_group_ids=['scannet/scene0400'],heldout_qids=['x'])
        inherited=save(root,'old.json',old)
        division,policy,census=a.division(request,inherited)
        self.assertEqual(census['admitted'],{'d3':2,'d1':1})
        for key in ('heldout_scenes','heldout_group_ids','heldout_qids'):
            self.assertEqual(division[key],old[key])
        self.assertEqual(policy['excluded_groups'],json.loads(rp.read_pin(request['authorities']['admission_policy']))['excluded_groups'])
        self.assertIn('d3/'+rp.token('d3','outsider'),division['train_scenes'])
        self.assertNotIn('d1/'+rp.token('d1','scene0400_00'),division['train_scenes'])
        self.assertTrue(census['heldout_unchanged'])

    def test_aliases_hide_paths_and_reject_source_changes(self):
        root=self.directory();original=root/'scannet_source.mp4';original.write_bytes(b'opaque fixture')
        p=rp.pin(original)
        doc={'recordings':[dict(dataset='scannet',scene='scene0000_00',video=p,poses={**p,'member':'x'})]}
        output,private=a.aliases(doc,root/'abc7')
        scanner=module(W/'h2/b10/rscan.py','alias_scanner').Scanner(json.loads((W/'h2/b10/wh.json').read_text()))
        for record in output['recordings']:
            self.assertEqual(record['dataset'],'d1')
            for kind in ('video','poses'):
                self.assertFalse(scanner.check(record[kind]['path'],'x','name').hits)
                path=Path(record[kind]['path']);self.assertFalse(path.is_symlink())
                self.assertEqual(rp.file_sha(path),p['sha256'])
        self.assertEqual(set(private.values()),{str(original)})
        original.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'source changed'):a.aliases(doc,root/'abc8')

    def test_frame_package_and_build_exact_row_paths(self):
        root=self.directory();request=fixture(root);request.update(variant='all_frames32',pool_size=96,rows_per_scene=4,epoch=0)
        plan=rp.make_plan(request);pp=save(root,'p.json',plan);receipt,sp=staged_fixture(root,plan,pp)
        wanted=a.used_frames(plan['scenes'][0],plan)
        count=a.package(plan,[sp],root,root/'f.tar',root/'f.json')
        self.assertEqual(count,len(wanted))
        manifest=json.loads((root/'f.json').read_text())
        with tarfile.open(root/'f.tar') as tf:
            self.assertEqual({m.name for m in tf},{f['path'][len('/data2/'):] for f in manifest})
        audit=rp.build(plan,pp,[sp],root/'rows')
        rows=(root/'rows/pose_rows.jsonl').read_text().splitlines()
        self.assertEqual(audit['rows'],4)
        a0=root/'a0.jsonl';legacy=json.loads(rows[0]);legacy['qid']='old';a0.write_text(json.dumps(legacy)+'\n')
        result=a.mixed_rows(root/'rows/pose_rows.jsonl',a0,root/'mixed.jsonl',expected_a0=1)
        self.assertEqual(result['rows'],5)
        for line in (root/'mixed.jsonl').read_text().splitlines():
            self.assertTrue(all(f['path'].startswith('/data2/k3f8/') for f in json.loads(line)['student_input']['frames']))
        with self.assertRaisesRegex(ValueError,'A0 census'):a.mixed_rows(root/'rows/pose_rows.jsonl',a0,root/'bad.jsonl',expected_a0=2)

    def test_shards_equal_single_and_refuse_gaps_duplicates_and_changed_pins(self):
        root=self.directory();path=root/'7c8190a4.sqlite'
        with sqlite3.connect(path) as c:
            c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY, a TEXT, b BLOB)')
            c.execute('CREATE TABLE tail(i INTEGER PRIMARY KEY, a TEXT) WITHOUT ROWID')
            c.executemany('INSERT INTO rows VALUES(?,?,?)',[(i,'scannet' if i%2 else 'clean'+str(i),b'scannet') for i in range(13)])
            c.executemany('INSERT INTO tail VALUES(?,?)',[(i,'scannet') for i in range(3)])
        m=module(W/'h2/b10/rscan.py','approved_scanner');words=W/'h2/b10/wh.json'
        self.check_scan_workers(path,m,words)
        single=m.scan(path,words,100000)
        reports=[scan.shard(path,words,i,4,m) for i in range(4)]
        merged=scan.merge(reports,m)
        self.assertEqual({k:v for k,v in merged.items() if k!='sharded'},single)
        for invalid in (reports[:-1],reports+[reports[0]],reports[:2]+[reports[1]]+reports[3:]):
            with self.assertRaises(ValueError):scan.merge(invalid,m)
        for field,value in [('sha256','b'*64),('start',99),('hits_truncated',True),('words_sha256','c'*64)]:
            invalid=copy.deepcopy(reports);invalid[0][field]=value
            with self.assertRaises(ValueError):scan.merge(invalid,m)

    def test_jsonl_ranges_equal_single(self):
        root=self.directory();path=root/'8a190c4f.jsonl'
        path.write_text('\n'.join([json.dumps({'path':'/abc/scannet.png','target':'scannet'}) for _ in range(7)]+['', '{invalid /scannet'])+'\n')
        m=module(W/'h2/b10/rscan.py','line_scanner');words=W/'h2/b10/wh.json'
        self.check_scan_workers(path,m,words)
        single=m.scan(path,words,100000)
        reports=[scan.shard(path,words,i,4,m) for i in range(4)]
        merged=scan.merge(reports,m)
        self.assertEqual({k:v for k,v in merged.items() if k!='sharded'},single)

    def check_scan_workers(self,path,m,words):
        # Exercise nonzero advisory counts alongside blocking hits.
        vocabulary=json.loads(words.read_bytes())
        vocabulary['advisory'].append(dict(length=7,sha256=hashlib.sha256(b'scannet').hexdigest()))
        words=path.with_suffix('.words.json');words.write_text(json.dumps(vocabulary))
        def encoded(report):return json.dumps(report,sort_keys=True).encode()
        for parts in (1,4,32):
            with patch.object(scan.os,'sched_getaffinity',return_value={0}):
                expected=[scan.shard(path,words,i,parts,m) for i in range(parts)]
            merged=scan.merge(expected,m)
            self.assertGreater(merged['advisory'],0)
            for workers in (1,2,3,7):
                with self.subTest(format=path.suffix,parts=parts,workers=workers), \
                     patch.object(scan.os,'sched_getaffinity',return_value=set(range(workers))), \
                     patch.object(scan,'ProcessPoolExecutor',wraps=scan.ProcessPoolExecutor) as pool:
                    actual=[scan.shard(path,words,i,parts,m) for i in range(parts)]
                    self.assertEqual([encoded(r) for r in actual],[encoded(r) for r in expected])
                    self.assertEqual(encoded(scan.merge(actual,m)),encoded(merged))
                    self.assertEqual([c.kwargs['max_workers'] for c in pool.call_args_list],
                                     [min(workers,r['end']-r['start']) for r in actual if r['end']>r['start']])
                    small=[scan.shard(path,words,i,parts,m,limit=1) for i in range(parts)]
                    for full,limited in zip(expected,small):
                        want={**full,'hit_list':full['hit_list'][:1],'hits_truncated':full['hits']>1}
                        self.assertEqual(encoded(limited),encoded(want))
                    if any(r['hits_truncated'] for r in small):
                        with self.assertRaises(ValueError):scan.merge(small,m)
                    else:self.assertEqual(encoded(scan.merge(small,m)),encoded(merged))
        # Change the actual input after workers finish and before the final stamp.
        original=scan.scan_ranges
        def changed(*args,**kwargs):
            original(*args,**kwargs)
            stamp=path.stat()
            os.utime(path,ns=(stamp.st_atime_ns,stamp.st_mtime_ns+1_000_000))
        with patch.object(scan.os,'sched_getaffinity',return_value={0,1,2}), \
             patch.object(scan,'scan_ranges',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'Input changed'):scan.shard(path,words,0,1,m)

    def test_real_pinned_bank_and_census(self):
        root=W/'h3/b14c';report=json.loads((root/'bank_validation.json').read_text())
        self.assertEqual(rp.pin(root/'heldout32.npz'),report['bank'])
        bank=bank32.read_bank(root/'heldout32.npz');old=read_bank(W/'aws_run1/kit/in/689136d4.npz')
        bank32.compare_even(bank,old)
        self.assertEqual(int(bank['camera_mask'].sum()),928)
        self.assertEqual(int(bank['camera_mask'][:,1::2].sum()),608)
        self.assertTrue(np.all(bank['camera'][bank['dataset_tokens']=='d1',0::2]==0))
        bad=copy.deepcopy(bank);bad['camera_mask'][0,0]=not bad['camera_mask'][0,0]
        with self.assertRaises(ValueError):bank32.validate_bank(bad)
        census=json.loads((root/'census.json').read_text())
        self.assertEqual(census['planned'],{'d1':14,'d2':662,'d3':2864})
        self.assertEqual(census['rows'],283200);self.assertEqual(census['mixed_rows'],321152)
        self.assertEqual(census['exact_frames'],339678);self.assertEqual(census['unused_pool_slots'],0)
        self.assertEqual(len(census['deferred']),4)
        for d in census['deferred']:self.assertEqual(d['dataset'],'d3')

    def test_masked_bank_readout_counts(self):
        bank=bank32.read_bank(W/'h3/b14c/heldout32.npz');records=[]
        # Both datasets; avoid a costly full cohort pairwise test.
        for dataset in ('d1','d2'):
            i=list(bank['dataset_tokens']).index(dataset)
            gt=dict(camera=bank['camera'][i],camera_mask=bank['camera_mask'][i],gravity=bank['gravity'][i])
            records.append(dict(dataset=dataset,gt=gt,pred=dict(camera=bank['camera'][i],gravity=bank['gravity'][i])))
        result=readout.pose_metrics(records,range(32))
        self.assertEqual(result['all']['rot_deg']['n'],48)
        self.assertEqual(result['d1']['rot_deg']['n'],16)
        self.assertEqual(result['d2']['rot_deg']['n'],32)
        self.assertEqual(result['all']['centre_err_m']['median'],0.)

    def test_concurrent_png_publication_has_complete_bytes(self):
        from concurrent.futures import ThreadPoolExecutor
        root=self.directory();raw=b'fixture complete bytes'*100;digest=rp.digest(raw)
        path=root/(digest+'.png')
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda _:rp.store_png(path,raw,digest),range(8)))
        self.assertEqual(path.read_bytes(),raw)
        self.assertEqual(rp.file_sha(path),digest)
        # Retained publication files share final bytes and never become tar members.
        for retained in root.glob('*.part'):self.assertEqual(retained.read_bytes(),raw)
        with self.assertRaisesRegex(ValueError,'corrupt'):rp.store_png(path,b'changed',rp.digest(b'changed'))

    def test_codec_roundtrip(self):
        value={'authorities':{'vsi288':{'path':'/abc'},'vsti':{'scenes':[]}},'reasons':['vsti']}
        self.assertNotIn('vsti',json.dumps(a.codec(value)))
        self.assertEqual(a.codec(a.codec(value),True),value)


if __name__=='__main__':unittest.main()
