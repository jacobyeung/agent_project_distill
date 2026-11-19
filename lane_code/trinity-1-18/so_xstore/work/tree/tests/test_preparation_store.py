"""Store/recorder unit tests. These are not native adoption/loss proofs."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from student_pilot.preparation_reads import Recorder, UnkeyedRead, canonical, digest
from student_pilot.preparation_store import Store, StoreRefused, compare, receipt, SCHEMA


class ScratchTest(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"TK_XSTORE_EXPERIMENT": "1"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.root = Path(tempfile.mkdtemp(prefix="store_", dir=os.environ["LANE_TEST_OUTPUT"]))

    def store(self, name="store"):
        return Store(self.root / name, create=True)

    def build(self, name="store", raw=b"native-shaped fixture rows", key=None):
        store = self.store(name)
        payload = store.put_bytes(raw)
        meta = store.put_bytes(receipt({"schema": "fixture-content-v1", "rows": {"object": payload["sha256"]}}), kind="receipt")
        key = key or digest({"fixture_input": "same"})
        root = store.publish(key, [{"name": "rows.bin", **payload}, {"name": "receipt.json", **meta}])
        return store, root, key


class RecorderTests(ScratchTest):
    def test_nested_get_membership_iteration_lists_and_absence_are_recorded(self):
        def read(r):
            c = r.config
            return (c["seed"], c.get("nested")["x"], "optional" in c,
                    c.get("missing", 4), list(c["sequence"]), list(c["nested"].items()))
        cfg = {"seed": 17, "nested": {"x": 2}, "sequence": [1, 2]}
        first = Recorder(cfg)
        a = read(first)
        second = Recorder(cfg, expected=first.finish())
        self.assertEqual(a, read(second))
        self.assertEqual(first.key, second.key)

    def test_injected_unkeyed_config_read_is_refused(self):
        first = Recorder({"seed": 17, "injected": 3})
        self.assertEqual(first.config["seed"], 17)
        second = Recorder({"seed": 17, "injected": 3}, expected=first.finish())
        self.assertEqual(second.config["seed"], 17)
        with self.assertRaisesRegex(UnkeyedRead, "Unkeyed"):
            second.config["injected"]

    def test_consumed_field_change_refuses_replay(self):
        first = Recorder({"filter": {"minimum": 1}})
        first.config["filter"]["minimum"]
        second = Recorder({"filter": {"minimum": 2}}, expected=first.finish())
        with self.assertRaisesRegex(UnkeyedRead, "changed read"):
            second.config["filter"]["minimum"]

    def test_unused_field_does_not_enter_key(self):
        keys = []
        for value in (1, 2):
            r = Recorder({"seed": 17, "unused": value})
            r.config["seed"]
            keys.append(r.key)
        self.assertEqual(*keys)

    def test_excluded_fields_refuse_get_contains_iteration_and_unpacking(self):
        for key in ("output", "run_key", "preparation_output"):
            for read in (lambda c, k: c[k], lambda c, k: c.get(k),
                         lambda c, k: k in c, lambda c, k: list(c),
                         lambda c, k: dict(c), lambda c, k: {**c}):
                with self.subTest(key=key, read=read), self.assertRaises(UnkeyedRead):
                    read(Recorder({key: "run-specific"}).config, key)

    def test_absent_read_becoming_present_refuses(self):
        a = Recorder({})
        self.assertFalse("optional" in a.config)
        b = Recorder({"optional": 1}, expected=a.finish())
        with self.assertRaises(UnkeyedRead):
            "optional" in b.config

    def test_unconsumed_planned_read_refuses(self):
        a = Recorder({"seed": 17})
        a.config["seed"]
        with self.assertRaisesRegex(UnkeyedRead, "exact planned read set"):
            Recorder({"seed": 17}, expected=a.finish()).finish()

    def test_file_byte_change_and_undeclared_file_refuse(self):
        path = self.root / "input"
        path.write_bytes(b"A")
        a = Recorder({}, files={"rows": path})
        self.assertEqual(a.read_file("rows"), b"A")
        path.write_bytes(b"B")
        with self.assertRaises(UnkeyedRead):
            Recorder({}, files={"rows": path}, expected=a.finish()).read_file("rows")
        with self.assertRaises(UnkeyedRead):
            Recorder({}).read_file("injected")

    def test_file_locations_are_not_keyed(self):
        a, b = self.root / "a", self.root / "b"
        a.write_bytes(b"same")
        b.write_bytes(b"same")
        keys = []
        for path in (a, b):
            r = Recorder({}, files={"input": path})
            r.read_file("input")
            keys.append(r.key)
        self.assertEqual(*keys)

    def test_declared_environment_change_and_unknown_environment_refuse(self):
        a = Recorder({}, environment={"SEED": "17"})
        a.environment("SEED")
        with self.assertRaises(UnkeyedRead):
            Recorder({}, environment={"SEED": "18"}, expected=a.finish()).environment("SEED")
        with self.assertRaises(UnkeyedRead):
            Recorder({}).environment("INJECTED")

    def test_raw_python_file_read_is_refused(self):
        path = self.root / "input"
        path.write_bytes(b"key me")
        r = Recorder({}, files={"rows": path})
        with r.python_io_guard():
            self.assertEqual(r.read_file("rows"), b"key me")
            with self.assertRaisesRegex(UnkeyedRead, "Raw I/O"):
                path.read_bytes()

    def test_raw_sqlite_connection_is_refused(self):
        with Recorder({}).python_io_guard():
            with self.assertRaisesRegex(UnkeyedRead, "sqlite3.connect"):
                sqlite3.connect(":memory:")

    def test_source_file_change_changes_key(self):
        p = self.root / "producer.py"
        keys = []
        for body in (b"x=1", b"x=2"):
            p.write_bytes(body)
            r = Recorder({}, files={"code/producer.py": p})
            r.read_file("code/producer.py")
            keys.append(r.key)
        self.assertNotEqual(*keys)

    def test_default_switch_is_off(self):
        with patch.dict(os.environ, {"TK_XSTORE_EXPERIMENT": "0"}):
            with self.assertRaises(ValueError):
                Recorder({})


class ObjectStoreTests(ScratchTest):
    def test_full_graph_verifies_and_materializes_privately(self):
        s, root, key = self.build()
        value, telemetry = s.verify(root, expected_key=key)
        self.assertEqual(telemetry["object_count"], 2)
        self.assertEqual(value["key"], key)
        s.materialize_private(root, expected_key=key, directory=self.root / "private")
        self.assertEqual((self.root / "private/rows.bin").read_bytes(), b"native-shaped fixture rows")
        self.assertFalse((self.root / "private/data_receipt.json").exists())

    def test_corrupted_prepared_object_refuses(self):
        s, root, key = self.build()
        value, _ = s.verify(root, expected_key=key)
        obj = next(e for e in value["objects"] if e["kind"] == "bytes")
        (s.path / "objects" / obj["sha256"]).write_bytes(b"X" * obj["bytes"])
        with self.assertRaisesRegex(StoreRefused, "object_hash_mismatch"):
            s.verify(root, expected_key=key)

    def test_missing_object_refuses(self):
        s, root, key = self.build()
        value, _ = s.verify(root, expected_key=key)
        path = s.path / "objects" / value["objects"][0]["sha256"]
        path.rename(s.path / "temporary/retained-missing-object")
        with self.assertRaisesRegex(StoreRefused, "missing_or_linked_object"):
            s.verify(root, expected_key=key)

    def test_partial_root_refuses(self):
        s, root, key = self.build()
        (s.path / "roots" / (root + ".json")).write_bytes(b'{"schema":')
        with self.assertRaisesRegex(StoreRefused, "root_hash_mismatch"):
            s.verify(root, expected_key=key)

    def test_foreign_key_refuses(self):
        s, root, _ = self.build()
        with self.assertRaisesRegex(StoreRefused, "foreign_key"):
            s.verify(root, expected_key=digest({"different_input": True}))

    def test_incomplete_graph_cannot_publish_root(self):
        s = self.store()
        obj = s.put_bytes(receipt({"child": {"object": "a" * 64}}), kind="receipt")
        with self.assertRaisesRegex(StoreRefused, "incomplete_object_graph"):
            s.publish("b" * 64, [{"name": "receipt.json", **obj}])
        self.assertEqual(list((s.path / "roots").iterdir()), [])

    def test_missing_payload_cannot_publish_root(self):
        s = self.store()
        with self.assertRaises(StoreRefused):
            s.publish("b" * 64, [{"name": "rows", "sha256": "a" * 64, "bytes": 10, "kind": "bytes"}])
        self.assertEqual(list((s.path / "roots").iterdir()), [])

    def test_interrupted_root_rename_does_not_publish(self):
        s = self.store()
        obj = s.put_bytes(b"rows")
        with patch("student_pilot.preparation_store.os.rename", side_effect=OSError("interrupted")):
            with self.assertRaises(OSError):
                s.publish("b" * 64, [{"name": "rows", **obj}])
        self.assertEqual(list((s.path / "roots").iterdir()), [])

    def test_object_symlink_refuses(self):
        s, root, key = self.build()
        value, _ = s.verify(root, expected_key=key)
        p = s.path / "objects" / value["objects"][0]["sha256"]
        saved = s.path / "temporary/retained-link-target"
        p.rename(saved)
        p.symlink_to(saved)
        with self.assertRaises(StoreRefused):
            s.verify(root, expected_key=key)

    def test_linked_store_directory_refuses(self):
        s, _, _ = self.build()
        alias = self.root / "alias"
        alias.symlink_to(s.path, target_is_directory=True)
        with self.assertRaisesRegex(StoreRefused, "linked_directory"):
            Store(alias)

    def test_shared_writable_store_refuses(self):
        s, _, _ = self.build()
        s.path.chmod(0o770)
        with self.assertRaisesRegex(StoreRefused, "untrusted_store_directory"):
            Store(s.path)

    def test_duplicate_and_traversal_names_refuse(self):
        s = self.store()
        obj = s.put_bytes(b"rows")
        for names in (("../escape",), ("/absolute",), ("a//b",), ("a/./b",), ("x", "x"), ("x", "x/y")):
            with self.subTest(names=names), self.assertRaises(StoreRefused):
                s.publish("b" * 64, [{"name": name, **obj} for name in names])

    def test_native_receipts_are_rejected_instead_of_normalized(self):
        for value in ({"path": "/run/abc"}, {"inventory": "/run/abc"}, {"resources": {}},
                      {"host": "node-a"}, {"timestamp": "today"}, {"uuid": "abc"}, {"seconds": 1}):
            with self.subTest(value=value), self.assertRaises(StoreRefused):
                receipt(value)

    def test_native_admission_objects_cannot_be_published(self):
        s = self.store()
        obj = s.put_bytes(b"foreign admission")
        for name in ("request.json", "data_receipt.json", "nested/data_receipt.json", "phase_prepare.complete.json"):
            with self.subTest(name=name), self.assertRaisesRegex(StoreRefused, "native_admission_name_refused"):
                s.publish("b" * 64, [{"name": name, **obj}])
        self.assertEqual(list((s.path / "roots").iterdir()), [])

    def test_materialization_preserves_existing_native_destination(self):
        s, root, key = self.build()
        directory = self.root / "native"
        directory.mkdir(mode=0o700)
        marker = directory / "phase_prepare.complete.json"
        marker.write_bytes(b"native journal")
        with self.assertRaises(FileExistsError):
            s.materialize_private(root, expected_key=key, directory=directory)
        self.assertEqual(marker.read_bytes(), b"native journal")

    def test_materialization_rehashes_bytes_after_verify(self):
        s, root, key = self.build()
        real = s.verify
        def changed(*a, **kw):
            value, meta = real(*a, **kw)
            e = value["objects"][0]
            (s.path / "objects" / e["sha256"]).write_bytes(b"X" * e["bytes"])
            return value, meta
        with patch.object(s, "verify", side_effect=changed):
            with self.assertRaisesRegex(StoreRefused, "object_hash_mismatch"):
                s.materialize_private(root, expected_key=key, directory=self.root / "partial")
        self.assertFalse((self.root / "partial/data_receipt.json").exists())

    def test_determinism_compares_every_entry_without_normalization(self):
        a, ar, key = self.build("a")
        b, br, _ = self.build("b")
        self.assertEqual(compare(a, ar, b, br, key=key)["status"], "IDENTICAL")
        c, cr, _ = self.build("c", raw=b"different rows", key=key)
        with self.assertRaisesRegex(StoreRefused, "determinism_difference"):
            compare(a, ar, c, cr, key=key)

    def test_host_and_tmpdir_do_not_enter_fixture_root(self):
        with patch.dict(os.environ, {"HOSTNAME": "node-a", "TMPDIR": str(self.root / "tmp-a")}):
            _, a, _ = self.build("a")
        with patch.dict(os.environ, {"HOSTNAME": "node-b", "TMPDIR": str(self.root / "tmp-b")}):
            _, b, _ = self.build("b")
        self.assertEqual(a, b)

    def test_hashes_alone_are_not_producer_authentication(self):
        # This is a negative admission result, not an adopter acceptance test.
        a, ar, key = self.build("a")
        b, br, _ = self.build("forged", raw=b"not produced by native code", key=key)
        a.verify(ar, expected_key=key)
        b.verify(br, expected_key=key)
        self.assertNotEqual(ar, br)

    def test_default_switch_is_off(self):
        with patch.dict(os.environ, {"TK_XSTORE_EXPERIMENT": "0"}):
            with self.assertRaisesRegex(StoreRefused, "switch_off"):
                Store(self.root / "off", create=True)
        self.assertFalse((self.root / "off").exists())


if __name__ == "__main__":
    unittest.main()
