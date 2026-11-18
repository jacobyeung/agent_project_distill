"""Filtered identities and recoverable, bounded early returns; no remote operations."""
import offline_guard
from collections import Counter
from contextlib import redirect_stdout, nullcontext
import copy
import io
import json
from pathlib import Path
import random
import signal
import sys
import tarfile
import time
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'kit/launcher'), str(ROOT/'kit/reader')]
import orchard_launcher as L
import orchard_job as J
import orchard_results as R
import chain_save as A
import read_filter as F
from tools.unpack_return import unpack


def folder():
    p = ROOT/'evidence'/('test_fix4_'+uuid.uuid4().hex)
    p.mkdir()
    return p


def prepare(root, **kwargs):
    return L.prepare('a000000001', root/'prepared', 544, run='469ddece',
                     generation='mstop', families=['a7'], **kwargs)


def journal(root, count=12, width=100):
    path = root/'a7/a0/results/0/g0.jsonl'
    path.parent.mkdir(parents=True)
    rng = random.Random(45)
    with path.open('w') as out:
        for i in range(count):
            # Deterministic high-entropy text exercises compression, not repeated padding.
            row = dict(id=str(i), key='devrows:'+str(i), status='complete', room='room'+str(i%98),
                       question_type='object_counting' if i%2 else 'object_size_estimation',
                       score=1, seconds=1, output_tokens=100,
                       raw_generation=rng.randbytes(width//2).hex())
            out.write(json.dumps(row)+'\n')
    return path


def partial(root, config, cap=89900000, count=12, width=100):
    source = root/'source'
    j = journal(source, count, width)
    archive = root/'partial.tar.gz'
    report = A.pack_partial(source, archive, config, cap-1)
    return archive, report, j


class FilterTests(unittest.TestCase):
    def test_outer_reader_preserves_full_frame_admission(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('fix4_worker', ROOT/'kit/reader/worker.py')
        worker = importlib.util.module_from_spec(spec); spec.loader.exec_module(worker)
        root = folder(); dest = root/'run/main/a0'; dest.mkdir(parents=True)
        tasks = [dict(example_id=str(i), question_type=t, native=str(i), room=str(i))
                 for i,t in enumerate(('object_counting', 'room_size_estimation'))]
        captures = {t['native']:dict(hw=[1,1],frames=[dict(sha256=t['native'])]) for t in tasks}
        cfg = dict(cells=[], source_sha256='fixture', legs1={}, output=str(dest/'results'))
        config = dict(spec=dict(run=str(root/'run'), types='direct', step=200,
            models=dict(base=dict(path='base',manifest=dict(path='manifest'))),
            artifact=dict(path=str(root/'artifact.json'),sha256='a'*64),
            interpreters=dict(p1cpu='fixture')))
        load = worker.T.load
        def loaded(path):
            if str(path) == 'manifest' or str(path).endswith('full_weights.json'):
                return dict(files=[dict(bytes=1)])
            return load(path)
        admitted = []
        def frames(cfg, rows, captures, *args):
            admitted.extend(rows)
            self.assertEqual({r['example_id'] for r in rows}, {'0','1'})
            self.assertEqual(set(captures), {'0','1'})
            return 'frame-pin'
        def launch(args):
            self.assertEqual(admitted, tasks)
            for arm in ('0','budget_2048/0','budget_4096/0'):
                p = dest/'results'/arm; p.mkdir(parents=True)
                (p/'summary_a0.json').write_text(json.dumps(dict(parity_pass=True,
                    benchmarks=dict(devrows=dict(missing=0,completed=1,expected=1)))))
                (p/'items_a0.jsonl').write_text('{}\n')
        def report(cfg, attempt, output):
            output.mkdir(); (output/'B2048.json').write_text('{}')
        sys.path.insert(0,str(ROOT/'kit/proof'))
        import phase_b
        with patch.object(worker,'bind',return_value=(NS(check_export=lambda *a:{},launch=launch),
                NS(make_frames=frames),None,dest,cfg,tasks,captures)), \
             patch.object(worker.T,'load',side_effect=loaded), \
             patch.object(worker.shutil,'disk_usage',return_value=NS(free=10**15)), \
             patch.object(phase_b,'pull_frames'), patch.object(F,'task_provider',return_value=nullcontext()), \
             patch.dict(sys.modules,report=NS(export_merged=report)), \
             patch.object(worker,'records',return_value=[dict(id='0')]):
            worker.run(config,'main')
        complete = json.loads((dest.parent/'COMPLETE.json').read_text())
        self.assertEqual(complete['items'],1)
        self.assertEqual(complete['population']['excluded']['room_size_estimation']['items'],1)

    def test_filtered_cli_identity_denominators_and_empty_refusal(self):
        root = folder()
        argv = ['launcher', 'prepare', '--run', '469ddece', '--step', '544', '--generation', 'mstop',
                '--families', 'a7', '--types', 'direct', '--token', 'a000000001',
                '--destination', str(root/'prepared')]
        with patch.object(sys, 'argv', argv), redirect_stdout(io.StringIO()):
            L.main()
        cfg = json.loads((root/'prepared/CONFIG.json').read_text())
        self.assertEqual(cfg['types'], 'direct')
        self.assertEqual(cfg['spec']['types'], 'direct')
        self.assertEqual(cfg['plan_sha256'], L.canonical(cfg['spec']))
        pop = cfg['spec']['population']['a7']
        self.assertEqual(pop['items'], 1781)
        self.assertEqual(pop['types'], dict(object_counting=385, object_size_estimation=293,
            object_rel_direction_easy=192, object_rel_direction_medium=194,
            object_rel_direction_hard=192, obj_appearance_order=246, object_rel_distance=279))
        self.assertEqual(pop['excluded'], {'object_abs_distance':dict(items=290, excluded=True),
                                         'room_size_estimation':dict(items=98, excluded=True)})
        self.assertEqual(cfg['extra']['registered_rooms'], 100)
        L.validate_batch((root/'prepared/BATCH.sh').read_text(), cfg)
        broken = copy.deepcopy(cfg); broken['types'] = None
        with self.assertRaises(ValueError): L.validate_request(broken)
        original = Path.read_text
        def empty(path, *args, **kwargs):
            if path == L.ROOT.parent/'reader/e193_items.json':
                return json.dumps({'families':{'main':{'items':{'one':'room_size_estimation'}}}})
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', empty):
            dest = folder()
            with self.assertRaisesRegex(ValueError, 'empties family'):
                L.prepare('a000000001', dest/'prepared', 200, run='359fcc3c', families=['main'], types='direct')
            self.assertFalse((dest/'prepared').exists())
        with self.assertRaisesRegex(ValueError, 'empties family'):
            F.select([dict(question_type=t) for t in F.EXCLUDED], {'types':'direct'})

    def test_unfiltered_fixture_plan_exact_and_config_only_integrity_pins(self):
        # Existing FIX3 preparation, never rewritten or regenerated in place.
        path = ROOT.parent/'h1read/evidence/test_fix3_targeted_a738cb8e2831495493f913ce23192669/test_fix3_e9b77b5c8c1a44fd93d2dc2d7b0822d5/prepared/CONFIG.json'
        old = json.loads(path.read_text())
        new = prepare(folder())
        self.assertEqual(json.dumps(new['spec'], sort_keys=True).encode(),
                         json.dumps(old['spec'], sort_keys=True).encode())
        self.assertEqual(new['plan_sha256'], old['plan_sha256'])
        integrity = {'payload_pins', 'payload_sha256', 'launcher_pins', 'launcher_review', 'launcher_review_pin'}
        self.assertEqual({k:v for k,v in new.items() if k not in integrity},
                         {k:v for k,v in old.items() if k not in integrity})
        self.assertNotIn('types', new)

    def test_all_families_full_kept_membership_and_provider_aliases(self):
        inventory = json.loads((ROOT/'kit/reader/e193_items.json').read_text())['families']
        for family in ('main', 'away', 'forward'):
            rows = [dict(example_id=k, question_type=v) for k,v in inventory[family]['items'].items()]
            kept = F.select(rows, {'types':'direct'})
            self.assertTrue(kept)
            self.assertEqual(Counter(r['question_type'] for r in kept),
                {k:v for k,v in Counter(r['question_type'] for r in rows).items() if k not in F.EXCLUDED})
            modules = {n:NS(tasks_for=lambda *args:copy.deepcopy(rows)) for n in ('data','worker','merge','budget_merge')}
            calls = []
            def validate(actual):
                self.assertEqual(actual, rows); calls.append(True)
            with patch.object(F.importlib, 'import_module', side_effect=modules.__getitem__):
                with F.task_provider({'types':'direct'}, validate):
                    for m in modules.values(): self.assertEqual(m.tasks_for({}, {}), kept)
            self.assertEqual(len(calls), 4)
        cfg = L.prepare('a000000001', folder()/'prepared', 200, run='359fcc3c', types='direct')
        self.assertEqual(set(cfg['spec']['population']), {'main','away','forward','a7'})

    def test_filtered_chain_completes_and_packs_kept_items(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('fix4_chain', ROOT/'kit/reader/chain.py')
        chain = importlib.util.module_from_spec(spec); spec.loader.exec_module(chain)
        root = folder(); cfg = prepare(root, types='direct')
        source = root/'run'; cfg['spec']['run'] = str(source); cfg['admission'] = {}
        rows = F.select([json.loads(l) for l in (ROOT/'assets/e52a690b.jsonl').read_text().splitlines()], cfg['spec'])
        class Process:
            stdout = io.BytesIO()
            def wait(self):
                p = source/'a7'; p.mkdir()
                (p/'COMPLETE.json').write_text(json.dumps(dict(items=len(rows), population=cfg['spec']['population']['a7'])))
                (p/'ITEMS.jsonl').write_text(''.join(json.dumps(dict(id=r['id'], family='a7',
                    task_type=r['question_type'], room=r['room'], score=1))+'\n' for r in rows))
                return 0
        with patch.object(chain.subprocess, 'Popen', return_value=Process()), patch.dict(chain.os.environ, A_JOB_CONFIG='fixture'):
            chain.run(cfg)
        report = json.loads((source/'SUMMARY.json').read_text())
        self.assertTrue(report['complete']); self.assertEqual(report['items'], 1781)
        self.assertEqual(report['coverage']['registered_rooms'], 100)
        self.assertEqual(set(report['excluded']['a7']), set(F.EXCLUDED))
        self.assertFalse(set(report['scores']['a7']) & set(F.EXCLUDED))
        with patch.object(R, 'pool_operation', return_value={'verified':True}), patch.object(R, 'upload', return_value={'verified':True}):
            result = R.publish(source, root/'pool', cfg['token'], cfg['plan_sha256'], 0)
        self.assertEqual(result['status'], 'COMPLETE')
        R.verify(result, Path(result['local_return'])/'result.tar.gz', cfg['plan_sha256'])


class PartialTests(unittest.TestCase):
    def test_large_journal_pack_time_and_no_lost_lines(self):
        root = folder(); cfg = prepare(root)
        archive, report, j = partial(root, cfg, count=1958, width=27880)
        self.assertGreater(j.stat().st_size, 54_000_000)
        self.assertLess(j.stat().st_size, 56_000_000)
        self.assertEqual(report['families']['a7']['finished_items'], 1958)
        self.assertFalse(report['truncated'])
        with tarfile.open(archive) as tf:
            self.assertEqual(tf.extractfile('a7/a0/results/0/g0.jsonl').read(), j.read_bytes())
        proof = A.pack_partial(root/'source', root/'proof.tar.gz', cfg, 19_900_000-1)
        self.assertTrue(proof['truncated'])
        self.assertLess(proof['bytes'], 19_900_000)
        self.assertEqual(proof['families']['a7']['finished_items'], 1958)
        print('FIX4_PACK_BENCHMARK '+json.dumps(dict(journal_bytes=j.stat().st_size,
              lines=1958, archive_bytes=report['bytes'], packing_seconds=report['seconds'])), flush=True)

    def test_truncation_whole_lines_counts_torn_tail_and_proof_cap(self):
        root = folder(); cfg = prepare(root, types='direct')
        archive, report, j = partial(root, cfg, cap=600000, count=120, width=10000)
        name = 'a7/a0/results/0/g0.jsonl'
        self.assertTrue(report['truncated']); self.assertLess(archive.stat().st_size, 600000)
        self.assertEqual(report['families']['a7']['finished_items'], 120)
        self.assertLess(report['journals'][name]['retained_lines'], 120)
        with tarfile.open(archive) as tf:
            raw = tf.extractfile(name).read()
            self.assertTrue(raw.endswith(b'\n'))
            self.assertEqual(len([json.loads(l) for l in raw.splitlines()]), report['journals'][name]['retained_lines'])
        with j.open('ab') as stream: stream.write(b'{"status":"comp')
        report = A.pack_partial(root/'source', root/'torn.tar.gz', cfg, 19_900_000-1)
        self.assertEqual(report['journals'][name]['invalid_lines'], 1)
        self.assertEqual(report['families']['a7']['finished_items'], 120)

    def test_cancel_during_summary_write_keeps_journals(self):
        root = folder(); cfg = prepare(root)
        j = journal(root/'source')
        (j.parent/'summary_a0.json').write_text('{"benchmarks":')
        (root/'source/a7/COMPLETE.json').write_text('{')
        report = A.pack_partial(root/'source', root/'partial.tar.gz', cfg, 89900000-1)
        self.assertEqual(report['families']['a7']['finished_items'], 12)
        self.assertEqual(len(report['malformed_summaries']), 2)
        with tarfile.open(root/'partial.tar.gz') as tf:
            self.assertEqual(tf.extractfile('a7/a0/results/0/g0.jsonl').read(), j.read_bytes())

    def test_signal_failure_and_timeout_pack_before_publish(self):
        import trace_runtime
        for trigger in (signal.SIGTERM, signal.SIGUSR1, signal.SIGINT, 'exception', 'chain', 'late_card', 'late_publish', 'publish_exception'):
            root = folder(); cfg = prepare(root, types='direct')
            source = J.physical(root, cfg['spec']['run']); journal(source)
            handlers = {}
            def handler(number, fn): handlers[number] = fn
            def stage(*args):
                if trigger == 'exception': raise ValueError('fixture stage failure')
                return {}
            class Process:
                def wait(self):
                    if trigger == 'chain': return 7
                    if trigger in ('late_card', 'late_publish', 'publish_exception'):
                        (source/'COMPLETE.json').write_text(json.dumps(dict(plan_sha256=cfg['plan_sha256'], synthetic=False)))
                        return 0
                    handlers[trigger](trigger, None)
                def poll(self): return 7
            def card(**kwargs):
                if not kwargs and trigger == 'late_card': handlers[signal.SIGTERM](signal.SIGTERM, None)
                return {}
            def publish(*args, **kwargs):
                if 'partial' not in kwargs:
                    if trigger == 'late_publish': handlers[signal.SIGTERM](signal.SIGTERM, None)
                    if trigger == 'publish_exception': raise ValueError('fixture publish failure')
                path, report = kwargs['partial']
                self.assertTrue(path.is_file())
                self.assertEqual(report['families']['a7']['finished_items'], 12)
                self.assertFalse(report['complete'])
                self.assertTrue(all(v == signal.SIG_IGN for v in handlers.values()))
                return dict(status='PARTIAL')
            with patch.object(J.signal,'signal',side_effect=handler), patch.object(R,'write_test',return_value={}), \
                 patch.object(J,'storage_proof',return_value={'source':'local'}), patch.object(J,'environment',return_value={}), \
                 patch.object(J,'card',side_effect=card), patch.object(J.S,'stage',side_effect=stage), \
                 patch.object(J,'namespace',return_value=[]), patch.object(J.subprocess,'Popen',return_value=Process()), \
                 patch.object(R,'publish',side_effect=publish) as pub, patch.object(trace_runtime,'snapshot'), \
                 patch.object(trace_runtime,'collect'), patch.dict(J.os.environ, SLURM_JOB_ID='123'):
                # environment() normally supplies these three values.
                with patch.object(J,'environment',return_value={k:str(root) for k in ('HOME','TMPDIR','XDG_CACHE_HOME')}):
                    self.assertNotEqual(J.run(root, cfg), 0)
            self.assertEqual(pub.call_count, 2 if trigger in ('late_publish','publish_exception') else 1)

    def test_partial_publish_verify_unpack_and_final_score_refusal(self):
        root = folder(); cfg = prepare(root, types='direct')
        archive, report, _ = partial(root, cfg)
        dest = root/'prepared'; fetched = dest/'fetched'; fetched.mkdir()
        (dest/'SUBMISSION.json').write_text(json.dumps(dict(status='SUBMITTED',job=123)))
        with patch.object(R,'pool_operation',return_value={'verified':True}) as pool, \
             patch.object(R,'upload',side_effect=AssertionError('No second transfer after verified partial')), \
             patch.dict(R.os.environ,SLURM_JOB_ID='123'):
            result = R.publish(root/'source', root/'pool', cfg['token'], cfg['plan_sha256'], 1,
                               partial=(archive,report))
        self.assertEqual(result['status'],'PARTIAL'); self.assertFalse(result['complete'])
        self.assertEqual(pool.call_args_list[0].kwargs['timeout'],8)
        returned = Path(result['local_return'])/'result.tar.gz'
        with self.assertRaises(ValueError): R.verify(result,returned,cfg['plan_sha256'])
        R.verify(result,returned,cfg['plan_sha256'],allow_partial=True)
        (fetched/'result.tar.gz').write_bytes(returned.read_bytes())
        (fetched/'EXIT.json').write_text(json.dumps(result))
        with redirect_stdout(io.StringIO()) as output: target = unpack(dest)
        self.assertIn('PARTIAL',output.getvalue())
        self.assertFalse(json.loads((target/'SUMMARY.json').read_text())['complete'])
        def transfer(argv, **kwargs):
            kwargs['stdout'].write(returned.read_bytes())
            return NS(returncode=0)
        with patch.object(L, 'remote', return_value=NS(returncode=0,stdout=json.dumps(result).encode())), \
             patch.object(L, 'remote_transport', return_value=['fixture']), patch.object(L.subprocess, 'run', side_effect=transfer):
            fetched_result = L.fetch(dest)
        self.assertEqual(fetched_result['status'], 'PARTIAL')
        broken = dict(result,plan_sha256='b'*64)
        with self.assertRaises(ValueError): R.verify(broken,returned,cfg['plan_sha256'],allow_partial=True)


if __name__ == '__main__': unittest.main()
