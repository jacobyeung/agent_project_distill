"""CPU fixtures; set TEST_TMP_ROOT to keep all retained test files in scratch."""
import copy
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import torch
torch.set_num_threads(8)

TREE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TREE))
spec = importlib.util.spec_from_file_location("prepared_cache", TREE / "launch_s1/b/pc.py")
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)


class Fixture:
    def __init__(self, same_path=False, extra_config=None):
        self.root = Path(tempfile.mkdtemp(prefix="pc-test-", dir=os.environ["TEST_TMP_ROOT"]))
        self.kit, self.node, self.cache = (self.root / name for name in ("kit", "node", "cache"))
        self.source, self.target = self.root / "old-run/inputs", self.root / "new-run/inputs"
        # Production uses the same physical path for one logical run. The
        # default synthetic relocation fixture only exercises defensive copying.
        if same_path:
            self.target = self.source
        self.logical = self.target
        for directory in (self.kit / "k", self.kit / "b", self.source, self.node):
            directory.mkdir(parents=True)
        (self.kit / "b/s.py").write_text("# fixture staging implementation\n")
        (self.kit / "b/pc.py").write_bytes((TREE / "launch_s1/b/pc.py").read_bytes())
        frame = b"a tiny pinned RGB fixture"
        h = pc.hashlib.sha256(frame).hexdigest()
        self.relative = "k3f8/" + h[:2] + "/" + h + ".png"
        self.frame = self.node / "c7d31ddd/data2root" / self.relative
        self.frame.parent.mkdir(parents=True)
        self.frame.write_bytes(frame)
        manifest = self.root / "frames.json"
        pc.atomic(manifest, [dict(path="/data2/" + self.relative, sha256=h)])
        self.cfg = dict(output=str(self.target.parent), preparation_output=str(self.root / "logical-prep"),
                        streams={k: dict(path="/sources/" + k, sha256=pc.digest(k))
                                 for k in ("pose", "vqa", "pointing", "routing")},
                        code=dict(path="/logical/k/code.json", sha256="a"*64),
                        init_artifact=dict(artifact=dict(path="/parent/artifact.json", sha256="b"*64)),
                        world_size=4, remove_files=[], training_mode="final")
        self.cfg.update(extra_config or {})
        config = self.kit / "k/config.json"
        pc.atomic(config, self.cfg)
        self.current = dict(commit="sha256:" + "c"*64,
                            trainer=dict(file="trainer.tar", sha256="d"*64),
                            venv=dict(file="runtime.tar", sha256="e"*64),
                            stores=dict(f3="k3f8"), f3=dict(file="frames.tar", sha256="f"*64),
                            f3_manifest=dict(file=str(manifest), sha256=pc.sha(manifest)))
        pc.atomic(self.kit / "k/0.json", self.current)
        self.launch = dict(config=dict(file="k/config.json", sha256=pc.sha(config)),
                           run_directory=str(self.source.parent), in_job_admission=dict(
                               schema="s1-in-job-admission-v1", directory=str(self.logical),
                               frame_roots=[str(self.node / "c7d31ddd/data2root")]))
        pc.atomic(self.kit / "k/launch.json", self.launch)
        request = dict(config=dict(path="/logical/k/config.json", sha256=pc.sha(config)),
                       frame_roots=self.launch["in_job_admission"]["frame_roots"],
                       source_revision=self.current["commit"])
        pc.atomic(self.source / "request.json", request)
        prep, frames = "prepare_" + "1"*32, "frames_" + "2"*32
        self.prep = prep
        database = self.source / prep / "pointing/rows.sqlite"
        database.parent.mkdir(parents=True)
        with sqlite3.connect(database) as conn:
            conn.execute("CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT)")
            conn.execute("INSERT INTO rows VALUES (0, '{}')")
        pc.atomic(self.source / prep / "config.json", self.cfg)
        pc.atomic(self.source / prep / "receipt.json", dict(database=self.pin(database)))
        inventory = self.source / frames / "frame_inventory.sqlite"
        inventory.parent.mkdir(parents=True)
        with sqlite3.connect(inventory) as conn:
            conn.execute("CREATE TABLE frames (path TEXT PRIMARY KEY, logical TEXT, sha256 TEXT)")
            conn.execute("INSERT INTO frames VALUES (?,?,?)", (str(self.frame), "/data2/"+self.relative, h))
        report = self.source / frames / "frames.json"
        pc.atomic(report, dict(inventory=self.pin(inventory), all_retained_frames_exist=True,
                               sources=dict(pose=dict(hash_sample=[dict(path="/data2/"+self.relative, sha256=h)]))))
        for name, directory, outputs in (("prepare", prep, [database, self.source / prep / "receipt.json",
                                                           self.source / prep / "config.json"]),
                                         ("frames", frames, [inventory, report])):
            result = self.source / directory / "result.json"
            pc.atomic(result, dict(outputs=[self.pin(p) for p in outputs], resources=dict(seconds=1)))
            pc.atomic(self.source / ("phase_"+name+".complete.json"),
                      dict(schema="s1-admission-phase-v1", binding=request, payload=self.pin(result)))
        pc.atomic(self.source / "data_receipt.json", dict(
            schema="s1-in-job-data-v1", status="PREPARED", real_frames_verified=True,
            rehearsal=False, gpu_first_step_pending=True, input_config=request["config"],
            input_streams=self.cfg["streams"], source_revision=self.current["commit"],
            config=self.pin(self.source / prep / "config.json"), frames=self.pin(report)))

    def pin(self, path):
        return dict(path=str(self.logical / path.relative_to(self.source)), sha256=pc.sha(path))

    def context(self, job="old"):
        return pc.Context(self.kit, self.node, self.cache, job)

    def publish(self):
        ctx = self.context()
        pc.seal(ctx)
        self.key = ctx.key
        return ctx

    def consumer(self, job="new"):
        self.launch["run_directory"] = str(self.target.parent)
        pc.atomic(self.kit / "k/launch.json", self.launch)
        return self.context(job)


class PreparedCacheTests(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()

    def test_real_wrapper_environment_has_same_restore_and_seal_key(self):
        f = self.f
        source = (TREE / 'launch_s1/b/c.sh').read_text()
        function = 'tk_env() {' + source.split('tk_env() {', 1)[1].split('\n}', 1)[0] + '\n}'
        environment = dict(os.environ)
        for name in ('R1_MOUNT', 'R1_STUDENT_HEX'):
            environment.pop(name, None)
        environment.update(X=pc.X, EPOCHS='/home/jjyeung/6d00e578', COMMIT=f.current['commit'],
                           P='/project/community/jjyeung/c7d31ddd', CLOSURE_DIR='fixture',
                           R1_RUNTIME_RECORD='/pinned/runtime.json', S=str(f.node),
                           TK_JOBDIR=str(f.root / 'job-environment'))
        code = 'import json,os; print(json.dumps({name:os.environ.get(name) for name in ' + repr(pc.ENVIRONMENT) + '}))'
        result = subprocess.run(['bash', '-c', function + '\ntk_env\n/usr/bin/python3 -I -c "$1"',
                                 'fixture', code], env=environment, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        before = pc.key_components(f.cfg, f.current, f.launch['in_job_admission'], {}, environment)
        after = pc.key_components(f.cfg, f.current, f.launch['in_job_admission'], {}, json.loads(result.stdout))
        self.assertEqual(before, after, 'tk_env must not change the cache key between restore and seal')

    def test_hit_verifies_and_preserves_native_journal(self):
        f = self.f
        source = f.publish()
        ctx = f.consumer()
        self.assertEqual(source.key, ctx.key)
        self.assertTrue(pc.restore(ctx))
        from student_pilot.first_batch_progress import PhaseJournal
        journal = PhaseJournal(f.target, pc.read(f.target / "request.json"))
        for phase in ("prepare", "frames"):
            _, reused = journal.run(phase, lambda _: self.fail("cache rebuilt a complete phase"))
            self.assertTrue(reused)
        from student_pilot.s1_admission import verify_frames
        report_pin = pc.read(f.target / "data_receipt.json")["frames"]
        with patch("student_pilot.orchard_paths.resolve_read", lambda _: f.frame):
            verify_frames(pc.read(report_pin["path"]))
        record = pc.read(ctx.report)
        self.assertEqual(record["source_job"], "old")
        self.assertEqual(record["source_inputs"], str(f.source))
        self.assertEqual(record["target_inputs"], str(f.target))
        self.assertGreater(record["verified_files"], 5)
        self.assertEqual(record["verified_frames"], 1)
        self.assertEqual(pc.sha(record["receipt"]["path"]), record["receipt"]["sha256"])
        inventory = pc.read(record["receipt"]["path"])
        for name, pin in inventory["files"].items():
            self.assertEqual(pc.sha(f.target / name), pin["sha256"])
        self.assertEqual(inventory["frames"][f.relative]["sha256"], pc.sha(f.frame))

    def test_restored_receipts_pass_the_native_training_gate_without_rebinding(self):
        f = self.f
        sys.path.insert(0, str(TREE / 'launch_s1/b'))
        spec = importlib.util.spec_from_file_location('cache_native_gate', TREE / 'launch_s1/b/d.py')
        gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate)
        f.cfg.update(base_identity='fixture-base', first_step_admission='all_rank_native_v1',
                     s1_routing=dict(schema='s1-routing-inputs-v1'),
                     scene_coverage=dict(schema='s1-scene-coverage-v1',
                         reference=dict(path='/inputs/scenes.json', sha256='1'*64),
                         source_map=dict(pose=[dict(source='fixture')])))
        pc.atomic(f.kit / 'k/config.json', f.cfg)
        f.launch['config']['sha256'] = pc.sha(f.kit / 'k/config.json')
        f.launch.update(source_revision=f.current['commit'],
                        source_seal=dict(tree_sha256='c'*64,
                            archive=dict(path='/inputs/source.tar', sha256='d'*64)))
        f.launch['in_job_admission'].update(parent_grounding_required=True, gpu_first_step_required=True)
        pc.atomic(f.kit / 'k/launch.json', f.launch)
        request = pc.read(f.source / 'request.json')
        request['config']['sha256'] = f.launch['config']['sha256']
        pc.atomic(f.source / 'request.json', request)

        def put(relative, value):
            path = f.source / relative
            pc.atomic(path, value)
            return f.pin(path)

        prepared = copy.deepcopy(f.cfg)
        prepared['streams']['pointing'] = f.pin(f.source / f.prep / 'receipt.json')
        prepared['streams']['vqa'] = put(f.prep + '/vqa.json', dict(schema='c1-stream-v1', stream='vqa',
            source=f.cfg['streams']['vqa'], source_receipt=f.cfg['streams']['vqa']))
        materialization = put(f.prep + '/materialization.json', dict(schema='s1-routing-materialization-v1',
            status='PASS', inputs=f.cfg['s1_routing'], legacy=f.cfg['streams']['routing']))
        prepared['streams']['routing'] = put(f.prep + '/routing.json', dict(materialization=materialization))
        prepared['preparation_output'] = str(f.logical / f.prep / 'prepared')
        seal = dict(schema='s1-run-seal-v1', tree_sha256='c'*64,
                    archive=f.launch['source_seal']['archive'], config_sha256=gate.config_identity(prepared))
        seal['sha256'] = gate.digest(seal)
        coverage = dict(coverage=dict(schema='s1-scene-coverage-result-v1', status='PASS',
                                     policy=f.cfg['scene_coverage'], sources=dict(pose=dict(rows=1))))
        prepared['preparation'] = put(f.prep + '/prepared/receipt.json', dict(
            config_sha256=gate.config_identity(prepared), source_seal=seal, scene_filter_report=coverage,
            stream_status=dict(mdg='absent'), streams={name:dict(count=1) for name in f.cfg['streams']}))
        config = put(f.prep + '/config.json', prepared)
        parent = put(f.prep + '/parent_grounding.json', dict(schema='s1-parent-grounding-v1', status='PASS',
            mdg='absent', method='verify-parent-metadata-without-mdg', parent_base_identity=f.cfg['base_identity'],
            parent_weight_payloads_verified=False, full_parent_model_loaded=False,
            parent_artifact=f.cfg['init_artifact']['artifact']))
        data = pc.read(f.source / 'data_receipt.json')
        data.update(production_authorized=False, world_size=4, input_config=request['config'], config=config,
                    source_seal=seal, source_counts={name:1 for name in f.cfg['streams']},
                    preparation=prepared['preparation'], parent_grounding=parent, mdg='absent',
                    scene_exclusions=coverage, routing_materialization=materialization)
        pc.atomic(f.source / 'data_receipt.json', data)
        for phase in ('prepare', 'frames'):
            path = f.source / ('phase_' + phase + '.complete.json')
            marker = pc.read(path)
            marker['binding'] = request
            result_path = f.source / Path(marker['payload']['path']).relative_to(f.logical)
            result = pc.read(result_path)
            for output in result['outputs']:
                output['sha256'] = pc.sha(f.source / Path(output['path']).relative_to(f.logical))
            pc.atomic(result_path, result)
            marker['payload']['sha256'] = pc.sha(result_path)
            pc.atomic(path, marker)
        self.assertEqual(gate.effective(f.kit, f.cfg, f.launch), prepared)
        f.publish()
        ctx = f.consumer()
        self.assertTrue(pc.restore(ctx))
        self.assertEqual(gate.effective(f.kit, f.cfg, f.launch), prepared)
        self.assertEqual(pc.read(f.target / 'data_receipt.json')['source_seal'], seal)
        self.assertEqual((f.source / 'data_receipt.json').read_bytes(), (f.target / 'data_receipt.json').read_bytes())

    def test_each_key_component_changed_alone_misses(self):
        f = self.f
        base = f.publish().components
        mutations = {
            "input_config": lambda v: v.update(sha256="6"*64),
            "store_receipts": lambda v: v["pose"].update(sha256="1"*64),
            "preparation_config": lambda v: v.update(ground_target_filter=False),
            "frame_manifests": lambda v: v["f3_manifest"].update(sha256="2"*64),
            "preparation_code_identity": lambda v: v.update(commit="sha256:"+"3"*64),
            "staging": lambda v: v["venv"].update(sha256="4"*64),
            "admission_contract": lambda v: v.update(frame_roots=["/different"]),
            "environment": lambda v: v.update(SLURM_CPUS_PER_TASK="changed"),
        }
        for component, change in mutations.items():
            with self.subTest(component=component):
                ctx = f.consumer(component)
                value = copy.deepcopy(base)
                change(value[component])
                self.assertEqual([k for k in value if value[k] != base[k]], [component])
                ctx.components, ctx.key = value, pc.digest(value)
                ctx.component_sha256 = {k: pc.digest(v) for k, v in value.items()}
                self.assertNotEqual(ctx.key, f.key)
                self.assertFalse(pc.restore(ctx))
                self.assertEqual(pc.read(ctx.report)["status"], "MISS")

    def test_real_config_init_and_code_changes_miss(self):
        f = self.f
        original = f.publish().key
        for field, value in (("seed", 99), ("init_artifact", {"artifact": {"sha256": "1"*64}})):
            cfg = {**f.cfg, field: value}
            pc.atomic(f.kit / "k/config.json", cfg)
            f.launch["config"]["sha256"] = pc.sha(f.kit / "k/config.json")
            ctx = f.consumer(field)
            self.assertNotEqual(ctx.key, original)
            self.assertFalse(pc.restore(ctx))
        pc.atomic(f.kit / "k/config.json", f.cfg)
        f.launch["config"]["sha256"] = pc.sha(f.kit / "k/config.json")
        (f.kit / "b/s.py").write_text("# different preparation code\n")
        ctx = f.consumer("code")
        self.assertNotEqual(ctx.key, original)
        self.assertFalse(pc.restore(ctx))

    def test_new_logical_run_cannot_reuse_a_native_configuration_seal(self):
        f = self.f
        original = pc.key_components(f.cfg, f.current, f.launch['in_job_admission'], {}, {})
        changed = {**f.cfg, 'output':'/another/logical/run'}
        other = pc.key_components(changed, f.current, f.launch['in_job_admission'], {}, {})
        self.assertNotEqual(pc.digest(original), pc.digest(other))

    def test_same_parsed_config_with_different_file_pin_misses(self):
        f = self.f
        original = f.publish().key
        path = f.kit / 'k/config.json'
        path.write_text(json.dumps(f.cfg, indent=2) + '\n')
        f.launch['config']['sha256'] = pc.sha(path)
        ctx = f.consumer()
        self.assertEqual(ctx.cfg, f.cfg)
        self.assertNotEqual(ctx.key, original, 'native admission binds the exact config file SHA256')
        self.assertFalse(pc.restore(ctx))

    def test_same_key_different_code_in_receipt_is_refused(self):
        f = self.f
        f.publish()
        index_path = f.cache / (f.key + ".json")
        index = pc.read(index_path)
        path = f.cache / index["receipt"]
        value = pc.read(path)
        value["component_sha256"]["preparation_code_identity"] = pc.digest("foreign")
        pc.atomic(path, value)
        pc.atomic(index_path, {**index, "sha256": pc.sha(path)})
        ctx = f.consumer()
        self.assertFalse(pc.restore(ctx))
        self.assertIn("code identity", pc.read(ctx.report)["reason"])

    def test_unpinned_remove_path_cannot_form_a_cache_key(self):
        f = self.f
        cfg = {**f.cfg, "remove_files": ["/mutable/remove.jsonl"]}
        with self.assertRaisesRegex(ValueError, "content-pinned REMOVE"):
            pc.key_components(cfg, f.current, f.launch["in_job_admission"], {}, {})

    def test_unpinned_mdg_paths_cannot_form_a_cache_key(self):
        f = self.f
        pin = dict(path='/inputs/pinned.json', sha256='a'*64)
        mdg = {name: pin for name in ('clips_jsonl', 'confusers', 'vocab', 'stem_weights')}
        mdg.update(frame_root=dict(root='/frames', manifest=pin),
                   rasters=dict(root='/rasters', manifest=pin), exclude_scenes=['d1/scene0001_00'],
                   init_artifact={name:pin for name in ('mdg.json', 'mdg.pt')})
        # Native MDG accepts these path-only variants and hashes their contents
        # during preparation. The cache must refuse them because a path alone
        # cannot bind those contents in its key.
        for name in mdg:
            with self.subTest(field=name):
                cfg = {**f.cfg, 'mdg':{**mdg, name:'/mutable/' + name}}
                with self.assertRaisesRegex(ValueError, 'content-pinned optional inputs'):
                    pc.key_components(cfg, f.current, f.launch['in_job_admission'], {}, {})
        cfg = {**f.cfg, 'mdg':mdg}
        self.assertIn('mdg', pc.key_components(cfg, f.current, f.launch['in_job_admission'], {}, {})['preparation_config'])

    def test_another_complete_generation_does_not_replace_native_journal(self):
        f = self.f
        f.publish()
        consumer = f.consumer()
        self.assertTrue(pc.restore(consumer))
        before = pc.sha(f.target / "data_receipt.json")
        # A later complete producer may have a different artifact inventory.
        # The destination's valid native journal still belongs to its checkpoint.
        pc.atomic(f.source / f.prep / "additional.json", {"another_generation": True})
        f.launch["run_directory"] = str(f.source.parent)
        pc.atomic(f.kit / "k/launch.json", f.launch)
        self.assertTrue(pc.seal(f.context("later")))
        consumer = f.consumer("later-consumer")
        self.assertFalse(pc.restore(consumer))
        self.assertEqual(pc.read(consumer.report)["status"], "NATIVE_JOURNAL")
        self.assertEqual(pc.sha(f.target / "data_receipt.json"), before)
        self.assertFalse((f.target / f.prep / "additional.json").exists())
        self.assertFalse(pc.seal(consumer))

    def test_corrupt_prepared_file_misses_and_preserves_target(self):
        f = self.f
        f.publish()
        (f.source / f.prep / "pointing/rows.sqlite").write_bytes(b"corrupt")
        f.target.mkdir(parents=True)
        (f.target / "partial").write_text("native journal owns this")
        before = (f.target / "partial").stat()
        ctx = f.consumer()
        self.assertFalse(pc.restore(ctx))
        self.assertEqual((f.target / "partial").read_text(), "native journal owns this")
        self.assertEqual((f.target / "partial").stat(), before)
        self.assertEqual(list(f.target.parent.glob("inputs.cache-refused.*")), [])

    def test_partial_native_journal_survives_same_path_miss_and_reuses_prepare(self):
        f = Fixture(same_path=True)
        f.publish()
        for name in ("phase_frames.complete.json", "data_receipt.json"):
            (f.source / name).rename(f.root / name)
        before = {str(p.relative_to(f.source)): (p.read_bytes(), p.stat())
                  for p in f.source.rglob('*') if p.is_file()}
        ctx = f.context('partial')
        self.assertFalse(pc.restore(ctx))
        self.assertEqual(before, {str(p.relative_to(f.source)): (p.read_bytes(), p.stat())
                                for p in f.source.rglob('*') if p.is_file()})
        self.assertEqual(list(f.source.parent.glob('inputs.cache-refused.*')), [])
        from student_pilot.first_batch_progress import PhaseJournal
        journal = PhaseJournal(f.source, pc.read(f.source / 'request.json'))
        _, reused = journal.run('prepare', lambda _: self.fail('native prepare must remain reusable'))
        self.assertTrue(reused)

    def test_foreign_config_native_journal_survives_same_path_miss_and_refuses(self):
        f = Fixture(same_path=True)
        f.publish()
        before = {str(p.relative_to(f.source)): (p.read_bytes(), p.stat())
                  for p in f.source.rglob('*') if p.is_file()}
        f.cfg['training_mode'] = 'another-mode'
        pc.atomic(f.kit / 'k/config.json', f.cfg)
        f.launch['config']['sha256'] = pc.sha(f.kit / 'k/config.json')
        pc.atomic(f.kit / 'k/launch.json', f.launch)
        self.assertFalse(pc.restore(f.context('foreign')))
        self.assertEqual(before, {str(p.relative_to(f.source)): (p.read_bytes(), p.stat())
                                for p in f.source.rglob('*') if p.is_file()})
        self.assertEqual(list(f.source.parent.glob('inputs.cache-refused.*')), [])
        from student_pilot.first_batch_progress import PhaseJournal
        request = pc.read(f.source / 'request.json')
        request['config']['sha256'] = f.launch['config']['sha256']
        with self.assertRaisesRegex(ValueError, 'phase binding differs'):
            PhaseJournal(f.source, request).run('prepare', lambda _: self.fail('must refuse'))

    def test_same_path_hit_only_verifies_native_reuse_and_a_purge_misses(self):
        f = Fixture(same_path=True)
        ctx = f.publish()
        self.assertEqual(ctx.destination, f.source)
        with patch.object(pc, 'copy_verified', side_effect=AssertionError('no production copy')):
            self.assertTrue(pc.restore(ctx))
        from student_pilot.first_batch_progress import PhaseJournal
        journal = PhaseJournal(f.source, pc.read(f.source / 'request.json'))
        for name in ('prepare', 'frames'):
            _, reused = journal.run(name, lambda _: self.fail('native reuse already works'))
            self.assertTrue(reused)
        f.source.rename(f.root / 'purged-node-local-inputs')
        self.assertFalse(pc.restore(f.context('cold-node')))
        self.assertFalse(f.source.exists())

    def test_copy_failure_never_touches_destination(self):
        f = self.f
        f.publish()
        f.target.mkdir(parents=True)
        path = f.target / 'native-progress'
        path.write_text('preserve')
        before = path.stat()
        with patch.object(pc, 'copy_verified', side_effect=OSError('injected copy failure')):
            self.assertFalse(pc.restore(f.consumer()))
        self.assertEqual(path.read_text(), 'preserve')
        self.assertEqual(path.stat(), before)
        self.assertEqual(list(f.target.parent.glob('inputs.cache-refused.*')), [])

    def test_failed_verified_install_restores_the_native_destination(self):
        f = self.f
        f.publish()
        f.target.mkdir(parents=True)
        path = f.target / 'native-progress'
        path.write_text('preserve')
        before = path.stat()
        rename = Path.rename
        def injected(source, target):
            if source.name.startswith('inputs.cache-copy.'):
                raise OSError('injected rename failure')
            return rename(source, target)
        with patch.object(Path, 'rename', injected):
            self.assertFalse(pc.restore(f.consumer()))
        self.assertEqual(path.read_text(), 'preserve')
        self.assertEqual(path.stat(), before)

    def test_hit_report_write_error_is_not_a_cli_miss(self):
        f = self.f
        f.publish()
        ctx = f.consumer()
        with patch.dict(os.environ, {'TK_PREPARED_INPUT_CACHE':'1'}), patch.object(pc, 'Context', return_value=ctx), \
                patch.object(ctx, 'result', side_effect=OSError('injected report write failure')), \
                patch.object(sys, 'argv', ['pc.py', 'restore', str(f.kit), str(f.node), str(f.cache), 'new']):
            self.assertEqual(pc.main(), 2)
        self.assertTrue((f.target / 'data_receipt.json').is_file())

    def test_irrelevant_environment_is_absent_from_key_and_written_json_names(self):
        f = self.f
        irrelevant = {'QWEN36_27B_SNAPSHOT':'fixture', 'STUDENT_R2_FRAME_HOST':'fixture',
                      'STUDENT_R2_LOCAL_NODE':'fixture'}
        before = f.context().key
        with patch.dict(os.environ, irrelevant):
            self.assertEqual(f.context().key, before)
            f.publish()
            self.assertTrue(pc.restore(f.consumer()))
        forbidden = re.compile(r'qwen|(?:^|_)r2(?:_|$)|canary[-_]?delta|cp1[-_]?rv', re.I)
        def check_fields(value):
            if isinstance(value, dict):
                for name, child in value.items():
                    self.assertIsNone(forbidden.search(name), name)
                    check_fields(child)
            elif isinstance(value, list):
                for child in value:
                    check_fields(child)
        written = [*f.cache.glob('*.json'), *(f.kit / 'o').glob('*.json')]
        self.assertGreaterEqual(len(written), 4)
        for path in written:
            self.assertIsNone(forbidden.search(path.name), path.name)
            check_fields(pc.read(path))

    def test_purged_pool_source_misses(self):
        f = self.f
        f.publish()
        f.source.rename(f.source.with_name("purged-fixture"))
        self.assertFalse(pc.restore(f.consumer()))

    def test_reports_and_receipts_store_only_component_digests(self):
        pin = dict(path='/inputs/pinned', sha256='a' * 64)
        mdg = {name: pin for name in ('clips_jsonl', 'confusers', 'vocab', 'stem_weights')}
        mdg.update(frame_root=dict(root='/frames', manifest=pin),
                   rasters=dict(root='/rasters', manifest=pin), exclude_scenes=[])
        f = Fixture(extra_config={'mdg': mdg, 'private_model': 'qwen-fixture'})
        source = f.publish()
        self.assertTrue(pc.restore(f.consumer()))
        expected = {name: pc.digest(value) for name, value in source.components.items()}
        for path in [*f.cache.glob('*.receipt.json'), *(f.kit / 'o').glob('*.json')]:
            record = pc.read(path)
            self.assertNotIn('key_components', record)
            self.assertEqual(record['component_sha256'], expected)
            self.assertEqual(record['key'], pc.digest(source.components))
            self.assertNotRegex(path.read_text().lower(), r'mdg|qwen|private_model')
        index = pc.read(f.cache / (source.key + '.json'))
        receipt_path = f.cache / index['receipt']
        receipt = pc.read(receipt_path)
        receipt['component_sha256']['preparation_config'] = '0' * 64
        pc.atomic(receipt_path, receipt)
        index['sha256'] = pc.sha(receipt_path)
        pc.atomic(f.cache / (source.key + '.json'), index)
        self.assertFalse(pc.restore(f.consumer('changed-digest')))

    def test_unpinned_optional_input_cli_refuses_without_method_or_traceback(self):
        f = Fixture(extra_config={'mdg': {'clips_jsonl': '/unpinned/private'}})
        result = subprocess.run([sys.executable, '-I', '-s', '-B',
            str(TREE / 'launch_s1/b/pc.py'), 'restore', str(f.kit), str(f.node), str(f.cache), 'refused'],
            env={**os.environ, 'TK_PREPARED_INPUT_CACHE': '1'}, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        self.assertIn('cache context refused', result.stderr)
        self.assertNotRegex(result.stdout + result.stderr, r'(?i)mdg|traceback|clips_jsonl')
        self.assertFalse(f.cache.exists())
        with self.assertRaisesRegex(ValueError, '^cache requires content-pinned optional inputs$'):
            f.context()

    def test_partial_prepared_directory_is_never_published(self):
        f = self.f
        (f.source / f.prep / "pointing/rows.sqlite").rename(f.root / "missing.sqlite")
        with self.assertRaisesRegex(ValueError, "partial or corrupt"):
            pc.seal(f.context())
        self.assertFalse(f.cache.exists())

    def test_partial_published_directory_misses(self):
        f = self.f
        f.publish()
        (f.source / f.prep / "result.json").rename(f.root / "missing-result.json")
        self.assertFalse(pc.restore(f.consumer()))

    def test_corrupt_or_missing_frames_force_ordinary_restaging(self):
        f = self.f
        f.publish()
        stamp = f.node / ".stamp" / ("f3." + f.current["f3"]["sha256"] + "." + f.current["f3_manifest"]["sha256"])
        stamp.parent.mkdir()
        stamp.write_text("")
        f.frame.write_bytes(b"wrong bytes")
        self.assertFalse(pc.restore(f.consumer()))
        self.assertFalse(f.frame.exists())
        self.assertFalse(stamp.exists())
        self.assertEqual(len(list(f.frame.parent.glob("*.cache-refused.*"))), 1)

    def test_uncovered_retained_frame_refuses_publication(self):
        f = self.f
        with patch.object(pc, "frame_files", return_value={}):
            with self.assertRaisesRegex(ValueError, "outside the cached manifests"):
                pc.seal(f.context())

    def test_symlink_and_path_traversal_refused(self):
        f = self.f
        f.publish()
        origin = f.source / f.prep / "config.json"
        moved = origin.with_name("config-original")
        origin.rename(moved)
        origin.symlink_to(moved)
        self.assertFalse(pc.restore(f.consumer()))
        for name in ("../escape", "/absolute"):
            with self.assertRaises(ValueError):
                pc.inside(f.root, name)

    def test_two_concurrent_publishers_commit_complete_receipts(self):
        f = self.f
        a, b = f.context("publisher_a"), f.context("publisher_b")
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(pc.seal, ctx) for ctx in (a, b)]
            for future in futures:
                future.result()
        self.assertTrue(pc.restore(f.consumer()))
        report = pc.read(f.kit / "o/new.prepared-cache.json")
        self.assertIn(report["source_job"], {"publisher_a", "publisher_b"})
        self.assertEqual(len(list(f.cache.glob("*.receipt.json"))), 2)

    def test_concurrent_consumers_keep_complete_target_and_training_evidence(self):
        f = self.f
        f.publish()
        a, b = f.consumer("consumer_a"), f.consumer("consumer_b")
        self.assertTrue(pc.restore(a))
        evidence = f.target / "first_step_prior.json"
        evidence.write_text('{"training_evidence":"preserve"}')
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(pc.restore, ctx) for ctx in (a, b)]
            self.assertEqual([future.result() for future in futures], [True, True])
        self.assertEqual(evidence.read_text(), '{"training_evidence":"preserve"}')

    def test_partial_index_is_a_miss(self):
        f = self.f
        f.publish()
        (f.cache / (f.key + ".json")).write_text('{"receipt":')
        self.assertFalse(pc.restore(f.consumer()))

    def test_cold_rebuild_after_miss_can_publish_and_hit(self):
        f = self.f
        f.publish()
        ctx = f.consumer()
        f.source.rename(f.root / "purged-source-fixture")
        self.assertFalse(pc.restore(ctx))
        # Fixture stands in for the unchanged native builder, with the same logical paths.
        files = pc.admission_files(ctx, f.root / "purged-source-fixture")
        pc.copy_verified(f.root / "purged-source-fixture", f.target, files)
        pc.seal(ctx)
        self.assertTrue(pc.restore(ctx))
        self.assertEqual(pc.read(ctx.report)["source_job"], "new")

    def test_an_existing_complete_journal_survives_a_cache_miss(self):
        f = self.f
        ctx = f.context()
        # No global cache receipt exists. The native journal already names exact files.
        before = pc.sha(f.source / "data_receipt.json")
        self.assertFalse(pc.restore(ctx))
        self.assertEqual(pc.read(ctx.report)["status"], "NATIVE_JOURNAL")
        self.assertEqual(pc.sha(f.source / "data_receipt.json"), before)
        pc.seal(ctx)
        self.assertFalse((f.cache / (ctx.key + ".json")).exists())

    def test_default_off_cli_has_no_side_effects(self):
        f = self.f
        with patch.dict(os.environ, {"TK_PREPARED_INPUT_CACHE": "0"}), patch.object(sys, "argv", [
                "pc.py", "restore", str(f.kit), str(f.node), str(f.cache), "off"]):
            self.assertEqual(pc.main(), 1)
        self.assertFalse(f.cache.exists())
        self.assertFalse((f.kit / "o/off.prepared-cache.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
