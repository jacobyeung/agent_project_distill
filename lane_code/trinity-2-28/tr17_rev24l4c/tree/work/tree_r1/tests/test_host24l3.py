"""CPU staging branch fixtures; the kit archive descriptor uses synthetic hashes."""
import base64
from copy import deepcopy
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

from launch_r1 import entry, production_proof as proof
from student_pilot.p3_provenance import digest, encoded, load, pinned, sha256
from student_pilot.r1_persisted import scope
from tests import test_host24l as previous


class StagerBranches(unittest.TestCase):
    setUp = previous.Host24L.setUp
    pin = previous.Host24L.pin
    fixture = previous.Host24L.fixture
    dependencies = previous.Host24L.dependencies
    run_q = previous.Host24L.run_q
    host = previous.Host24L.host
    refused = previous.Host24L.refused
    repin = previous.Host24L.repin
    archive_fixture = previous.Host24L.archive_fixture

    def assert_plan_hash(self, host, request):
        with scope(self.paths):
            expected = sha256(pinned(request['staging']))
        self.assertEqual(host['staging_plan_sha256'], expected)
        self.assertEqual(expected, request['staging']['sha256'])

    def kit_fixture(self):
        cfg, request = self.fixture()
        # Match pl.py's direct-file parts and e archive/receipt-label inventory.
        copies = {}
        for name, item in self.entries.items():
            raw = base64.b64decode(item['payload'])
            copies[name] = raw
            self.entries[name] = dict(sha256=item['sha256'], parts=[str(self.root/name)], bytes=len(raw))
        for name, raw in [('n.json', b'{}\n'), ('source_code.json', b'{}\n'), ('f/weights.bin', b'fixture')]:
            copies[name] = raw
            self.entries[name] = dict(sha256=hashlib.sha256(raw).hexdigest(),
                                      parts=[str(self.root/name)], bytes=len(raw))
        self.entries['e'] = dict(archive=dict(sha256='0'*64, bytes=1,
            parts=[dict(sha256='1'*64, bytes=1)]), inventory={'artifact': '2'*64})
        plan = dict(entries=self.entries)
        # The outer capsule hash differs from the decoded plan digest.
        raw = encoded(plan).encode()
        capsule = dict(encoding='base64-json', payload=base64.b64encode(raw).decode(),
                       sha256=hashlib.sha256(raw).hexdigest())
        request['staging'] = self.pin('kit_stage.json', capsule)
        expected_entries = deepcopy(self.entries)
        calls = []
        def stage(entries, root):
            self.assertEqual(entries, expected_entries)
            calls.append(root)
            for name, payload in copies.items():
                target = root/name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
        return cfg, request, stage, calls

    def test_native_receipt_records_pinned_plan_hash(self):
        _, request = self.fixture()
        with patch.object(entry, 'verify_host_staging', wraps=entry.verify_host_staging) as verify:
            host = self.host(self.run_q(request))
        self.assertEqual(verify.call_count, 1)
        self.assertEqual(host['stager'], 'native')
        self.assert_plan_hash(host, request)

    def test_native_archive_and_directory_pass(self):
        request, _ = self.archive_fixture()
        host = self.host(self.run_q(request))
        self.assertEqual(host['stager'], 'native')
        self.assert_plan_hash(host, request)

    def test_native_input_wrong_bytes_refuse(self):
        cfg, request = self.fixture()
        self.pin('unreferenced.txt', b'right', stage=True)
        self.entries['u/unreferenced.txt']['payload'] = base64.b64encode(b'wrong').decode()
        self.repin(cfg, request)
        self.refused(self.run_q(request), 'Staging digest differs')

    def test_kit_hook_passes_stage_host_and_records_plan_hash(self):
        cfg, request, stage, calls = self.kit_fixture()
        with self.dependencies(), patch.object(entry, 'verify_host_staging') as verify:
            root, job, receipt = entry.begin_host(cfg, self.root, request)
            with entry.host_environment(job):
                entry.stage_host(cfg, root, request, job, stage=stage, result=receipt)
        verify.assert_not_called()
        self.assertEqual(calls, [self.root])
        self.assertEqual(receipt['stager'], 'hook')
        self.assert_plan_hash(receipt, request)
        with scope(self.paths):
            self.assertNotEqual(receipt['staging_plan_sha256'], digest(load(pinned(request['staging']))))

    def test_kit_hook_writes_host_json_with_plan_hash(self):
        _, request, stage, calls = self.kit_fixture()
        with self.dependencies(), patch.object(entry, 'verify_host_staging') as verify:
            host = self.host(proof.run(request, self.root, stage=stage))
        verify.assert_not_called()
        self.assertEqual(calls, [self.root])
        self.assertEqual(host['stager'], 'hook')
        self.assert_plan_hash(host, request)
        self.assertEqual(load(self.root/'host.json'), host)

    def test_hook_unreferenced_bytes_are_not_native_reverified(self):
        cfg, request = self.fixture()
        self.pin('unreferenced.txt', b'right', stage=True)
        self.repin(cfg, request)
        from launch_r2.staging import stage_inputs
        def stage(entries, root):
            stage_inputs(entries, root)
            (root/'u/unreferenced.txt').write_bytes(b'hook-owned bytes')
        with self.dependencies():
            host = self.host(proof.run(request, self.root, stage=stage))
        self.assertEqual(host['stager'], 'hook')
        self.assert_plan_hash(host, request)

    def test_hook_plan_wrong_bytes_refuse_before_hook(self):
        _, request, stage, calls = self.kit_fixture()
        (self.area/'bootstrap/kit_stage.json').write_bytes(b'{}')
        with self.dependencies():
            result = proof.run(request, self.root, stage=stage)
        self.refused(result, 'Missing or changed pinned input:')
        self.assertEqual(calls, [])
