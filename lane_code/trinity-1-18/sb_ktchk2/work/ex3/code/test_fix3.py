"""CPU fixtures for every sb_ktchk plant and the GPU admission shell."""
import os
import subprocess
import unittest
import uuid
from unittest.mock import patch
from common import ROOT, Path, json, sha, read_json, write_json, digest
import process_guard as G

PROBES = {}

def fresh(name):
    root = ROOT/'runtime'/('fix3_'+name+'_'+uuid.uuid4().hex)
    root.mkdir(parents=True)
    return root

def tree(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}

class Fix3Tests(unittest.TestCase):
    def plant(self, name, part, rel, value):
        root = fresh(name)
        G.freeze(root, part)
        path = root/rel
        path.parent.mkdir(parents=True, exist_ok=True)
        write_json(path, value)
        before = tree(root)
        call = {'A':'E.run_a()', 'B':'E.run_b()', 'C':'E.run_c()', 'H':'E.heldout_once()'}[part]
        script = "import sys;sys.path.insert(0,'code');from pathlib import Path;import evaluate_v2 as E,evaluate as V,camera_pricing as C;E.OUT=V.OUT=C.OUT=Path(sys.argv[1]);"+call
        result = subprocess.run([os.sys.executable, '-B', '-c', script, str(root)], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('REFUSE:', result.stderr)
        self.assertEqual(tree(root), before)
        PROBES[name] = dict(status='REFUSED', returncode=result.returncode, unchanged=True, input_sha256={str(path):sha(path)})

    def test_plant_A_report(self):
        self.plant('A_report','A','A_DISTANCE.txt',dict(rows=[dict(score=99)]))

    def test_plant_A_subdir_bars(self):
        self.plant('A_subdir_bars','A','parts/A/old/BARS.json',dict(score=99))

    def test_plant_A_control_per_item(self):
        self.plant('A_control_per_item','A','parts/A/PER_ITEM_A_train.jsonl',dict(score=99))

    def test_plant_B_report(self):
        self.plant('B_report','B','B_LADDER_TRAIN.txt',dict(rows=[dict(score=99)]))

    def test_plant_C_report(self):
        self.plant('C_report','C','C_CAMERA.txt',dict(rows=[dict(score=99)]))

    def test_plant_H_report(self):
        self.plant('H_report','H','HELDOUT_once.txt',dict(results=dict(A=dict(rows=[dict(score=99)]))))

    def test_plant_H_control_legacy(self):
        self.plant('H_control_legacy','H','PER_ITEM_A_heldout.jsonl',dict(score=99))

    def test_plant_B_reads_planted_A_DISTANCE(self):
        import evaluate_v2 as E
        import evaluate as V
        from exclusions import population
        rows=[dict(row_id=i,room=r,split='train',arm=E.arm(32,32,'today'),score=50.)
              for i,r in population()['row_rooms'].items()]
        for score in (40.,60.):
            root=fresh('a_report_mismatch')
            G.freeze(root,'A');G.freeze(root,'B')
            with patch.object(V,'OUT',root):V.items_file(rows,'A','train')
            write_json(root/'A_DISTANCE.txt',dict(rows=[dict(r,score=score) for r in rows]))
            before=tree(root)
            with patch.object(E,'OUT',root),patch.object(E,'labels',return_value={}),patch.object(E,'captures',return_value=[]),patch.object(E,'row_ids',return_value={'absent'}):
                with self.assertRaisesRegex(RuntimeError,'REFUSE: A_DISTANCE.txt'):E.run_b()
            self.assertEqual(tree(root),before)
        PROBES['B_reads_planted_A_DISTANCE']=dict(status='REFUSED',unchanged=True)

    def test_plant_A_planted_FREEZE_after_code_edit(self):
        for part in 'ABCH':
            root=fresh('forged_freeze');G.freeze(root,part)
            bars=G.directory(root,part)/'BARS.json'
            receipt=G.directory(root,part)/'FREEZE.json'
            self.assertEqual(read_json(bars)['code_sha256'],read_json(receipt)['code_sha256'])
            with patch.object(G,'code_pins',return_value={'metrics.py':'fixture changed code'}):
                with self.assertRaisesRegex(RuntimeError,'REFUSE: code differs'):G.require_score(root,part)
                data=read_json(receipt);data['code_sha256']=digest(G.code_pins());write_json(receipt,data)
                before=tree(root)
                with self.assertRaisesRegex(RuntimeError,'REFUSE: code differs from BARS.json'):G.require_score(root,part)
                self.assertEqual(tree(root),before)
        PROBES['A_planted_FREEZE_after_code_edit']=dict(status='REFUSED',unchanged=True)

    def test_duplicate_row_arm_refuses(self):
        from evaluate_v2 import gains_once,arm
        from exclusions import population
        rows=[]
        for i,r in population()['row_rooms'].items():
            rows += [dict(row_id=i,room=r,split='train',arm=arm(32,32,'today'),score=1.),
                     dict(row_id=i,room=r,split='train',arm=arm(64,64,'today'),score=0.)]
        self.assertEqual(gains_once(rows)['gains']['added_frame_gain']['point'],-1.)
        with self.assertRaisesRegex(RuntimeError,'REFUSE: duplicate'):gains_once(rows+[dict(rows[-1],score=100.)])
        PROBES['duplicate_rows_appended']=dict(status='REFUSED')

    def test_report_guard_pose_and_nested_receipt(self):
        self.plant('A_pose','A','A_POSE.json',dict(rows=[dict(score=99)]))
        self.plant('A_nested_freeze','A','parts/A/old/FREEZE.json',dict(score=99))

    def test_a_rows_provenance_and_missing_receipt(self):
        import evaluate as V
        import evaluate_v2 as E
        root=fresh('a_rows');G.freeze(root,'A')
        rows=[dict(row_id='fixture',arm='C32_V32_today',score=1.)]
        with patch.object(E,'OUT',root):
            with self.assertRaisesRegex(FileNotFoundError,'MISSING .*PER_ITEM_A_train.jsonl'):E.a_train_rows()
            with patch.object(V,'OUT',root):V.items_file(rows,'A','train')
            write_json(root/'A_DISTANCE.txt',dict(rows=rows))
            self.assertEqual(E.a_train_rows(),rows)

    def test_a_freezes_h_before_preflight(self):
        import runner
        root=fresh('early_h')
        def preflight(part):
            G.require_score(root,'A');G.require_score(root,'H')
            raise PermissionError('fixture stops before GPU')
        with patch.object(runner,'OUT',root),patch.object(runner,'preflight',side_effect=preflight),patch.object(os.sys,'argv',['runner.py','A']):
            with self.assertRaisesRegex(PermissionError,'fixture stops'):runner.main()

    def test_per_item_written_before_reports(self):
        import evaluate_v2 as E
        import evaluate as V
        for part in 'AB':
            root=fresh('order_'+part);G.freeze(root,part)
            if part=='B':
                G.freeze(root,'A')
                with patch.object(V,'OUT',root):V.items_file([],'A','train')
                write_json(root/'A_DISTANCE.txt',dict(rows=[]))
            def emit(*args,**kwargs):
                self.assertTrue((G.directory(root,part)/f'PER_ITEM_{part}_train.jsonl').is_file())
                raise RuntimeError('fixture report interrupted')
            with patch.object(E,'OUT',root),patch.object(V,'OUT',root),patch.object(E,'labels',return_value={}),patch.object(E,'captures',return_value=[]),patch.object(E,'row_ids',return_value={'absent'}),patch.object(E,'emit',side_effect=emit):
                with self.assertRaisesRegex(RuntimeError,'fixture report interrupted'):{'A':E.run_a,'B':E.run_b}[part]()
            with self.assertRaisesRegex(RuntimeError,'REFUSE: per-item'):G.require_score(root,part)

    def test_camera_and_heldout_item_order(self):
        import evaluate as V
        import evaluate_v2 as E
        import camera_pricing as C
        root=fresh('camera_order');G.freeze(root,'C')
        def camera_write(path,value):
            self.assertTrue((G.directory(root,'C')/'PER_ITEM_C_devs1.jsonl').is_file())
            raise RuntimeError('fixture report interrupted')
        with patch.object(C,'OUT',root),patch.object(V,'OUT',root),patch.object(C,'records',return_value=[]),patch.object(C,'frame_binding',return_value={'status':'PASS'}),patch.object(C,'camera_items',return_value={'items':[]}),patch.object(C,'parity_check',return_value=({'status':'PASS'},{})),patch.object(C,'write_json',side_effect=camera_write):
            with self.assertRaisesRegex(RuntimeError,'fixture report interrupted'):C.run()
        with self.assertRaisesRegex(RuntimeError,'REFUSE: per-item'):G.require_score(root,'C')
        root=fresh('heldout_order');G.freeze(root,'H')
        original=Path.is_file
        def exists(path):
            return True if str(path)=='/scratch/jjyeung/orch_n30/sb_kbox2/heldout_labels.json' else original(path)
        def heldout_write(path,value):
            self.assertTrue((G.directory(root,'H')/'PER_ITEM_H_heldout.jsonl').is_file())
            raise RuntimeError('fixture report interrupted')
        with patch.object(E,'OUT',root),patch.object(V,'OUT',root),patch.object(Path,'is_file',exists),patch.object(E,'consume_heldout'),patch.object(E,'run_a',return_value={'rows':[],'complete':True}),patch.object(E,'run_b',return_value={'rows':[],'complete':True}),patch.object(E,'write_json',side_effect=heldout_write),patch.object(E,'_HELDOUT_ACTIVE',False):
            with self.assertRaisesRegex(RuntimeError,'fixture report interrupted'):E.heldout_once()
        with self.assertRaisesRegex(RuntimeError,'REFUSE: per-item'):G.require_score(root,'H')

    def test_b_uses_a_baselines_without_overlapping_c64(self):
        import evaluate as V
        import evaluate_v2 as E
        import numpy as np
        from contextlib import ExitStack
        root=fresh('b_arms');G.freeze(root,'A');G.freeze(root,'B')
        # A and B both measure C64/V32, while gains need A's C32 baseline only.
        a_rows=[dict(row_id='fixture',room='fixture',split='train',arm=E.arm(c,32,'today'),score=10.) for c in (32,64)]
        with patch.object(V,'OUT',root):V.items_file(a_rows,'A','train')
        write_json(root/'A_DISTANCE.txt',dict(rows=a_rows))
        (root/'tower.npz').write_bytes(b'fixture');write_json(root/'candidates.json',{})
        c=dict(canonical='fixture',anchor_slots=[0],gt={'path':str(root/'gt.npz')})
        tower=dict(depth_grid=np.ones((1,1,1)))
        observed=[]
        def gain(rows):
            keys=[(r['row_id'],r['arm']) for r in rows]
            self.assertEqual(len(keys),len(set(keys)))
            observed.extend(keys)
            return {'status':'MISSING'}
        mocks=dict(OUT=root,labels=lambda split:{},captures=lambda split:[c],row_ids=lambda split:{'absent'},
                   capdir=lambda *args:root,npz=lambda p:tower,stored_tower=lambda c:tower,geometry=lambda *args:({},1.),
                   read_json=lambda p:{},price=lambda *args:[dict(row_id='fixture',room='fixture',split='train',score=10.)],
                   scored=lambda rows,name,labels:[dict(r,arm=name) for r in rows],winning_box=lambda *args:None,
                   flagged_row=lambda row,dense:row,selector_diagnostics=lambda *args:{},diagnostics=lambda rows:{},gains_once=gain)
        with ExitStack() as stack:
            for name,value in mocks.items():stack.enter_context(patch.object(E,name,value))
            stack.enter_context(patch.object(V,'OUT',root))
            # The authoritative reader uses read_json; use its real implementation here.
            stack.enter_context(patch.object(E,'a_train_rows',return_value=a_rows))
            E.run_b()
        self.assertEqual({arm for _,arm in observed},{E.arm(32,32,'today'),E.arm(64,32,'today'),E.arm(64,64,'today'),'C64_V64_today_flagged'})

    def gpu_fixture(self, memory=(0,1024), apps=('',''), bad_query=False):
        root=fresh('gpu')
        # Fake commands are confined to explicit fixture mode, which cannot launch a runner.
        smi='''#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
printf '%s\\n' "$*" >> calls.txt
printf '%s|%s\\n' "$CUDA_DEVICE_ORDER" "$CUDA_CACHE_PATH" >> env.txt
[[ "$1" == -i && "$2" == GPU-fixture ]] || exit 7
if [[ "$3" == --query-gpu=memory.used,utilization.gpu ]]; then
 n=0; if [[ -f count ]]; then read -r n < count; fi
 n=$((n+1)); echo "$n" > count
 sed -n "${n}p" memory.txt
else
 read -r n < count
 sed -n "${n}p" apps.txt
fi
'''
        (root/'nvidia-smi').write_text(smi if not bad_query else '#!/bin/bash\nexit 9\n')
        (root/'sleep').write_text('#!/bin/bash\nprintf "%s\\n" "$*" >> "$(dirname "$0")/wait.txt"\n')
        for name in ('nvidia-smi','sleep'):(root/name).chmod(0o755)
        (root/'memory.txt').write_text(''.join(f'{m}, 99\n' for m in memory))
        (root/'apps.txt').write_text('\n'.join(apps)+'\n')
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='GPU-fixture')
        result=subprocess.run(['bash','scripts/gpu_environment.sh','A','--test-fixture',str(root)],cwd=ROOT,env=env,capture_output=True,text=True)
        return result,root

    def test_gpu_idle_two_readings_and_environment(self):
        result,root=self.gpu_fixture()
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((root/'wait.txt').read_text(),'300\n')
        self.assertEqual(len((root/'calls.txt').read_text().splitlines()),4)
        self.assertEqual(set((root/'env.txt').read_text().splitlines()),{'PCI_BUS_ID|'+str(ROOT/'runtime/nv')})
        log=(root/'out/tower_frames/NVIDIA_SMI_A.log').read_text()
        self.assertIn('Reading 1 UTC',log);self.assertIn('Reading 2 UTC',log)
        self.assertEqual(log.count('compute-apps pid'),2)
        self.assertFalse((root/'captures').exists())
        # Logs append, including on repeated fixture invocations.
        result=subprocess.run(['bash','scripts/gpu_environment.sh','A','--test-fixture',str(root)],cwd=ROOT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='GPU-fixture'),capture_output=True,text=True)
        self.assertTrue((root/'out/tower_frames/NVIDIA_SMI_A.log').read_text().startswith(log))

    def test_gpu_memory_refuses_either_reading(self):
        for memory in ((1025,0),(0,1025)):
            result,root=self.gpu_fixture(memory=memory)
            self.assertNotEqual(result.returncode,0);self.assertIn('REFUSE:',result.stderr)
            self.assertEqual((root/'wait.txt').read_text(),'300\n')
            self.assertEqual(len((root/'calls.txt').read_text().splitlines()),4)

    def test_gpu_compute_process_refuses_either_reading(self):
        for apps in (('123',''),('','456')):
            result,root=self.gpu_fixture(apps=apps)
            self.assertNotEqual(result.returncode,0);self.assertIn('REFUSE:',result.stderr)
            self.assertEqual((root/'wait.txt').read_text(),'300\n')
            self.assertEqual(len((root/'calls.txt').read_text().splitlines()),4)

    def test_gpu_query_errors_and_invalid_values_refuse(self):
        for kw in (dict(bad_query=True),dict(memory=('N/A',0)),dict(memory=('0\n0',0))):
            result,_=self.gpu_fixture(**kw)
            self.assertNotEqual(result.returncode,0);self.assertIn('REFUSE:',result.stderr)
