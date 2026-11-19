import copy
import hashlib
import json
import os
import subprocess
import tempfile
import threading
import time
import types
import unittest
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from student_pilot import common, orchard_paths, provisional, provisional_data, storage


BASE = "ad42813188224c367d7b49393f840a1e97f8fce7"
LABEL = "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW"


def baseline(name):
    source = subprocess.run(["git", "show", f"{BASE}:student_pilot/{name}.py"], cwd=common.REPO,
                            check=True, capture_output=True, text=True).stdout
    module = types.ModuleType(f"student_pilot._stagefast_baseline_{name}")
    module.__package__ = "student_pilot"
    module.__file__ = str(common.REPO / "student_pilot" / f"{name}.py")
    exec(compile(source, f"{BASE}:{name}.py", "exec"), module.__dict__)
    return module


class StagefastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(os.environ["LANE_TEST_OUTPUT"])
        root.mkdir(parents=True, exist_ok=True)
        cls.fixture = Path(tempfile.mkdtemp(prefix="stagefast_pool_", dir=root))
        cls.original_paths = baseline("orchard_paths")
        cls.original_common = baseline("common")
        cls.original_common.resolve_read = cls.original_paths.resolve_read
        cls.original_lane = baseline("finetune_lane")
        cls.original_lane.resolve_read = cls.original_paths.resolve_read
        cls.original = baseline("provisional")
        cls.original.binding = cls.original_common.binding
        cls.original.checked_payload = cls.original_lane.checked_payload
        cls.original_storage = baseline("storage")
        cls.original_storage.resolve_read = cls.original_paths.resolve_read
        cls.original_storage.binding = cls.original_common.binding
        cls.frames = []
        for index in range(64):
            path = cls.fixture / f"rgb_{index:03d}.bin"
            path.write_bytes(f"synthetic RGB frame {index}".encode() * 16)
            cls.frames.append(common.binding(path))
        cls.entries = []
        for index in range(320):
            qid = f"fixture_{319 - index:04d}"
            row = {"qid": qid, "dataset": "scannet", "scene": f"scene{index // 2:04d}_{index % 2:02d}",
                   "category": "object_counting", "target": "Synthetic evidence. <answer>2</answer>",
                   "generation_commit": "a" * 40, "validation_commit": "b" * 40,
                   "student_input": {"question": "Synthetic count?", "options": ["1", "2"],
                                     "frames": cls.frames[(index % 2) * 32:(index % 2 + 1) * 32],
                                     "frame_indices": list(range(32)), "timestamps": [i / 2 for i in range(32)],
                                     "fps": 2.0, "total_num_frames": 32}}
            row_path = cls.fixture / f"row_{index:04d}.json"
            row_path.write_bytes(common.canonical_bytes(row))
            target = cls.fixture / f"target_{index:04d}.txt"
            target.write_text(row["target"] + "\n")
            cls.entries.append({"qid": qid, "dataset": row["dataset"], "scene": row["scene"],
                                "question_type": row["category"], "answer": "2", "pool": "synthetic",
                                "target_path": str(target), "sha256": common.binding(target)["sha256"],
                                "row_path": str(row_path), "row_sha256": common.binding(row_path)["sha256"],
                                "generation_commit": row["generation_commit"], "validation_commit": row["validation_commit"]})
        cls.index = cls.fixture / "candidate_index.jsonl"
        cls.index.write_text("".join(json.dumps(entry) + "\n" for entry in cls.entries))

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="stagefast_case_", dir=os.environ["LANE_TEST_OUTPUT"]))
        self.context = ExitStack()
        self.addCleanup(self.context.close)
        self.context.enter_context(patch.dict(os.environ, STUDENT_ORCHARD="0", STUDENT_FRAME_ROOT_MAP=""))
        for module in (storage, self.original_storage):
            self.context.enter_context(patch.object(module, "SCRATCH_HOME", self.root))
            self.context.enter_context(patch.object(module, "ensure_free_space"))

    def load(self, threads, index=None):
        with patch.dict(os.environ, STUDENT_IO_THREADS=str(threads)):
            return provisional.load_provisional_candidates(index or self.index, LABEL)

    def write_index(self, entries, name="index.jsonl"):
        path = self.root / name
        path.write_text("".join(json.dumps(entry) + "\n" for entry in entries))
        return path

    def replace_row(self, entries, position, row, name):
        path = self.root / name
        path.write_bytes(common.canonical_bytes(row))
        entries[position].update(row_path=str(path), row_sha256=common.binding(path)["sha256"])

    def error(self, function, *args):
        try:
            function(*args)
        except Exception as error:
            return type(error).__name__, str(error)
        self.fail("Expected the serial validation error")

    def check_errors(self, index):
        expected = self.error(self.original.load_provisional_candidates, index, LABEL)
        for threads in (1, 32):
            with self.subTest(threads=threads):
                self.assertEqual(expected, self.error(self.load, threads, index))
        return expected

    def quarantine(self, path, name):
        destination = self.root / "_quarantine"
        destination.mkdir(exist_ok=True)
        path.rename(destination / name)

    def test_rows_division_and_training_manifest_match_base(self):
        expected = self.original.load_provisional_candidates(self.index, LABEL)
        self.assertEqual(len(expected), 320)
        division = self.original.division_candidates(expected, LABEL)
        for threads in (1, 32):
            with self.subTest(threads=threads):
                rows = self.load(threads)
                self.assertEqual(common.canonical_bytes(expected), common.canonical_bytes(rows))
                self.assertEqual(division, provisional.division_candidates(rows, LABEL))
                self.assertEqual([row["qid"] for row in rows], sorted(entry["qid"] for entry in self.entries))
        protocol = {"candidate_source": common.binding(self.index), **division,
                    "candidate_census": [{"qid": row["qid"], "row_sha256": common.digest_json(row)} for row in expected]}
        protocol_path = self.root / "protocol.json"
        protocol_path.write_bytes(common.canonical_bytes(protocol))
        rows = [row for row in expected if row["qid"] in protocol["division"]["train_candidate_qids"]]
        audits = [{"qid": row["qid"], "frame_count": 32, "assistant_tokens_including_eos": 8, "prompt_tokens": 16}
                  for row in rows]
        manifest = provisional.tag({"schema": "provisional-diagnostic-training-manifest-v1",
                                   "protocol": common.binding(protocol_path), "candidate_source": protocol["candidate_source"],
                                   "PROVISIONAL_DIVISION_SHA": protocol["PROVISIONAL_DIVISION_SHA"], "rows": rows,
                                   "input_audits": audits, "pre_evaluation_drops": [], "accepted_before_token_limits": len(rows),
                                   "counts": provisional_data.training_counts(rows, audits), "training_ready": True}, LABEL)
        manifest_path = self.root / "training.json"
        manifest_path.write_bytes(common.canonical_bytes(manifest))
        with patch.object(provisional_data, "load_protocol", return_value=protocol):
            for threads in (1, 32):
                with patch.dict(os.environ, STUDENT_IO_THREADS=str(threads)):
                    actual = provisional_data.load_training(manifest_path, LABEL)
                    self.assertEqual(common.canonical_bytes(actual), manifest_path.read_bytes())

    def test_frozen_protocol_and_prepared_training_bytes_match_between_thread_counts(self):
        from student_pilot import ddp_config, diagnostic_data
        from student_pilot.students import get_student

        marker = self.root / "synthetic_checkpoint.json"
        marker.write_text('{"synthetic":true}\n')
        base = {"revision": get_student("qwen35")["snapshot"].name,
                "files": [common.binding(marker)], "weight_shards": []}
        config_path = self.root / "training_config.json"
        config_path.write_text('{"world_size":8}\n')
        protocol_path, training_path = self.root / "protocol.json", self.root / "training.json"
        results = []

        def encode(processor, row):
            return {}, {"qid": row["qid"], "frame_count": 32, "assistant_tokens_including_eos": 10, "prompt_tokens": 20}

        with patch.object(diagnostic_data, "checkpoint_bindings", return_value=base), \
                patch.object(diagnostic_data, "versions", return_value={"synthetic_cpu_fixture": True}), \
                patch.object(storage, "code_provenance", side_effect=lambda value: {
                    "commit": BASE, "dirty": False, "config_sha256": common.digest_json(value),
                    "recorded_at": "2026-09-26T00:00:00+00:00"}), \
                patch("student_pilot.batches.load_processor", return_value=object()), \
                patch.object(diagnostic_data, "target_tokens", return_value=10), \
                patch.object(diagnostic_data, "encode_training", side_effect=encode):
            for threads in (1, 32):
                with patch.dict(os.environ, STUDENT_IO_THREADS=str(threads)):
                    provisional_data.prepare_protocol(self.index, protocol_path, LABEL, student="qwen35",
                                                      scratch_root=self.root, training_config=config_path)
                    provisional_data.prepare_training(protocol_path, training_path, LABEL, scratch_root=self.root)
                    loaded = provisional_data.load_training(training_path, LABEL)
                    self.assertEqual(common.canonical_bytes(loaded), training_path.read_bytes())
                    protocol = provisional_data.load_protocol(protocol_path, LABEL)
                    self.assertEqual(protocol["training_sha256"],
                                     common.digest_json(ddp_config.normalize_training_config({"world_size": 8}, "qwen35")))
                    results.append((protocol_path.read_bytes(), training_path.read_bytes()))
                self.quarantine(protocol_path, f"protocol_{threads}.json")
                self.quarantine(training_path, f"training_{threads}.json")
        self.assertEqual(results[0], results[1])

    def test_training_hash_and_epoch_rank_slots_match_base(self):
        from student_pilot import ddp_config, ddp_core

        original_config, original_core = baseline("ddp_config"), baseline("ddp_core")
        expected = self.original.load_provisional_candidates(self.index, LABEL)[:313]
        for threads in (1, 32):
            with patch.dict(os.environ, STUDENT_IO_THREADS=str(threads)):
                rows = self.load(threads)[:313]
                for world in (2, 8, 16, 32):
                    settings = ddp_config.normalize_training_config({"world_size": world}, "qwen35")
                    old_settings = original_config.normalize_training_config({"world_size": world}, "qwen35")
                    self.assertEqual(common.digest_json(settings), common.digest_json(old_settings))
                    for epoch in range(3):
                        batches = list(ddp_core.global_batches(len(rows), epoch))
                        old_batches = list(original_core.global_batches(len(expected), epoch))
                        self.assertEqual(batches, old_batches)
                        for batch in batches:
                            for rank in range(world):
                                slots = ddp_core.rank_slots(batch["indices"], rank, world, 1)
                                old_slots = original_core.rank_slots(batch["indices"], rank, world, 1)
                                self.assertEqual([(rows[index]["qid"], weight) for index, weight in slots],
                                                 [(expected[index]["qid"], weight) for index, weight in old_slots])

    def test_inline_and_embedded_rows_preserve_paths_and_bytes(self):
        entries = copy.deepcopy(self.entries[:6])
        for position, entry in enumerate(entries):
            row = json.loads(Path(entry["row_path"]).read_bytes())
            del entry["row_path"], entry["row_sha256"]
            if position % 2:
                entry.update(student_input=row["student_input"], target=row["target"], category=row["category"])
            else:
                path = self.root / f"embedded_{position}.json"
                path.write_bytes(common.canonical_bytes(row))
                entry.update(target_path=path.name, sha256=common.binding(path)["sha256"])
        index = self.write_index(entries)
        expected = self.original.load_provisional_candidates(index, LABEL)
        self.assertEqual(expected, self.load(1, index))
        self.assertEqual(expected, self.load(32, index))

    def test_first_corrupt_target_row_and_frame_matches_base(self):
        for order in (("target", "row", "frame"), ("row", "frame", "target"), ("frame", "target", "row")):
            entries = copy.deepcopy(self.entries)
            for position, kind in zip((3, 67, 251), order):
                path = self.root / f"{order[0]}_{kind}.bin"
                path.write_bytes(b"corrupt bytes")
                if kind == "frame":
                    row = json.loads(Path(entries[position]["row_path"]).read_bytes())
                    row["student_input"]["frames"][4]["path"] = str(path)
                    self.replace_row(entries, position, row, f"{order[0]}_frame_row.json")
                else:
                    entries[position]["target_path" if kind == "target" else "row_path"] = str(path)
            with self.subTest(order=order):
                error = self.check_errors(self.write_index(entries, f"{order[0]}.jsonl"))
                self.assertIn(str(self.root / f"{order[0]}_{order[0]}.bin"), error[1])

    def test_validation_errors_precede_prefetched_io_errors(self):
        cases = []
        entries = copy.deepcopy(self.entries[:4])
        entries[0]["answer"] = None
        entries[0]["sha256"] = "0" * 64
        cases.append(entries)
        entries = copy.deepcopy(self.entries[:4])
        row = json.loads(Path(entries[0]["row_path"]).read_bytes())
        row["provisional_diagnostic"] = provisional.LABELS[1]
        self.replace_row(entries, 0, row, "wrong_label.json")
        entries[1]["sha256"] = "0" * 64
        cases.append(entries)
        entries = copy.deepcopy(self.entries[:4])
        row = json.loads(Path(entries[0]["row_path"]).read_bytes())
        row["student_input"]["frames"][0]["sha256"] = "0" * 64
        row["student_input"]["frames"][-1]["path"] = str(self.root / "offline_labels/frame.bin")
        self.replace_row(entries, 0, row, "protected_frame.json")
        cases.append(entries)
        entries = copy.deepcopy(self.entries[:4])
        entries[1]["qid"] = entries[0]["qid"]
        entries[1]["row_path"] = str(self.root / "missing.json")
        cases.append(entries)
        for number, entries in enumerate(cases):
            with self.subTest(number=number):
                self.check_errors(self.write_index(entries, f"validation_{number}.jsonl"))

    def test_staged_rows_and_receipt_files_match_base_exactly(self):
        rows = self.load(1)
        before = copy.deepcopy(rows)
        config = {"student": "qwen35", "PROVISIONAL_DIVISION_SHA": "f" * 64, **provisional.flags(LABEL)}
        output = self.root / "run"
        provenance = {"commit": BASE, "dirty": False, "config_sha256": common.digest_json(config),
                      "recorded_at": "2026-09-26T00:00:00+00:00"}
        results = []
        for number, (module, threads) in enumerate(((self.original_storage, 1), (storage, 1), (storage, 32))):
            with patch.dict(os.environ, STUDENT_IO_THREADS=str(threads)), \
                    patch.object(module, "code_provenance", return_value=provenance):
                store = module.RunArtifacts(output, config, self.root)
                staged = module.localize_frames(rows, store, self.index, self.root, stage=True)
                results.append((common.canonical_bytes(staged),
                                (output / "frame_staging.json").read_bytes(),
                                (output / "input_manifest.json").read_bytes(),
                                (output / "frames/provenance.json").read_bytes()))
                for frame in staged[0]["student_input"]["frames"]:
                    self.assertEqual(common.binding(frame["path"]), frame)
                staged[0]["student_input"]["options"].append("not shared")
                staged[0]["candidate_provenance"]["target"]["path"] = "not shared"
                self.assertEqual(rows, before)
            self.quarantine(output, f"run_{number}")
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[0], results[2])

    def test_stage_first_errors_match_with_later_scan_failure(self):
        rows = self.load(1)[:4]
        rows[0]["student_input"]["frames"][0]["sha256"] = "0" * 64
        rows[2]["student_input"]["frames"][0]["sha256"] = "invalid"
        output = self.root / "frames"
        expected = self.error(self.original_storage.stage_frames, rows, output, self.root)
        for threads in (1, 32):
            with patch.dict(os.environ, STUDENT_IO_THREADS=str(threads)):
                self.assertEqual(expected, self.error(storage.stage_frames, rows, output, self.root))
        self.assertFalse(output.exists())

    def test_path_resolution_and_lstat_scale_with_unique_paths(self):
        real_resolve, real_lstat = Path.resolve, os.lstat
        observations = {}
        for threads in (1, 32):
            counts, lock = Counter(), threading.Lock()

            def resolve(path, *args, **kwargs):
                with lock:
                    counts["resolve"] += 1
                    counts[("resolve", str(path))] += 1
                return real_resolve(path, *args, **kwargs)

            def lstat(*args, **kwargs):
                with lock:
                    counts["lstat"] += 1
                return real_lstat(*args, **kwargs)

            with patch.object(Path, "resolve", resolve), patch.object(os, "lstat", lstat):
                self.load(threads)
            observations[threads] = counts
        slow, fast = observations[1], observations[32]
        self.assertEqual(fast["resolve"], 4 * (2 * len(self.entries) + len(self.frames)) + 2)
        self.assertGreater(slow["resolve"], fast["resolve"] * 7)
        self.assertGreater(slow["lstat"], fast["lstat"] * 7)
        for frame in self.frames:
            self.assertEqual(fast[("resolve", frame["path"])], 4)
        print(json.dumps({"stagefast_path_counts": {str(n): {k: v[k] for k in ("resolve", "lstat")}
                                                  for n, v in observations.items()}}, sort_keys=True))

    def test_parallel_payload_reads_speed_up_injected_latency(self):
        index = self.write_index(self.entries[:96])
        real_read = Path.read_bytes
        elapsed, results, peaks, lock = {}, {}, {}, threading.Lock()

        def slow_read(path):
            if not path.name.startswith(("row_", "target_")):
                return real_read(path)
            with lock:
                counts["active"] += 1
                counts["peak"] = max(counts["peak"], counts["active"])
            try:
                time.sleep(0.02)
                return real_read(path)
            finally:
                with lock:
                    counts["active"] -= 1

        with patch.object(Path, "read_bytes", slow_read):
            for threads in (1, 32):
                counts = Counter()
                started = time.perf_counter()
                results[threads] = self.load(threads, index)
                elapsed[threads] = time.perf_counter() - started
                peaks[threads] = counts["peak"]
        self.assertEqual(results[1], results[32])
        self.assertEqual(peaks[1], 1)
        self.assertGreaterEqual(peaks[32], 4)
        self.assertLessEqual(peaks[32], 32)
        print(json.dumps({"stagefast_payload_seconds": elapsed, "peak_reads": peaks,
                          "speedup": elapsed[1] / elapsed[32]}, sort_keys=True))
        self.assertLess(elapsed[32], elapsed[1] * 0.6)

    def test_parallel_staging_speed_and_hash_counts(self):
        rows = self.load(1)[:8]
        output = self.root / "frames"
        real_copy, real_sha = storage.copy_new, common.sha256
        elapsed, observations, results = {}, {}, {}
        for threads in (1, 32):
            counts, lock = Counter(), threading.Lock()

            def sha(*args, **kwargs):
                with lock:
                    counts["hashes"] += 1
                time.sleep(0.005)
                return real_sha(*args, **kwargs)

            def copy_frame(*args, **kwargs):
                time.sleep(0.02)
                return real_copy(*args, **kwargs)

            with patch.dict(os.environ, STUDENT_IO_THREADS=str(threads)), patch.object(common, "sha256", sha), \
                    patch.object(storage, "copy_new", copy_frame):
                started = time.perf_counter()
                results[threads] = storage.stage_frames(rows, output, self.root)
                elapsed[threads] = time.perf_counter() - started
            observations[threads] = counts["hashes"]
            self.quarantine(output, f"frames_{threads}")
        self.assertEqual(results[1], results[32])
        self.assertEqual(observations[1], 3 * len(self.frames))
        self.assertEqual(observations[32], 4 * len(self.frames))
        print(json.dumps({"stagefast_staging_seconds": elapsed, "hashes": observations,
                          "speedup": elapsed[1] / elapsed[32]}, sort_keys=True))
        self.assertLess(elapsed[32], elapsed[1] * 0.6)

    def test_mapped_paths_preserve_pins_and_detect_fresh_corruption_and_escape(self):
        project = self.root / "project"
        physical = project / "data2root/stagefast"
        physical.mkdir(parents=True)
        logical = Path("/data2/stagefast")
        pins = []
        for index, frame in enumerate(self.frames):
            path = physical / f"frame_{index}.bin"
            path.write_bytes(Path(frame["path"]).read_bytes())
            pins.append({"path": str(logical / path.name), "sha256": frame["sha256"]})
        entries = copy.deepcopy(self.entries[:12])
        for number, entry in enumerate(entries):
            row = json.loads(Path(entry["row_path"]).read_bytes())
            row["student_input"]["frames"] = pins[(number % 2) * 32:(number % 2 + 1) * 32]
            row_path = physical / f"row_{number}.json"
            target = physical / f"target_{number}.txt"
            row_path.write_bytes(common.canonical_bytes(row))
            target.write_text(row["target"] + "\n")
            entry.update(row_path=str(logical / row_path.name), row_sha256=common.binding(row_path)["sha256"],
                         target_path=str(logical / target.name), sha256=common.binding(target)["sha256"])
        index = self.write_index(entries)
        with patch.object(orchard_paths, "PROJECT", project), patch.object(self.original_paths, "PROJECT", project), \
                patch.dict(os.environ, STUDENT_ORCHARD="1", STUDENT_FRAME_ROOT_MAP=f"/data2={project}/data2root"):
            expected = self.original.load_provisional_candidates(index, LABEL)
            self.assertEqual(expected, self.load(1, index))
            self.assertEqual(expected, self.load(32, index))
            output, results = self.root / "staged", []
            for number, (module, threads) in enumerate(((self.original_storage, 1), (storage, 1), (storage, 32))):
                with patch.dict(os.environ, STUDENT_IO_THREADS=str(threads)):
                    results.append(common.canonical_bytes(module.stage_frames(expected, output, self.root)))
                self.quarantine(output, f"mapped_{number}")
            self.assertEqual(results[0], results[1])
            self.assertEqual(results[0], results[2])
            (physical / "frame_0.bin").write_bytes(b"corrupted between calls")
            self.assertIn("Hash mismatch", self.check_errors(index)[1])
            self.quarantine(physical / "frame_0.bin", "corrupt_mapped_frame")
            outside = self.root / "outside.bin"
            outside.write_bytes(b"outside owned mapping")
            (physical / "frame_0.bin").symlink_to(outside)
            self.assertIn("symlink escapes", self.check_errors(index)[1])
            for mapping in (f"/data2={self.root}", f"/unsupported={project}/data2root"):
                with patch.dict(os.environ, STUDENT_FRAME_ROOT_MAP=mapping):
                    self.check_errors(index)

    def test_malformed_payloads_and_row_paths_keep_exception_types_and_messages(self):
        for number, path in enumerate((None, [], {}, 7, str(self.root / "missing.json"))):
            entries = copy.deepcopy(self.entries[:3])
            entries[0]["row_path"] = path
            entries[1]["sha256"] = "0" * 64
            with self.subTest(path=path):
                self.check_errors(self.write_index(entries, f"bad_path_{number}.jsonl"))
        for number, payload in enumerate((b'{"qid":"a","qid":"b"}', b'{"value":NaN}', b"\xff", b"[1,2]")):
            entries = copy.deepcopy(self.entries[:3])
            path = self.root / f"malformed_{number}.json"
            path.write_bytes(payload)
            entries[0].update(row_path=str(path), row_sha256=hashlib.sha256(payload).hexdigest())
            entries[1]["sha256"] = "0" * 64
            with self.subTest(payload=payload):
                self.check_errors(self.write_index(entries, f"bad_payload_{number}.jsonl"))

    def test_malformed_frame_count_does_not_queue_frame_hashes(self):
        entries = copy.deepcopy(self.entries[:1])
        path = Path(entries[0]["row_path"])
        row = json.loads(path.read_bytes())
        row["student_input"]["frames"].append(self.frames[0])
        self.replace_row(entries, 0, row, "extra_frame.json")
        with patch.object(provisional, "binding", wraps=provisional.binding) as hashed:
            self.check_errors(self.write_index(entries))
        frame_paths = {frame["path"] for frame in self.frames}
        self.assertFalse(any(str(call.args[0]) in frame_paths for call in hashed.call_args_list))

    def test_rebuild_preserves_nested_values_and_aliases_without_copying_old_frames(self):
        inputs = {"frames": [self.frames[0], self.frames[1]], "options": ["a", "b"]}
        row = {"student_input": inputs, "input_alias": inputs, "frame_list_alias": inputs["frames"]}
        rows = (row, row, {"student_input": None, "nested": {"values": [1, 2]}})
        before, results = copy.deepcopy(rows), []
        output = self.root / "frames"
        for number, (module, threads) in enumerate(((self.original_storage, 1), (storage, 32))):
            with patch.dict(os.environ, STUDENT_IO_THREADS=str(threads)):
                staged, receipt = module.stage_frames(rows, output, self.root)
            self.assertIsInstance(staged, tuple)
            self.assertIs(staged[0], staged[1])
            self.assertIs(staged[0]["student_input"], staged[0]["input_alias"])
            self.assertIsNot(staged[0]["student_input"]["frames"], staged[0]["frame_list_alias"])
            self.assertEqual(rows, before)
            results.append(common.canonical_bytes((staged, receipt)))
            self.quarantine(output, f"aliases_{number}")
        self.assertEqual(results[0], results[1])

    def test_content_duplicates_keep_last_source_and_original_reference_order(self):
        alias = self.root / "same_frame.bin"
        alias.write_bytes(Path(self.frames[0]["path"]).read_bytes())
        pins = [self.frames[0], self.frames[1], common.binding(alias), self.frames[0]]
        rows = [{"student_input": {"frames": pins}}]
        output, results = self.root / "frames", []
        for number, (module, threads) in enumerate(((self.original_storage, 1), (storage, 32))):
            with patch.dict(os.environ, STUDENT_IO_THREADS=str(threads)):
                results.append(module.stage_frames(rows, output, self.root))
            self.quarantine(output, f"duplicates_{number}")
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[1][1]["source_references"],
                         [{**pin, "bytes": Path(pin["path"]).stat().st_size} for pin in pins[:3]])
        copied = next(item for item in results[1][1]["files"] if item["source"]["sha256"] == pins[0]["sha256"])
        self.assertEqual(copied["source"]["path"], str(alias))

    def test_copy_verification_and_directory_capacity_keep_first_error(self):
        buckets = {}
        for frame in self.frames:
            buckets.setdefault(frame["sha256"][:2], []).append(frame)
        collision = next(frames[:2] for frames in buckets.values() if len(frames) >= 2)
        rows = [{"student_input": {"frames": collision}}]
        output = self.root / "frames"
        for kind in ("capacity", "corrupt_copy"):
            results = []
            for number, (module, threads) in enumerate(((self.original_storage, 1), (storage, 1), (storage, 32))):
                with ExitStack() as stack:
                    stack.enter_context(patch.dict(os.environ, STUDENT_IO_THREADS=str(threads)))
                    if kind == "capacity":
                        stack.enter_context(patch.object(module, "MAX_DIRECTORY_FILES", 1))
                    else:
                        stack.enter_context(patch.object(module.shutil, "copyfileobj",
                                                        side_effect=lambda reader, writer, **kwargs: writer.write(b"bad copy")))
                    results.append(self.error(module.stage_frames, rows, output, self.root))
                self.quarantine(output, f"{kind}_{number}")
            self.assertEqual(results[0], results[1])
            self.assertEqual(results[0], results[2])

    def test_stage_resolver_calls_scale_with_unique_frames(self):
        rows = self.load(1)
        output, counts = self.root / "frames", {}
        original = storage.resolve_read
        for threads in (1, 32):
            with patch.dict(os.environ, STUDENT_IO_THREADS=str(threads)), \
                    patch.object(storage, "resolve_read", wraps=original) as resolver:
                storage.stage_frames(rows, output, self.root)
                counts[threads] = resolver.call_count
            self.quarantine(output, f"resolution_{threads}")
        self.assertEqual(counts[1], len(rows) * 32 + len(self.frames))
        self.assertEqual(counts[32], 5 * len(self.frames))
        print(json.dumps({"stagefast_stage_resolver_calls": counts}, sort_keys=True))

    def test_default_threads_and_per_call_caches(self):
        with patch.dict(os.environ, STUDENT_IO_THREADS="1"):
            self.assertEqual(common.io_threads(), 1)
        with patch.dict(os.environ):
            os.environ.pop("STUDENT_IO_THREADS", None)
            self.assertEqual(common.io_threads(), 32)
        for value in ("0", "-1", "bad"):
            with patch.dict(os.environ, STUDENT_IO_THREADS=value), self.assertRaises(ValueError):
                common.io_threads()
        calls, lock = Counter(), threading.Lock()

        def resolve(path):
            with lock:
                calls[path] += 1
            time.sleep(0.01)
            return Path(path)

        cached = common.memoize_io(resolve)
        with ThreadPoolExecutor(max_workers=32) as pool:
            self.assertEqual(list(pool.map(cached, ["same"] * 320)), [Path("same")] * 320)
        self.assertEqual(calls["same"], 1)
        self.assertEqual(common.memoize_io(resolve)("same"), Path("same"))
        self.assertEqual(calls["same"], 2)

    def test_ordered_prefetch_is_bounded_and_defers_iterator_errors(self):
        seen = []

        def items():
            for number in range(100):
                seen.append(number)
                yield number

        with ThreadPoolExecutor(max_workers=2) as pool:
            iterator = common.ordered_io(pool, lambda item: item, items(), 4)
            self.assertEqual(next(iterator), 0)
            self.assertEqual(len(seen), 4)
            self.assertEqual([0, *iterator], list(range(100)))

        def broken_items():
            yield 0
            raise ValueError("later iterator error")

        def broken_read(item):
            time.sleep(0.02)
            raise OSError("first I/O error")

        with ThreadPoolExecutor(max_workers=2) as pool:
            iterator = common.ordered_io(pool, broken_read, broken_items(), 4)
            self.assertEqual(self.error(next, iterator), ("OSError", "first I/O error"))

    def freshness_modes(self):
        return (("base", self.original, self.original_storage, self.original_paths),
                ("serial", provisional, storage, orchard_paths),
                ("default", provisional, storage, orchard_paths),
                ("parallel32", provisional, storage, orchard_paths))

    def freshness_threads(self, mode):
        if mode in ("base", "default"):
            os.environ.pop("STUDENT_IO_THREADS", None)
        else:
            os.environ["STUDENT_IO_THREADS"] = "1" if mode == "serial" else "32"

    def loader_freshness(self, scenario):
        observations = {}
        for mode, module, _, _ in self.freshness_modes():
            with self.subTest(mode=mode), patch.dict(os.environ):
                self.freshness_threads(mode)
                root = self.root / mode
                root.mkdir()
                frames = copy.deepcopy(self.frames[:32])
                alias = root / "alias.bin"
                alias.symlink_to(frames[0]["path"])
                frames[0]["path"] = str(alias)
                protected = root / "answer_bank_fixture"
                protected.mkdir()
                (protected / "frame.bin").write_bytes(alias.read_bytes())
                target = root / "target.txt"
                target.write_text("Synthetic evidence. <answer>2</answer>\n")
                entries = []
                for number in range(2):
                    entries.append({"qid": f"fresh_{number}", "dataset": "scannet", "scene": f"scene{number:04d}_00",
                                    "question_type": "object_counting", "category": "object_counting", "answer": "2",
                                    "pool": "synthetic", "generation_commit": "a" * 40, "validation_commit": "b" * 40,
                                    "target_path": str(target), "sha256": common.binding(target)["sha256"],
                                    "target": "Synthetic evidence. <answer>2</answer>",
                                    "student_input": {"question": "Synthetic count?", "options": ["1", "2"],
                                                      "frames": frames, "frame_indices": list(range(32)),
                                                      "timestamps": [i / 2 for i in range(32)], "fps": 2.0,
                                                      "total_num_frames": 32}})
                index = root / "index.jsonl"
                index.write_text("".join(json.dumps(entry) + "\n" for entry in entries))
                ready, lock = threading.Event(), threading.Lock()
                reads, changed = 0, False
                original_payload, original_tag = module.checked_payload, module.tag

                def payload(*args, **kwargs):
                    nonlocal reads
                    result = original_payload(*args, **kwargs)
                    if Path(args[0]) == target:
                        with lock:
                            reads += 1
                            if reads >= 2:
                                ready.set()
                    return result

                def tagged(value, label):
                    nonlocal changed
                    result = original_tag(value, label)
                    if value.get("qid") == "fresh_0" and not changed:
                        if scenario.startswith("prefetched_") and mode in ("default", "parallel32"):
                            self.assertTrue(ready.wait(10), "Both target payloads must be prefetched before mutation")
                        retained = root / "_quarantine"
                        retained.mkdir()
                        if scenario == "protected_alias_retarget":
                            alias.rename(retained / "alias.bin")
                            alias.symlink_to(protected / "frame.bin")
                        elif scenario == "prefetched_missing_target":
                            target.rename(retained / "target.txt")
                        else:
                            target.write_bytes(b"Changed synthetic target after first row validation\n")
                        changed = True
                    return result

                with patch.object(module, "checked_payload", side_effect=payload), patch.object(module, "tag", side_effect=tagged):
                    error = self.error(module.load_provisional_candidates, index, LABEL)
                observations[mode] = {"status": "error", "exception": error[0], "message": error[1]}
                self.assertTrue(changed)
                expected = "FileNotFoundError" if scenario == "prefetched_missing_target" else "ValueError"
                self.assertEqual(error[0], expected)
                if scenario == "protected_alias_retarget":
                    self.assertEqual(error[1], "Protected label/archive paths are not candidate inputs")
                elif scenario == "prefetched_changed_target":
                    self.assertEqual(error[1], f"SHA256 mismatch: {target}")
        print(json.dumps({"freshness_scenario": scenario, "outcomes": observations}, sort_keys=True))

    def test_within_call_protected_alias_retarget_is_rejected(self):
        self.loader_freshness("protected_alias_retarget")

    def test_within_call_prefetched_missing_target_is_rejected(self):
        self.loader_freshness("prefetched_missing_target")

    def test_within_call_prefetched_changed_target_is_rejected(self):
        self.loader_freshness("prefetched_changed_target")

    def test_within_call_mapped_stage_retarget_is_rejected(self):
        observations = {}
        for mode, _, module, paths in self.freshness_modes():
            with self.subTest(mode=mode), patch.dict(os.environ):
                self.freshness_threads(mode)
                root = self.root / mode
                project = root / "project"
                physical = project / "data2root" / "retarget"
                physical.mkdir(parents=True)
                outside = root / "outside.bin"
                outside.write_bytes(b"same synthetic bytes\n")
                original = physical / "valid.bin"
                original.write_bytes(outside.read_bytes())
                alias = physical / "alias.bin"
                alias.symlink_to(original)
                frame = {"path": "/data2/retarget/alias.bin", "sha256": common.binding(alias)["sha256"]}
                rows = [{"student_input": {"frames": [frame]}}]
                changed = False

                def retarget(*args, **kwargs):
                    nonlocal changed
                    retained = root / "_quarantine"
                    retained.mkdir()
                    alias.rename(retained / "alias.bin")
                    alias.symlink_to(outside)
                    changed = True

                with patch.object(module, "SCRATCH_HOME", root), patch.object(paths, "PROJECT", project), \
                        patch.dict(os.environ, STUDENT_ORCHARD="1", STUDENT_FRAME_ROOT_MAP=f"/data2={project}/data2root"), \
                        patch.object(module, "ensure_free_space", side_effect=retarget):
                    error = self.error(module.stage_frames, rows, root / "staged", root)
                observations[mode] = {"status": "error", "exception": error[0], "message": error[1]}
                self.assertTrue(changed)
                self.assertEqual(error, ("ValueError", "Mapped input symlink escapes its root"))
        print(json.dumps({"freshness_scenario": "mapped_stage_retarget", "outcomes": observations}, sort_keys=True))

    def test_within_call_removed_staged_destination_is_rejected(self):
        observations = {}
        for mode, _, module, _ in self.freshness_modes():
            with self.subTest(mode=mode), patch.dict(os.environ):
                self.freshness_threads(mode)
                root = self.root / mode
                root.mkdir()
                source = root / "source.bin"
                source.write_bytes(b"synthetic destination existence check\n")
                rows = [{"student_input": {"frames": [common.binding(source)]}}]
                original_copy = module.copy_new
                changed = False

                def move_destination(*args, **kwargs):
                    nonlocal changed
                    result = original_copy(*args, **kwargs)
                    retained = root / "_quarantine"
                    retained.mkdir()
                    Path(args[1]).rename(retained / "staged.bin")
                    changed = True
                    return result

                with patch.object(module, "SCRATCH_HOME", root), patch.object(module, "ensure_free_space"), \
                        patch.object(module, "copy_new", side_effect=move_destination):
                    error = self.error(module.stage_frames, rows, root / "staged", root)
                observations[mode] = {"status": "error", "exception": error[0], "message": error[1]}
                self.assertTrue(changed)
                self.assertEqual(error[0], "FileNotFoundError")
        print(json.dumps({"freshness_scenario": "removed_staged_destination", "outcomes": observations}, sort_keys=True))

    def single_fresh_row(self, root):
        root.mkdir()
        row = json.loads(Path(self.entries[0]["row_path"]).read_bytes())
        frame = root / "frame.bin"
        frame.write_bytes(Path(row["student_input"]["frames"][0]["path"]).read_bytes())
        row["student_input"]["frames"][0] = common.binding(frame)
        target = root / "target.txt"
        target.write_text(row["target"] + "\n")
        row_path = root / "row.json"
        row_path.write_bytes(common.canonical_bytes(row))
        entry = {**self.entries[0], "target_path": str(target), "sha256": common.binding(target)["sha256"],
                 "row_path": str(row_path), "row_sha256": common.binding(row_path)["sha256"]}
        index = root / "index.jsonl"
        index.write_text(json.dumps(entry) + "\n")
        return index, {"target": target, "row": row_path, "frame": frame}

    def test_final_loader_sweep_rehashes_targets_rows_and_frames(self):
        for threads in (2, 32):
            for kind in ("target", "row", "frame"):
                for mutation in ("missing", "changed"):
                    with self.subTest(threads=threads, kind=kind, mutation=mutation):
                        root = self.root / f"{threads}_{kind}_{mutation}"
                        index, paths = self.single_fresh_row(root)
                        path = paths[kind]
                        original_tag = provisional.tag

                        def tagged(value, label):
                            result = original_tag(value, label)
                            retained = root / "_quarantine"
                            retained.mkdir()
                            path.rename(retained / path.name)
                            if mutation == "changed":
                                path.write_bytes(b"Changed bytes after the final row validated\n")
                            return result

                        with patch.object(provisional, "tag", side_effect=tagged):
                            error = self.error(self.load, threads, index)
                        if mutation == "missing":
                            self.assertEqual(error[0], "FileNotFoundError")
                            self.assertIn(str(path), error[1])
                        else:
                            self.assertEqual(error, ("ValueError", f"SHA256 mismatch: {path}"))

    def test_final_loader_sweep_rejects_equal_byte_resolution_changes(self):
        for threads in (2, 32):
            with self.subTest(threads=threads):
                root = self.root / str(threads)
                index, paths = self.single_fresh_row(root)
                frame = paths["frame"]
                alternate = root / "permitted_alternate.bin"
                alternate.write_bytes(frame.read_bytes())
                original_tag = provisional.tag

                def tagged(value, label):
                    result = original_tag(value, label)
                    retained = root / "_quarantine"
                    retained.mkdir()
                    frame.rename(retained / "frame.bin")
                    frame.symlink_to(alternate)
                    return result

                with patch.object(provisional, "tag", side_effect=tagged):
                    error = self.error(self.load, threads, index)
                self.assertEqual(error, ("ValueError", f"Path resolution changed during validation: {frame}"))

    def test_final_stage_checks_uncopied_sources_and_copied_destinations(self):
        for threads in (2, 32):
            for kind in ("source", "destination"):
                for mutation in ("missing", "changed"):
                    with self.subTest(threads=threads, kind=kind, mutation=mutation):
                        root = self.root / f"{threads}_{kind}_{mutation}"
                        root.mkdir()
                        sources = [root / name for name in ("uncopied.bin", "copied.bin")]
                        for source in sources:
                            source.write_bytes(b"Equal-content distinct synthetic sources\n")
                        rows = [{"student_input": {"frames": [common.binding(source) for source in sources]}}]
                        original_copy = storage.copy_new
                        changed = []

                        def copy_frame(*args, **kwargs):
                            result = original_copy(*args, **kwargs)
                            self.assertEqual(Path(args[0]), sources[1])
                            path = sources[0] if kind == "source" else Path(args[1])
                            retained = root / "_quarantine"
                            retained.mkdir()
                            path.rename(retained / "original.bin")
                            if mutation == "changed":
                                path.write_bytes(b"Changed bytes after copying\n")
                            changed.append(path)
                            return result

                        with patch.dict(os.environ, STUDENT_IO_THREADS=str(threads)), \
                                patch.object(storage, "copy_new", side_effect=copy_frame):
                            error = self.error(storage.stage_frames, rows, root / "staged", self.root)
                        self.assertEqual(len(changed), 1)
                        if mutation == "missing":
                            self.assertEqual(error[0], "FileNotFoundError")
                            self.assertIn(str(changed[0]), error[1])
                        else:
                            prefix = "SHA256 mismatch: " if kind == "source" else "Hash mismatch for "
                            self.assertEqual(error, ("ValueError", prefix + str(changed[0])))

    def test_freshness_verifier_uses_uncached_guards_once_per_path(self):
        calls, current = [], [Path("same")]

        def uncached(path):
            calls.append((str(path), threading.get_ident()))
            if isinstance(current[0], Exception):
                raise current[0]
            return current[0]

        cached = common.memoize_io(lambda path: Path(path), uncached=uncached)
        for _ in range(32):
            self.assertEqual(cached("same"), cached(Path("same")))
        with ThreadPoolExecutor(max_workers=2) as pool:
            cached.verify(pool, 4)
            self.assertEqual(len(calls), 1)
            self.assertNotEqual(calls[0][1], threading.get_ident())
            current[0] = Path("different")
            with self.assertRaisesRegex(ValueError, "^Path resolution changed during validation: same$"):
                cached.verify(pool, 4)
            current[0] = FileNotFoundError("original uncached guard failure")
            with self.assertRaises(FileNotFoundError) as failure:
                cached.verify(pool, 4)
            self.assertIs(failure.exception, current[0])
        self.assertEqual(len(calls), 3)


if __name__ == "__main__":
    unittest.main()
