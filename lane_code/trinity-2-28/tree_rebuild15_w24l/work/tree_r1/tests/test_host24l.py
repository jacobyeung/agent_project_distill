"""Tiny retained q fixtures; production authorities and capacity work are synthetic."""
from copy import deepcopy
import base64
import io
from pathlib import Path
import sqlite3
import tarfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from launch_r1 import entry, production_proof as proof
from student_pilot.p3_provenance import digest, encoded, file_pin, load, pinned
from tests import test_host24j as previous


class Host24L(unittest.TestCase):
    setUp = previous.HostReceipt.setUp
    pin = previous.HostReceipt.pin
    fixture = previous.HostReceipt.fixture
    run_q = previous.HostReceipt.run_q

    def dependencies(self, **kwargs):
        stack = previous.HostReceipt.dependencies(self, **kwargs)
        def audit(cfg, directory):
            self.calls.append(('audit', previous.carrier.identity(cfg)))
            directory.mkdir(parents=True, exist_ok=True)
            return dict(complete=True, fixture_config_identity=previous.carrier.identity(cfg))
        stack.enter_context(patch('student_pilot.r1_loader.production_audit', side_effect=audit))
        return stack

    def repin(self, cfg, request):
        request['config'] = self.pin('config24l.json', cfg)
        request['staged_pins'] = [request['config']]
        request['staging'] = self.pin('stage24l.json', dict(entries=self.entries))

    def host(self, result):
        self.assertEqual(result['status'], 'ADMIT', result)
        return load(pinned(result['host_receipt']))

    def refused(self, result, name):
        self.assertEqual(result['status'], 'REFUSE', result)
        self.assertIn(name, result['refusal'])
        self.assertNotIn('host_receipt', result)
        self.assertFalse((self.root/'host.json').exists())

    def twins(self, *, bad_scene=False, bad_base=False):
        cfg, request = self.fixture(bad_scene=bad_base)
        row = dict(qid='source', dataset='d1', scene='bad' if bad_base else 'clean')
        db = sqlite3.connect(':memory:')
        db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
        db.execute('INSERT INTO rows VALUES(?,?,?)', (0, encoded(row), '{}'))
        source = self.pin('twin_source.db', db.serialize(), stage=True)
        db.close()
        receipt = dict(database=source, count=1, division=cfg['scene_division'])
        cfg['streams']['vqa'] = self.pin('twin_source.json', receipt, stage=True)
        spec = dict(source_database=source,
                    binding=self.pin('twin_binding.json', {}, stage=True),
                    rows=self.pin('twin_rows.json', {}, stage=True))
        cfg['r1_training']['direction_twins'] = spec
        twin = dict(qid='twin', dataset='d1', scene='bad' if bad_scene else 'clean')
        self.repin(cfg, request)
        stack = self.dependencies()
        # Exercise native augment and verify_augmented on two rows. Only the
        # production authority and room census are replaced by fixture evidence.
        stack.enter_context(patch('student_pilot.r1_rooms.STORE', source['sha256']))
        stack.enter_context(patch('student_pilot.r1_direction_twins.specifications', return_value=spec))
        stack.enter_context(patch('student_pilot.r1_direction_twins.Binding',
                                  return_value=SimpleNamespace(rows=lambda: iter([twin]))))
        stack.enter_context(patch('student_pilot.r1_rooms.census', return_value=({}, {})))
        return cfg, request, stack

    def test_scene_receipt_certifies_native_twin_store(self):
        cfg, request, stack = self.twins()
        with stack, patch.object(entry, 'check_host_scene', wraps=entry.check_host_scene) as check:
            result = proof.run(request, self.root)
        host = self.host(result)
        final = load(pinned(result['config']))
        self.assertEqual(check.call_count, 2)
        self.assertEqual(check.call_args_list[0].args[0]['streams']['vqa'], cfg['streams']['vqa'])
        self.assertEqual(check.call_args_list[1].args[0]['streams']['vqa'], final['streams']['vqa'])
        self.assertNotEqual(cfg['streams']['vqa'], final['streams']['vqa'])
        self.assertEqual(host['scene_division_inputs']['vqa'], final['streams']['vqa'])
        self.assertEqual(host['scene_division_inputs']['division'], final['scene_division'])
        self.assertEqual(host['scene_division']['vqa']['read'], 2)
        self.assertEqual(host['scene_division']['vqa']['admitted'], 2)
        self.assertEqual(host['scene_division']['routing']['read'], 1)

    def test_cross_division_twin_refuses_by_name(self):
        _, request, stack = self.twins(bad_scene=True)
        with stack:
            result = proof.run(request, self.root)
        self.refused(result, 'SCENE_DIVISION_REFUSED')
        self.assertTrue((self.root/'twins/receipt.json').is_file())
        self.assertEqual(self.calls, [])

    def test_pre_twin_scene_refusal_remains(self):
        _, request, stack = self.twins(bad_base=True)
        with stack:
            result = proof.run(request, self.root)
        self.refused(result, 'SCENE_DIVISION_REFUSED')
        self.assertFalse((self.root/'twins').exists())

    def test_selection_pin_digest_and_native_stager_recorded(self):
        _, request = self.fixture()
        host = self.host(self.run_q(request))
        self.assertEqual(host['routing_selection'], request['routing_selection'])
        self.assertEqual(host['regenerated_sha256'], digest({'synthetic_routing': True}))
        self.assertEqual(host['stager'], 'native')
        self.assertFalse(host['routing_substituted'])

    def test_substituted_routing_and_inputs_recorded_without_refusal(self):
        cfg, request = self.fixture()
        original = deepcopy(cfg)
        routed = load(self.area/'bootstrap/routing.json')
        routed['fixture_substitution'] = True
        request['routing_base'] = self.pin('substituted.json', routed, stage=True)
        request['routing_inputs'] = {'fixture': 'substituted'}
        self.repin(cfg, request)
        host = self.host(self.run_q(request))
        self.assertTrue(host['routing_substituted'])
        changes = host['routing_substitution']
        self.assertEqual(changes['routing']['original_sha256'], original['streams']['routing']['sha256'])
        self.assertEqual(changes['routing']['substituted_sha256'], request['routing_base']['sha256'])
        self.assertEqual(changes['routing_inputs']['original_sha256'], digest(original['r1_training']['routing_inputs']))
        self.assertEqual(changes['routing_inputs']['substituted_sha256'], digest(request['routing_inputs']))
        final = load(self.root/'h/config.json')
        self.assertEqual(final['streams']['routing'], request['routing_base'])
        self.assertEqual(final['r1_training']['routing_inputs'], request['routing_inputs'])

    def test_minimal_routing_records_only_routing_substitution(self):
        _, request = self.fixture()
        request.pop('routing_inputs')
        with self.dependencies(), patch('student_pilot.r1_coverage.routing_request', return_value=True), \
                patch('student_pilot.r1_coverage.validate_binding'):
            host = self.host(proof.run(request, self.root))
        self.assertEqual(set(host['routing_substitution']), {'routing'})
        self.assertFalse(host['routing_substituted'])

    def run_hook(self, request, corrupt=None):
        from launch_r2.staging import stage_inputs
        def stage(entries, root):
            stage_inputs(entries, root)
            if corrupt:
                corrupt(root)
        with self.dependencies():
            return proof.run(request, self.root, stage=stage)

    def test_hook_stager_recorded(self):
        _, request = self.fixture()
        self.assertEqual(self.host(self.run_hook(request))['stager'], 'hook')

    def test_hook_wrong_unreferenced_byte_refuses(self):
        cfg, request = self.fixture()
        self.pin('unreferenced.txt', b'right byte', stage=True)
        self.repin(cfg, request)
        result = self.run_hook(request, lambda root: (root/'u/unreferenced.txt').write_bytes(b'wrong byte'))
        self.refused(result, 'R1_HOST_STAGING_DIFFERS:u/unreferenced.txt')

    def archive_fixture(self, *, inventory_only=False):
        cfg, request = self.fixture()
        payload = io.BytesIO()
        inventory = {}
        import hashlib
        with tarfile.open(fileobj=payload, mode='w') as archive:
            for name, raw in [('payload/used.txt', b'used'), ('payload/unreferenced.txt', b'authenticated')]:
                member = tarfile.TarInfo(name)
                member.size = len(raw)
                archive.addfile(member, io.BytesIO(raw))
                inventory[name] = hashlib.sha256(raw).hexdigest()
        source = dict(payload=base64.b64encode(payload.getvalue()).decode(), inventory=inventory)
        key = digest(inventory) if inventory_only else hashlib.sha256(payload.getvalue()).hexdigest()
        source['inventory_sha256' if inventory_only else 'sha256'] = key
        self.entries['u/archive.txt'] = dict(archive=source, member='payload/used.txt', sha256=inventory['payload/used.txt'])
        self.entries['u/directory'] = dict(directory=source, member='payload', sha256=digest(inventory))
        self.repin(cfg, request)
        return request, key

    def test_hook_archive_and_directory_pass(self):
        request, _ = self.archive_fixture()
        self.assertEqual(self.host(self.run_hook(request))['stager'], 'hook')

    def test_hook_archive_inventory_catches_unreferenced_byte(self):
        request, key = self.archive_fixture(inventory_only=True)
        result = self.run_hook(request, lambda root: (root/'x'/key/'payload/unreferenced.txt').write_bytes(b'wrong'))
        self.refused(result, 'R1_HOST_STAGING_DIFFERS:u/archive.txt')

    def test_hook_archive_hash_catches_wrong_archive_byte(self):
        request, key = self.archive_fixture()
        result = self.run_hook(request, lambda root: (root/'a'/key).write_bytes(b'wrong'))
        self.refused(result, 'R1_HOST_STAGING_DIFFERS:u/archive.txt')

    def test_hook_archive_target_catches_wrong_byte(self):
        request, _ = self.archive_fixture()
        result = self.run_hook(request, lambda root: (root/'u/archive.txt').write_bytes(b'wrong'))
        self.refused(result, 'R1_HOST_STAGING_DIFFERS:u/archive.txt')
