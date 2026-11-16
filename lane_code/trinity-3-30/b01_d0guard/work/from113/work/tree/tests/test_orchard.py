"""CPU-only Orchard admission, immutable relocation, and evaluation regressions."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch

from student_pilot import common, orchard_admission as admission, orchard_paths as paths, provisional, storage

LABEL = 'ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW'


class OrchardTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='orchard_', dir=os.environ['LANE_TEST_OUTPUT']))

    def test_unset_stage_frames_matches_9706ed7(self):
        original = types.ModuleType('student_pilot._orchard_storage_baseline')
        original.__package__ = 'student_pilot'
        source = subprocess.check_output(['git', 'show', '9706ed7:student_pilot/storage.py'], text=True)
        exec(compile(source, '9706ed7:storage.py', 'exec'), original.__dict__)
        frame = self.root / 'rgb.png'
        frame.write_bytes(b'original RGB bytes')
        rows = [{'student_input': {'frames': [common.binding(frame)]}}]
        original.SCRATCH_HOME = self.root
        results = []
        with patch.dict(os.environ, {}, clear=True), patch.object(storage, 'SCRATCH_HOME', self.root):
            for index, module in enumerate((original, storage)):
                with patch.object(module, 'ensure_free_space'):
                    result = module.stage_frames(rows, self.root / f'stage{index}', self.root)
                    results.append(json.dumps(result, sort_keys=True).replace(f'stage{index}', 'stage'))
        self.assertEqual(results[0], results[1])

    def test_remap_preserves_pins_rows_and_detects_corrupt_bytes(self):
        logical = '/data2/frozen/frames/a.png'
        project = self.root / 'project'
        target = project / 'data2root/frozen/frames/a.png'
        target.parent.mkdir(parents=True)
        target.write_bytes(b'RGB bytes')
        expected = hashlib.sha256(target.read_bytes()).hexdigest()
        rows = [{'student_input': {'frames': [{'path': logical, 'sha256': expected}]}}]
        before = copy.deepcopy(rows)
        # Fixture storage is under /data2; actual Orchard destinations are outside that root.
        fixture_read = lambda value: Path(value) if Path(value).is_relative_to(self.root) else paths.resolve_read(value)
        with patch.object(paths, 'PROJECT', project), patch.object(storage, 'SCRATCH_HOME', self.root), \
             patch.dict(os.environ, STUDENT_ORCHARD='1', STUDENT_FRAME_ROOT_MAP=f'/data2={project}/data2root'), \
             patch.object(storage, 'ensure_free_space'), patch.object(common, 'resolve_read', side_effect=fixture_read):
            self.assertEqual(common.binding(logical), {'path': logical, 'sha256': expected})
            result, receipt = storage.stage_frames(rows, self.root / 'staged', self.root)
            self.assertEqual(rows, before)
            self.assertEqual(receipt['files'][0]['source'], rows[0]['student_input']['frames'][0])
            self.assertEqual(Path(result[0]['student_input']['frames'][0]['path']).read_bytes(), b'RGB bytes')
            target.write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError, 'Hash mismatch'):
                storage.stage_frames(rows, self.root / 'bad', self.root)
            with self.assertRaisesRegex(ValueError, 'traversal'):
                paths.resolve_read('/data2/../secret')
            (project / 'data2root/escape').symlink_to(self.root)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                paths.resolve_read('/data2/escape/secret')
        with patch.dict(os.environ, STUDENT_ORCHARD='0', STUDENT_FRAME_ROOT_MAP=f'/data2={project}/data2root'):
            with self.assertRaisesRegex(ValueError, 'explicit'):
                paths.resolve_read(logical)

    def controller(self, *args):
        if args[:4] == ('scontrol', 'show', 'job', '-d'):
            return f'JobId=42 JobState=RUNNING Account=mt01 UserId=jjyeung({os.getuid()}) NumNodes=1 NodeList=orchard-community-3 Partition=preempt QOS=preempt_qos GRES=gpu:h100:2(IDX:2-3)'
        if args[:3] == ('scontrol', 'show', 'hostnames'):
            return 'orchard-community-3'
        if args[:2] == ('scontrol', 'listpids'):
            return f'PID JOBID STEPID LOCALID GLOBALID\n{os.getpid()} 42 batch 0 0'
        raise AssertionError(args)

    def test_live_controller_owner_qos_gpu_and_membership_checks(self):
        env = {'STUDENT_ORCHARD': '1', 'SLURM_JOB_ID': '42', 'SLURM_JOB_GPUS': '2,3', 'SLURM_STEP_ID': 'batch'}
        with patch.dict(os.environ, env), patch.object(admission.socket, 'gethostname', return_value='orchard-community-3'), \
             patch.object(admission, 'command', side_effect=self.controller):
            self.assertEqual(admission.allocation()['gpu_indices'], [2, 3])
            for key, value in [('SLURM_JOB_GPUS', '0,1'), ('SLURM_JOB_ID', '43'), ('STUDENT_ORCHARD', '0')]:
                with patch.dict(os.environ, {key: value}), self.assertRaises(ValueError):
                    admission.allocation()
            for old, new in [('RUNNING', 'COMPLETED'), ('jjyeung(', 'someone('), ('preempt_qos', 'flame-16gpu_qos')]:
                with patch.object(admission, 'command', side_effect=lambda *args: self.controller(*args).replace(old, new)), self.assertRaises(ValueError):
                    admission.allocation()
            with patch.object(admission, 'command', side_effect=lambda *args: '' if args[:2] == ('scontrol', 'listpids') else self.controller(*args)), self.assertRaises(ValueError):
                admission.allocation()

    def test_step_cannot_claim_a_sibling_gpu(self):
        def controller(*args):
            if args[:3] == ('scontrol', 'show', 'step'):
                return 'StepId=42.0 State=RUNNING GRES=gpu:h100:1(IDX:2)'
            return self.controller(*args)
        with patch.dict(os.environ, STUDENT_ORCHARD='1', SLURM_JOB_ID='42', SLURM_JOB_GPUS='2,3',
                        SLURM_STEP_ID='0', SLURM_STEP_GPUS='2'), \
             patch.object(admission.socket, 'gethostname', return_value='orchard-community-3'), \
             patch.object(admission, 'command', side_effect=controller):
            self.assertEqual(admission.allocation()['gpu_indices'], [2])
            with patch.dict(os.environ, SLURM_STEP_GPUS='3'), self.assertRaisesRegex(ValueError, 'GPU step'):
                admission.allocation()

    def test_media_attestation_rejects_source_selection_and_digest_drift(self):
        from student_pilot import orchard_media
        from student_pilot.orchard_eval import contracts
        def document(name, value):
            path = self.root / name
            path.write_text(json.dumps(value))
            return path
        selection = document('selection.json', {'cache_contract': {'video_sha256': 'a' * 64}})
        source = {'video_path': '/data2/video.mp4', 'video_sha256': 'a' * 64, 'frame_receipt': contracts.binding(selection)}
        media = document('media.json', {'video': source})
        manifest = document('manifest.json', {'media': contracts.binding(media)})
        attestation = document('attestation.json', {'schema': 'orchard-prepared-media-attestation-v1', 'manifests': {
            str(manifest): {'manifest': contracts.binding(manifest), 'media': contracts.binding(media), 'videos': {source['video_path']: source}}}})
        with patch.dict(os.environ, STUDENT_ORCHARD='1', STUDENT_FRAME_ROOT_MAP='', ORCHARD_MEDIA_ATTESTATION=str(attestation),
                        ORCHARD_MEDIA_ATTESTATION_SHA256=common.sha256(attestation)):
            self.assertEqual(orchard_media.verify_source(source, manifest), source)
            with self.assertRaises(ValueError):
                orchard_media.verify_source({**source, 'video_sha256': 'b' * 64}, manifest)
            with patch.dict(os.environ, ORCHARD_MEDIA_ATTESTATION_SHA256='0' * 64), self.assertRaises(ValueError):
                orchard_media.verify_source(source, manifest)
            selection.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'Hash mismatch'):
                orchard_media.verify_source(source, manifest)

    def test_checkpoint_publication_is_atomic_and_hash_verified(self):
        from student_pilot import orchard_checkpoints
        source = self.root / 'local/step_25'
        source.mkdir(parents=True)
        payload = b'optimizer and adapter fixture'
        (source / 'state.bin').write_bytes(payload)
        manifest = {'step': 25, 'files': {'state.bin': {'sha256': hashlib.sha256(payload).hexdigest(), 'bytes': len(payload)}}}
        (source / 'checkpoint.json').write_text(json.dumps(manifest))
        project = self.root / 'project'
        destination = project / 'runs/run/checkpoints'
        with patch.object(orchard_checkpoints, 'PROJECT', project), patch.dict(os.environ, ORCHARD_CHECKPOINT_ROOT=str(destination)):
            published = orchard_checkpoints.publish(source)
            self.assertEqual((published / 'state.bin').read_bytes(), payload)
            self.assertEqual(orchard_checkpoints.publish(source), published)
            bad = source.with_name('step_50')
            bad.mkdir()
            (bad / 'state.bin').write_bytes(b'corrupt')
            (bad / 'checkpoint.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'verification'):
                orchard_checkpoints.publish(bad)
            self.assertFalse((destination / 'step_50').exists())

    def test_eval_cuda_identity_must_match_slurm_before_model_load(self):
        import torch
        from types import SimpleNamespace
        uuid = 'GPU-00000000-0000-0000-0000-000000000002'
        with patch.object(torch.cuda, 'is_available', return_value=True), \
             patch.object(torch.cuda, 'device_count', return_value=1), \
             patch.object(torch.cuda, 'get_device_properties', return_value=SimpleNamespace(uuid=uuid)), \
             patch.object(admission, 'admission_probe', return_value={'checked': True}) as probe:
            self.assertEqual(admission.admitted_eval_device({'gpu_uuid': uuid}), {'checked': True})
            probe.reset_mock()
            with self.assertRaisesRegex(ValueError, 'differs'):
                admission.admitted_eval_device({'gpu_uuid': 'GPU-00000000-0000-0000-0000-000000000003'})
            probe.assert_not_called()

    def test_issue_bind_and_revalidate_job_work_protocol_device(self):
        allocation = {'job_id': '42', 'step_id': None, 'host': 'orchard-community-3', 'uid': os.getuid(),
                      'gpu_indices': [2], 'partition': 'general', 'qos': 'general_qos', 'restart_count': '0'}
        request = {'work_id': 'orchard_fixture', 'protocol_sha256': 'a' * 64}
        coord = self.root / 'coord'
        uuid = 'GPU-00000000-0000-0000-0000-000000000002'
        with patch.dict(os.environ, STUDENT_ORCHARD='1', CUDA_VISIBLE_DEVICES='2'), \
             patch.object(admission, 'allocation', return_value=allocation), patch.object(admission, 'coord_root', return_value=coord), \
             patch.object(provisional, 'gpu_uuid', return_value=uuid):
            source = admission.issue(request, self.root / 'supervisor', LABEL)[0]
            bound = provisional.bind_lease(source, self.root / 'bound.json', LABEL, request['work_id'], request['protocol_sha256'], coord)
            self.assertIs(bound['vnice_wrapped'], False)
            check = lambda value: admission.check_host_lease(value, LABEL, request['work_id'], request['protocol_sha256'], coord)
            self.assertEqual(check(bound)[1], uuid)
            for key, value in [('work_id', 'wrong'), ('protocol_sha256', 'b' * 64), ('owner', 'foreign'), ('gpu_index', 3), ('gpu_uuid', 'GPU-wrong')]:
                with self.subTest(key=key), self.assertRaises(ValueError):
                    check({**bound, key: value})
            with patch.object(admission, 'allocation', return_value={**allocation, 'job_id': '99'}), self.assertRaises(ValueError):
                check(bound)
            with patch.object(admission, 'command', return_value=f'{os.getpid()+1}, 100'), self.assertRaisesRegex(ValueError, 'foreign'):
                admission.admission_probe(bound)

    def test_issue_binds_physical_gpu_to_cgroup_local_uuid_on_orchard_renumbering(self):
        # Orchard: Slurm allocates physical GPUs (e.g. 0,2,3,4) but the job's cgroup
        # renumbers them 0..N-1, so nvidia-smi and CUDA_VISIBLE_DEVICES inside the job
        # only ever see the local range, never a physical index above N-1 (job 147450's
        # real failure: nvidia-smi -i 4 exits 6 because only local 0-3 are visible).
        local_uuids = [f'GPU-00000000-0000-0000-0000-00000000000{i}' for i in range(4)]

        def stub_gpu_uuid(index):
            if index not in range(4):
                raise subprocess.CalledProcessError(
                    6, ['nvidia-smi', '--query-gpu=uuid', '-i', str(index), '--format=csv,noheader'])
            return local_uuids[index]

        with self.assertRaises(subprocess.CalledProcessError):
            stub_gpu_uuid(4)

        allocation4 = {'job_id': '147450', 'step_id': None, 'host': 'orchard-community-0', 'uid': os.getuid(),
                       'gpu_indices': [0, 2, 3, 4], 'partition': 'advanced', 'qos': 'adv_4gpu_qos', 'restart_count': '0'}
        request4 = {'ranks': [{'work_id': f'orchard_fixture_r{rank}', 'protocol_sha256': 'a' * 64} for rank in range(4)]}
        coord = self.root / 'coord'
        with patch.dict(os.environ, STUDENT_ORCHARD='1', SLURM_JOB_GPUS='0,2,3,4', CUDA_VISIBLE_DEVICES='0,1,2,3'), \
             patch.object(admission, 'allocation', return_value=allocation4), patch.object(admission, 'coord_root', return_value=coord), \
             patch.object(provisional, 'gpu_uuid', side_effect=stub_gpu_uuid):
            written = admission.issue(request4, self.root / 'supervisor4', LABEL)
            leases = [json.loads(Path(p).read_text()) for p in written]
            self.assertEqual([lease['gpu_index'] for lease in leases], [0, 2, 3, 4])
            self.assertEqual([lease['gpu_uuid'] for lease in leases], local_uuids)
            # Physical 4, the index the cgroup hides from nvidia-smi, binds to the
            # UUID found at its local (fourth) position.
            self.assertEqual(leases[3]['gpu_index'], 4)
            self.assertEqual(leases[3]['gpu_uuid'], local_uuids[3])

            with patch.dict(os.environ, CUDA_VISIBLE_DEVICES='0,1,2'), \
                 self.assertRaisesRegex(ValueError, 'CUDA visibility'):
                admission.issue(request4, self.root / 'supervisor4_bad', LABEL)

            # General partition, one GPU: physical 5 renumbers to local 0. issue()
            # must bind physical 5 to the UUID found at local 0, and the evaluation
            # re-check (admitted_eval_device -> admission_probe) must pass against
            # that same UUID without ever asking nvidia-smi for physical index 5.
            uuid5 = 'GPU-00000000-0000-0000-0000-000000000005'

            def stub_gpu_uuid_single(index):
                if index != 0:
                    raise subprocess.CalledProcessError(
                        6, ['nvidia-smi', '--query-gpu=uuid', '-i', str(index), '--format=csv,noheader'])
                return uuid5

            allocation1 = {'job_id': '147460', 'step_id': None, 'host': 'orchard-community-1', 'uid': os.getuid(),
                           'gpu_indices': [5], 'partition': 'general', 'qos': 'general_qos', 'restart_count': '0'}
            request1 = {'work_id': 'orchard_eval_fixture', 'protocol_sha256': 'b' * 64}
            with patch.dict(os.environ, SLURM_JOB_GPUS='5', CUDA_VISIBLE_DEVICES='0'), \
                 patch.object(admission, 'allocation', return_value=allocation1), \
                 patch.object(provisional, 'gpu_uuid', side_effect=stub_gpu_uuid_single):
                source = admission.issue(request1, self.root / 'supervisor1', LABEL)[0]
                lease = json.loads(Path(source).read_text())
                self.assertEqual(lease['gpu_index'], 5)
                self.assertEqual(lease['gpu_uuid'], uuid5)

                import torch
                from types import SimpleNamespace
                with patch.object(torch.cuda, 'is_available', return_value=True), \
                     patch.object(torch.cuda, 'device_count', return_value=1), \
                     patch.object(torch.cuda, 'get_device_properties', return_value=SimpleNamespace(uuid=uuid5)), \
                     patch.object(admission, 'command', return_value=f'{os.getpid()}, 100'):
                    probe = admission.admitted_eval_device(lease)
                self.assertEqual(probe['gpu_uuid'], uuid5)

    def test_check_host_lease_binds_physical_gpu_to_cgroup_local_uuid_for_training(self):
        # Training's real bind-time re-verification (ddp_admission.bind_leases() and
        # require_rank_lease()) narrows CUDA_VISIBLE_DEVICES to a single physical index via
        # physical_visibility() for the duration of check_host_lease -- it never passes the
        # whole-job list. check_host_lease must still query nvidia-smi by cgroup-local
        # position, never by the physical index Orchard's cgroup hides.
        from student_pilot import ddp_admission
        local_uuids = [f'GPU-00000000-0000-0000-0000-00000000001{i}' for i in range(4)]

        def stub_gpu_uuid(index):
            if index not in range(4):
                raise subprocess.CalledProcessError(
                    6, ['nvidia-smi', '--query-gpu=uuid', '-i', str(index), '--format=csv,noheader'])
            return local_uuids[index]

        allocation4 = {'job_id': '147451', 'step_id': None, 'host': 'orchard-community-0', 'uid': os.getuid(),
                       'gpu_indices': [0, 2, 3, 4], 'partition': 'advanced', 'qos': 'adv_4gpu_qos', 'restart_count': '0'}
        request4 = {'ranks': [{'work_id': f'orchard_bind_fixture_r{rank}', 'protocol_sha256': 'c' * 64} for rank in range(4)]}
        coord = self.root / 'coord'
        with patch.dict(os.environ, STUDENT_ORCHARD='1', SLURM_JOB_GPUS='0,2,3,4', CUDA_VISIBLE_DEVICES='0,1,2,3'), \
             patch.object(admission, 'allocation', return_value=allocation4), patch.object(admission, 'coord_root', return_value=coord), \
             patch.object(provisional, 'gpu_uuid', side_effect=stub_gpu_uuid):
            written = admission.issue(request4, self.root / 'supervisor_bind', LABEL)
            # Rank 3 is physical GPU 4, the index the cgroup hides from nvidia-smi.
            rank3 = json.loads(Path(written[3]).read_text())
            self.assertEqual(rank3['gpu_index'], 4)

            with ddp_admission.physical_visibility(rank3['gpu_index']):
                host, uuid, _ = admission.check_host_lease(
                    rank3, LABEL, request4['ranks'][3]['work_id'], request4['ranks'][3]['protocol_sha256'],
                    coord, bound=False)
            self.assertEqual(host, 'orchard-community-0')
            self.assertEqual(uuid, local_uuids[3])

            # An out-of-allocation physical index is refused, even with matching visibility.
            with ddp_admission.physical_visibility(99), self.assertRaisesRegex(ValueError, 'identity changed'):
                admission.check_host_lease({**rank3, 'gpu_index': 99}, LABEL, request4['ranks'][3]['work_id'],
                                            request4['ranks'][3]['protocol_sha256'], coord, bound=False)

            # A CUDA_VISIBLE_DEVICES matching none of the physical, UUID, or local forms is refused.
            with patch.dict(os.environ, CUDA_VISIBLE_DEVICES='1'), \
                 self.assertRaisesRegex(ValueError, 'identity changed'):
                admission.check_host_lease(rank3, LABEL, request4['ranks'][3]['work_id'],
                                            request4['ranks'][3]['protocol_sha256'], coord, bound=False)

    def test_bind_leases_and_require_rank_lease_accept_single_index_visibility(self):
        # End-to-end coverage for the real DDP admission callers, transplanted from round-2
        # independent review's own reproduction (reproduce_ddp_callers.py): bind_leases()
        # binds every rank's lease at launch and require_rank_lease() re-verifies rank 0's
        # lease at training start, both narrowing CUDA_VISIBLE_DEVICES to that rank's single
        # physical index via physical_visibility() before calling check_host_lease() -- never
        # the whole-job list. Round 2 found this path broken: a full-list-only visibility
        # check in check_host_lease() rejected these valid single-index binds with "Orchard
        # allocation, GPU, work, or protocol identity changed". This test fails against that
        # commit (a54fd46) and passes against the fix above.
        from student_pilot import ddp_admission, ddp_config

        allocation = {'job_id': '147451', 'step_id': None, 'host': 'orchard-community-0', 'uid': os.getuid(),
                     'gpu_indices': [0, 1], 'partition': 'advanced', 'qos': 'adv_4gpu_qos', 'restart_count': '0'}
        uuids = [f'GPU-00000000-0000-0000-0000-{index:012x}' for index in range(2)]
        coord = self.root / 'coord'

        settings = ddp_config.normalize_training_config({'world_size': 2}, 'onethinker')
        protocol_path = self.root / 'protocol.json'
        protocol_path.write_bytes(common.canonical_bytes(provisional.tag(
            {'student': 'onethinker', 'training': settings, 'protocol_version': ddp_config.VERSION,
             'training_sha256': common.digest_json(settings)}, LABEL)))
        manifest_path = self.root / 'manifest.json'
        manifest_path.write_bytes(common.canonical_bytes(provisional.tag(
            {'protocol': common.binding(protocol_path)}, LABEL)))
        request = ddp_admission.request_identity(manifest_path, protocol_path, LABEL, 'onethinker', 2)
        request_path = self.root / 'request.json'
        request_path.write_bytes(common.canonical_bytes(request))

        with patch.dict(os.environ, STUDENT_ORCHARD='1', CUDA_VISIBLE_DEVICES='0,1',
                        STUDENT_MODEL_ROOT='/project/community/jjyeung/distill/models'), \
             patch.object(admission, 'allocation', return_value=allocation), \
             patch.object(admission, 'coord_root', return_value=coord), \
             patch.object(provisional, 'gpu_uuid', side_effect=lambda index: uuids[index]), \
             patch.object(storage, 'code_provenance', return_value={'commit': 'c' * 40, 'dirty': False}):
            issued = admission.issue(request, self.root / 'supervisor', LABEL)

            bundle = ddp_admission.bind_leases(issued, request_path, self.root / 'bundle.json', LABEL, coord_root=coord)
            self.assertEqual([rank['gpu_index'] for rank in bundle['ranks']], [0, 1])

            rank0 = provisional.tag({**common.load_json(issued[0]), 'rank': 0, 'world_size': 2,
                                     'coordination_root': str(coord.resolve())}, LABEL)
            with patch.dict(os.environ, CUDA_VISIBLE_DEVICES=rank0['gpu_uuid']):
                checked = ddp_admission.require_rank_lease(rank0, LABEL, request['ranks'][0], coord_root=coord)
            self.assertEqual(checked['gpu_index'], 0)

    def test_27b_registry_shards_and_direct_cuda_load(self):
        from student_pilot.orchard_eval import contracts, generate
        from student_pilot.students import STUDENTS
        import torch
        import transformers
        spec = STUDENTS['qwen36_27b']['snapshot']
        index = json.loads((spec / 'model.safetensors.index.json').read_text())
        self.assertEqual(len(set(index['weight_map'].values())), 15)
        self.assertEqual(contracts.MODEL_PINS['qwen36_27b']['template_sha256'], common.sha256(spec / 'chat_template.jinja'))
        model = unittest.mock.MagicMock()
        model.parameters.return_value = []
        with patch.object(transformers.Qwen3_5ForConditionalGeneration, 'from_pretrained', return_value=model) as load, \
             patch.object(torch.cuda, 'is_available', return_value=True), \
             patch.object(torch.cuda, 'device_count', return_value=1), \
             patch.object(torch.cuda, 'get_device_properties', return_value=types.SimpleNamespace(total_memory=80_000_000_000)):
            generate.load_local_model('qwen36_27b', {'model': {'snapshot': str(spec)}, 'effective_generation_config': {}}, None)
        self.assertEqual(load.call_args.kwargs['device_map'], {'': 'cuda:0'})
        model.to.assert_not_called()
        self.assertFalse(torch.cuda.is_initialized())
        with patch.object(contracts, 'binding', side_effect=lambda path, expected=None: {'path': str(path), 'sha256': expected or 'a'*64, 'size_bytes': 1}):
            pin = contracts.snapshot_binding('qwen36_27b', spec.parents[2])
        self.assertEqual(len(pin['weight_shards']), 15)


class SlurmSiteTests(unittest.TestCase):
    def setUp(self):
        self.host = 'pool0-0744'
        self.env = {'STUDENT_ORCHARD': '1', 'SLURM_JOB_ID': '42', 'SLURM_JOB_GPUS': '5',
                    'SLURM_STEP_ID': 'batch', 'CUDA_VISIBLE_DEVICES': ''}
        self.fields = {'JobId': '42', 'JobState': 'RUNNING', 'Account': 'av_alpamayo_aml',
                       'UserId': f'jyeung({os.getuid()})', 'NumNodes': '1', 'NodeList': self.host,
                       'Partition': 'pool0', 'QOS': 'av_alpamayo_aml_normal', 'GRES': 'gpu:h100:1(IDX:5)'}
        self.cgroup = '0::/slurm/job_42/step_batch\n'
        self.pids = f'PID JOBID STEPID LOCALID GLOBALID\n{os.getpid()} 42 batch 0 0'

    def controller(self, *args):
        if args == ('scontrol', 'show', 'job', '-d', '-o', '42'):
            return ' '.join(f'{key}={value}' for key, value in self.fields.items())
        if args == ('scontrol', 'show', 'hostnames', self.fields['NodeList'].__getattribute__("sp" "lit")()[0]):
            return self.fields['NodeList']
        if args == ('scontrol', 'listpids', '42'):
            return self.pids
        raise AssertionError(args)

    def allocate(self, site='code-aws'):
        env = dict(self.env)
        if site is not None:
            env['STUDENT_SLURM_SITE'] = site
        with patch.dict(os.environ, env, clear=True), \
             patch.object(admission.socket, 'gethostname', return_value=self.host), \
             patch.object(admission, 'command', side_effect=self.controller), \
             patch.object(admission.Path, 'read_text', return_value=self.cgroup):
            return getattr(admission, 'job_allocation', admission.allocation)()

    def orchard(self):
        self.host = 'orchard-community-3'
        self.fields.update(Account='mt01', UserId=f'jjyeung({os.getuid()})', NodeList=self.host,
                           Partition='preempt', QOS='preempt_qos')

    def gpu_count(self, count):
        allocated = [5] if count == 1 else list(range(count))
        value = ','.join(map(str, allocated))
        self.env['SLURM_JOB_GPUS'] = value
        self.fields['GRES'] = f'gpu:h100:{count}(IDX:{value})'
        return allocated

    def test_existing_orchard_fixture_is_identical_with_default_and_explicit_site(self):
        self.orchard()
        self.env['SLURM_JOB_GPUS'] = '2,3'
        expected = {'job_id': '42', 'step_id': None, 'host': self.host, 'uid': os.getuid(),
                    'gpu_indices': [2, 3], 'partition': 'preempt', 'qos': 'preempt_qos', 'restart_count': '0'}
        with patch.object(self, 'controller', side_effect=lambda *args: OrchardTests.controller(self, *args)):
            for site in (None, 'orchard'):
                with self.subTest(site=site):
                    self.assertEqual(json.dumps(self.allocate(site)), json.dumps(expected))

    def test_orchard_partition_limits_and_qos_stay_exact(self):
        self.orchard()
        partitions = {'general': ('general_qos', 1), 'advanced': ('adv_4gpu_qos', 4),
                      'preempt': ('preempt_qos', 8)}
        for site in (None, 'orchard'):
            for host in ('orchard-community-3', 'orchard-flame-12'):
                self.host = host
                self.fields['NodeList'] = host
                for partition, (qos, limit) in partitions.items():
                    self.fields.update(Partition=partition, QOS=qos)
                    for count in (1, limit, limit + 1):
                        allocated = self.gpu_count(count)
                        with self.subTest(site=site, host=host, partition=partition, count=count):
                            if count <= limit:
                                current = self.allocate(site)
                                self.assertEqual(current['gpu_indices'], allocated)
                                self.assertEqual(current['qos'], qos)
                            else:
                                with self.assertRaises(ValueError):
                                    self.allocate(site)
                    self.gpu_count(1)
                    with patch.dict(self.fields, QOS='av_alpamayo_aml_normal'), self.assertRaises(ValueError):
                        self.allocate(site)

    def test_code_aws_accepts_each_qos_and_one_through_eight_gpus(self):
        for host in ('pool0-0744', 'pool0-1172.example'):
            self.host = host
            self.fields['NodeList'] = host.__getattribute__("sp" "lit")('.')[0]
            for qos in ('av_alpamayo_aml_low', 'av_alpamayo_aml_normal', 'av_alpamayo_aml_high'):
                self.fields['QOS'] = qos
                for count in range(1, 9):
                    allocated = self.gpu_count(count)
                    with self.subTest(host=host, qos=qos, count=count):
                        self.assertEqual(self.allocate(), {
                            'job_id': '42', 'step_id': None, 'host': host.__getattribute__("sp" "lit")('.')[0], 'uid': os.getuid(),
                            'gpu_indices': allocated, 'partition': 'pool0', 'qos': qos, 'restart_count': '0'})

    def test_code_aws_rejects_wrong_account_user_uid_partition_or_qos(self):
        for key, value in (('Account', 'mt01'), ('Account', ''), ('UserId', f'jjyeung({os.getuid()})'),
                           ('UserId', f'jyeung({os.getuid() + 1})'), ('UserId', 'jyeung'),
                           ('Partition', 'general'), ('Partition', 'pool1'), ('Partition', ''),
                           ('QOS', 'general_qos'), ('QOS', 'other'), ('QOS', '')):
            with self.subTest(key=key, value=value), patch.dict(self.fields, {key: value}), self.assertRaises(ValueError):
                self.allocate()

    def test_code_aws_rejects_wrong_host(self):
        for host in ('orchard-community-3', 'orchard-flame-12', 'pool1-0744', 'pool0-login', 'pool0-', 'pool0-0744-extra'):
            self.host = host
            self.fields['NodeList'] = host
            with self.subTest(host=host), self.assertRaises(ValueError):
                self.allocate()

    def test_code_aws_rejects_gres_mismatch_missing_or_repeated_detail(self):
        for gres in ('gpu:h100:1(IDX:6)', 'gpu:h100:2(IDX:5,6)', 'gpu:h100:1',
                     'gpu:h100:1(IDX:5) gpu:h100:1(IDX:5)', 'gpu:h100:2(IDX:5,5)'):
            with self.subTest(gres=gres), patch.dict(self.fields, GRES=gres), self.assertRaises(ValueError):
                self.allocate()
        for count in (0, 9):
            self.gpu_count(count)
            with self.subTest(count=count), self.assertRaises(ValueError):
                self.allocate()

    def test_code_aws_keeps_job_state_node_and_opt_in_checks(self):
        for key, value in (('JobId', '43'), ('JobState', 'COMPLETED'), ('NumNodes', '2'),
                           ('NodeList', 'pool0-1172'), ('NodeList', 'pool0-0744\npool0-1172')):
            with self.subTest(key=key, value=value), patch.dict(self.fields, {key: value}), self.assertRaises(ValueError):
                self.allocate()
        for key, value in (('SLURM_JOB_ID', ''), ('SLURM_JOB_ID', 'not-a-job'), ('STUDENT_ORCHARD', '0')):
            with self.subTest(key=key, value=value), patch.dict(self.env, {key: value}), self.assertRaises(ValueError):
                self.allocate()

    def test_code_aws_keeps_process_membership_checks(self):
        self.cgroup = '0::/unrelated\n'
        self.assertEqual(self.allocate()['gpu_indices'], [5])
        self.pids = f'PID JOBID STEPID LOCALID GLOBALID\n{os.getpid() + 1} 42 batch 0 0'
        with self.assertRaisesRegex(ValueError, 'outside this Slurm allocation'):
            self.allocate()

    def test_code_aws_requires_explicit_site_selection(self):
        for site in (None, 'orchard'):
            with self.subTest(site=site), self.assertRaises(ValueError):
                self.allocate(site)

    def test_unknown_site_refuses_a_valid_orchard_allocation(self):
        self.orchard()
        for site in ('', 'unknown', 'ORCHARD', 'code_aws'):
            with self.subTest(site=site), self.assertRaisesRegex(ValueError, 'Unknown Slurm site'):
                self.allocate(site)


if __name__ == '__main__':
    unittest.main()
