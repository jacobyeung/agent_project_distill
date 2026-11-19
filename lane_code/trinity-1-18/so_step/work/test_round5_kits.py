"""Fifth-review regressions, runnable against SO_KIT_BUNDLE before or after fixes."""
import ast
import copy
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = Path(os.environ.get('SO_KIT_BUNDLE', ROOT/'out'))
TREE = ROOT/'work/b21_final/work/tree_r1'
ENV = Path('/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages')
os.environ.update(CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='8',
    MKL_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8', TOKENIZERS_PARALLELISM='false',
    LANE_TEST_OUTPUT=str(ROOT/'work/test_runs'), TMPDIR=str(ROOT/'work/test_runs'))
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:8])
sys.path[:0] = [str(BUNDLE/'kit_timing'), str(BUNDLE/'kit_profile'), str(TREE), str(ROOT/'work')]
import torch
torch.set_num_threads(8)
from student_pilot import carrier_c1_run as run
from tests.so_helpers import root, reset_switches
import test_round4_kits as previous_tests


class Round5Kits(unittest.TestCase):
    def setUp(self):
        reset_switches(self)

    def test_processor_limit_accepts_real_16_9_and_square_sources(self):
        from audit import Coverage
        trainer = ast.parse((TREE/'student_pilot/batches.py').read_text())
        size = next(k.value for n in ast.walk(trainer) if isinstance(n, ast.Call)
                    for k in n.keywords if k.arg == 'size' and isinstance(k.value, ast.Dict))
        limits = eval(compile(ast.Expression(size), '<trainer-size>', 'eval'), {'__builtins__': {}})
        source = ENV/'transformers/models/qwen3_vl/video_processing_qwen3_vl.py'
        parsed = ast.parse(source.read_text())
        function = next(n for n in parsed.body if isinstance(n, ast.FunctionDef) and n.name == 'smart_resize')
        namespace = {'math': math}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
        self.assertEqual(limits['longest_edge'] // (32 * 16**2), 576)
        for height,width,expected in [(1080,1920,[32,18,32]), (1920,1080,[32,32,18]),
                                      (512,512,[32,24,24]), (480,480,[32,24,24])]:
            with self.subTest(source=(height,width)):
                h,w = namespace['smart_resize'](32,height,width,temporal_factor=2,factor=32,
                    min_pixels=limits['shortest_edge'],max_pixels=limits['longest_edge'])
                self.assertEqual([32,h//16,w//16], expected)
                Coverage().observe({'video_grid_thw':torch.tensor([expected])})
        print('PROCESSOR_LIMIT: longest_edge=4718592; spatial_patches=576; sources=16:9,9:16,square')

    def test_grid_above_processor_limit_refuses(self):
        from audit import Coverage
        for grid in ([32,20,30], [32,30,20], [33,24,24], [32,0,24]):
            with self.subTest(grid=grid), self.assertRaisesRegex(ValueError, 'grid cap'):
                Coverage().observe({'video_grid_thw':torch.tensor([grid])})

    def test_replay_pools_all_four_ranks(self):
        from replay_compare import compare, loss_acceptance
        for target in range(4):
            with self.subTest(target_rank=target):
                directory,audits = previous_tests.Round4Kits().replay_fixture()
                for rank in range(4):
                    values = (0.,1.,.5) if rank == (target+1)%4 else (0.,.1,.3 if rank == target else .1)
                    for arm,value in zip(('off1','off2','on'), values):
                        path=directory/arm/f'rank{rank}'/'steps.json'
                        record=json.loads(path.read_text())[0]
                        record.update(components={'x':value},stream_means={'vqa':value},first_step_micro_losses=[value])
                        path.write_text(json.dumps([record]))
                self.assertFalse(loss_acceptance([0.],[.1],[.3])['accepted'])
                result=compare(directory,audits)
                self.assertTrue(result['accepted'])
                self.assertEqual(result['pooled']['off_max_abs'],1.)
                self.assertEqual(result['pooled']['threshold'],2.)
                self.assertFalse(result['ranks'][target]['accepted'])  # Diagnostic, not a veto.

    def test_all_ranks_outside_local_bounds_cannot_pass_pooled_max(self):
        from replay_compare import pooled_loss_acceptance
        def records(values):
            return [dict(components={'x':v},stream_means={'vqa':v},first_step_micro_losses=[v]) for v in values]
        self.assertFalse(pooled_loss_acceptance(records([0.]*4),records([1.,2.,3.,4.]),
            records([2.1,4.1,6.1,8.1]))['accepted'])

    def test_pooled_strict_branch_nonfinite_and_schema_controls(self):
        from replay_compare import pooled_loss_acceptance
        records=[dict(components={'x':0.},stream_means={'vqa':1.},first_step_micro_losses=[1.]) for _ in range(4)]
        self.assertTrue(pooled_loss_acceptance(records,records,records)['accepted'])
        for value in (-0.,float('nan'),float('inf'),.00001):
            changed=copy.deepcopy(records);changed[3]['components']['x']=value
            self.assertFalse(pooled_loss_acceptance(records,records,changed)['accepted'])
        changed=copy.deepcopy(records);changed[3]['components']={'other':0.}
        with self.assertRaisesRegex(ValueError,'Loss field'):
            pooled_loss_acceptance(records,records,changed)
        changed=copy.deepcopy(records);changed[2]['first_step_micro_losses'].append(1.)
        with self.assertRaisesRegex(ValueError,'Loss count'):
            pooled_loss_acceptance(records,records,changed)

    def manifest_fixture(self):
        directory=root()
        manifest=directory/'manifest.json';manifest.write_text('{}')
        receipt=dict(model=run.file_pin(manifest))
        for name,value in [('receipt.json',receipt),('config.json',{}),('plan.json',{})]:
            (directory/name).write_text(json.dumps(value))
        argv=['data_only.py','--tree',str(TREE),'--receipt',str(directory/'receipt.json'),
            '--manifest',str(manifest),'--config',str(directory/'config.json'),
            '--plan',str(directory/'plan.json'),'--out',str(directory/'out.json')]
        return directory,receipt,argv

    def test_wrong_processor_manifest_refuses_before_loading_processor(self):
        import data_only
        directory,receipt,argv=self.manifest_fixture()
        (directory/'manifest.json').write_text('{"root":"wrong"}')
        with patch.object(sys,'argv',argv), patch.object(run,'processor_for_receipt',side_effect=AssertionError('wrong processor loaded')) as processor:
            with self.assertRaisesRegex(ValueError,'model pin'):
                data_only.main()
        processor.assert_not_called()

    def test_valid_manifest_matches_trainer_pin_and_alternate_path_refuses(self):
        from data_only import processor_manifest
        directory,receipt,_=self.manifest_fixture()
        self.assertEqual(processor_manifest(run,receipt,directory/'manifest.json'),{})
        alternate=directory/'copy.json';alternate.write_text('{}')
        with self.assertRaisesRegex(ValueError,'model pin'):
            processor_manifest(run,receipt,alternate)

    def continuation_fixture(self):
        directory,audits=previous_tests.Round4Kits().replay_fixture()
        for rank in range(4):
            for arm,value in zip(('off1','off2','on'), (0.,1.,.5) if rank==1 else (0.,.1,.3)):
                path=directory/arm/f'rank{rank}'/'steps.json'
                record=json.loads(path.read_text())[0]
                record.update(rank=rank,components={'x':value},stream_means={'vqa':value})
                path.write_text(json.dumps([record]))
        def metric(step, wall, data, on):
            ranks=[]
            for rank in range(4):
                value=.5 if rank==1 else .3
                ranks.append(dict(rank=rank,step=step,components={'x':value},stream_means={'vqa':value},
                    performance=dict(C1_CPU_PREFETCH='1' if on else '0',C1_BATCH_METRICS='0',C1_DECODED_CACHE_MIB='0'),
                    wall_seconds=wall+rank,data_seconds=data+rank))
            return dict(step=step,ranks=ranks)
        launch=[metric(s,10.,5.,False) for s in range(181,201)]
        continuation=[metric(s,8.,3.,True) for s in range(201,222)]
        # A large first-update cold start must be excluded from the wall window.
        continuation[0]['ranks'][3]['wall_seconds']=1000.
        for name,values in [('launch.jsonl',launch),('continuation.jsonl',continuation)]:
            (directory/name).write_text(''.join(json.dumps(v)+'\n' for v in values))
        return directory,launch,continuation

    def continuation_cli(self,directory,extra=()):
        return subprocess.run([sys.executable,'-I','-s','-B',str(BUNDLE/'kit_timing/continuation_check.py'),
            '--replay-out',str(directory),'--continuation',str(directory/'continuation.jsonl'),
            '--launch',str(directory/'launch.jsonl'),*extra],capture_output=True,text=True,env=os.environ.copy())

    def test_continuation_executable_passing_and_failing_fixtures(self):
        directory,launch,continuation=self.continuation_fixture()
        result=self.continuation_cli(directory)
        self.assertEqual(result.returncode,0,result.stderr)
        report=json.loads(result.stdout)
        self.assertTrue(report['accepted']);self.assertEqual(report['loss']['threshold'],2.)
        self.assertAlmostEqual(report['wall_ratio'],11/13)
        self.assertAlmostEqual(report['data_ratio'],6/8)
        for metric in continuation[1:]:
            for rank in metric['ranks']:rank['wall_seconds']+=2.
        (directory/'continuation.jsonl').write_text(''.join(json.dumps(v)+'\n' for v in continuation))
        result=self.continuation_cli(directory)
        self.assertEqual(result.returncode,1,result.stderr)
        self.assertEqual(json.loads(result.stdout)['wall_ratio'],1.)
        self.assertFalse(json.loads(result.stdout)['accepted'])

    def test_zero_data_wait_is_diagnostic_only(self):
        directory,launch,continuation=self.continuation_fixture()
        for record in launch:
            for rank in record['ranks']:
                rank['data_seconds']=0.
        (directory/'launch.jsonl').write_text(''.join(json.dumps(v)+'\n' for v in launch))
        result=self.continuation_cli(directory)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(json.loads(result.stdout)['accepted'])
        self.assertIsNone(json.loads(result.stdout)['data_ratio'])

    def test_continuation_loss_refusal_and_first_update_mode(self):
        directory,launch,continuation=self.continuation_fixture()
        path=directory/'continuation.jsonl';path.write_text(json.dumps(continuation[0])+'\n')
        result=self.continuation_cli(directory,('--first-only',))
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(json.loads(result.stdout)['wall_pending'])
        self.assertNotEqual(self.continuation_cli(directory).returncode,0)
        continuation[0]['ranks'][3]['components']['x']=3.
        path.write_text(json.dumps(continuation[0])+'\n')
        result=self.continuation_cli(directory,('--first-only',))
        self.assertEqual(result.returncode,1,result.stderr)
        self.assertFalse(json.loads(result.stdout)['loss']['accepted'])

    def test_continuation_refuses_missing_rank_step_key_provenance_or_bad_timer(self):
        directory,launch,original=self.continuation_fixture()
        for mutation in ('rank','step','key','provenance','timer','order'):
            with self.subTest(mutation=mutation):
                values=copy.deepcopy(original)
                if mutation=='rank':values[0]['ranks'].pop()
                if mutation=='step':values[0]['step']=202
                if mutation=='key':values[0]['ranks'][0]['components']={'wrong':.3}
                if mutation=='provenance':values[0]['ranks'][0]['performance']['C1_CPU_PREFETCH']='0'
                if mutation=='timer':values[1]['ranks'][0]['wall_seconds']=float('nan')
                if mutation=='order':values[0]['ranks'].reverse()
                (directory/'continuation.jsonl').write_text(''.join(json.dumps(v)+'\n' for v in values))
                self.assertNotEqual(self.continuation_cli(directory).returncode,0)

    def test_note_records_simulation_and_executable_command(self):
        note=(BUNDLE/'NOTE_FOR_TREE_REBUILD.md').read_text()
        for text in ('Simulation','false-refusal','all four ranks','continuation_check.py','--first-only','--replay-out','--continuation','--launch'):
            self.assertIn(text,note)

    def test_production_log_lf_citations_and_carriage_return_explanation(self):
        path=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/o/look2.out')
        raw=path.read_bytes();lines=raw.split(b'\n')
        self.assertEqual(raw.count(b'\r'),8)
        for number,step in zip((694,698,702,706),(100,101,102,200)):
            self.assertTrue(lines[number-2].startswith(f'STEP {step} '.encode()))
            self.assertTrue(lines[number-1].lstrip().startswith(b'shapes '))
        for file in ('REPORT.md','NOTE_FOR_TREE_REBUILD.md'):
            text=(BUNDLE/file).read_text()
            self.assertIn('694/698/702/706',text)
            self.assertIn('carriage return',text)
            self.assertNotIn('eight extra config lines',text)


if __name__=='__main__':unittest.main(verbosity=2)
