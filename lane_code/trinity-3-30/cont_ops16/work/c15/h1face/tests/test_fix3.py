"""Closed step-544 identity, prepared bootstrap and unchanged full admission."""
import offline_guard
import base64
from contextlib import contextmanager, redirect_stdout
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import struct
import sys
import tarfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'kit/launcher'))
import binding as B
import export_stage as E
import orchard_launcher as L
import orchard_job as J
import orchard_stage as S

RUN = '469ddece'
OBJECT = 'q8/8865619b/469ddece_mstop.tar'
DEPLOY = '/project/community/jjyeung/okh7/x_07ca49df/o/'
RAW = (OBJECT+' 21583032320 3ed73aead82cb0bb6468321256ea25e8fdaa5a2963da31062fdf8874bda2d4c7\n').encode()


def folder():
    root = ROOT/'evidence'/('test_fix3_'+uuid.uuid4().hex)
    root.mkdir()
    return root


class Step544(unittest.TestCase):
    def test_exact_receipt_claim_and_identity(self):
        bound = B.expected(RUN, 544, 'mstop')
        self.assertEqual(bound, dict(run=RUN, step=544, namespace='8865619b', generation='mstop',
                                    object=OBJECT, done=DEPLOY+'gcs_469ddece_m544.done',
                                    claim=DEPLOY+'gcs_469ddece_mstop.claim'))
        self.assertEqual(B.parse(RAW, bound, b'm544\n'), dict(object=OBJECT, bytes=21583032320,
                         sha256='3ed73aead82cb0bb6468321256ea25e8fdaa5a2963da31062fdf8874bda2d4c7'))
        for claim in (None, b'm543\n', b'm544', b'm544\r\n', b'm544\n\n', b'mstop\n'):
            with self.subTest(claim=claim), self.assertRaisesRegex(ValueError, 'Stop claim differs'):
                B.parse(RAW, bound, claim)
        for raw in (RAW.replace(b'mstop', b'm544'), RAW.replace(b'469ddece', b'359fcc3c'),
                    RAW.replace(b'8865619b', b'00000000'), RAW+b'extra'):
            with self.assertRaises(ValueError):
                B.parse(raw, bound, b'm544\n')
        # The legacy unclaimed m544 receipt remains refused.
        with self.assertRaisesRegex(ValueError, 'Invalid completion receipt identity'):
            E.parse_done(RAW.replace(b'mstop', b'm544'), RUN, 544)

    def test_other_steps_generations_and_namespaces_refuse(self):
        for step in (-1, 0, 1, 100, 137, 200, 543, 544, 545, 600, 800, 1000, True, 544.0, '544'):
            for generation in (None, 'm100', 'm544', 'mstop', 'mstopB', 'mstopC', 'mstopD'):
                if type(step) is int and step == 544 and generation == 'mstop':
                    continue
                with self.subTest(step=step, generation=generation):
                    with self.assertRaisesRegex(ValueError, 'Unregistered export identity'):
                        B.expected(RUN, step, generation)
                    dest = folder()/'prepared'
                    with self.assertRaises(ValueError):
                        L.prepare('a000000001', dest, step, run=RUN, generation=generation, families=['a7'])
                    self.assertFalse(dest.exists())
        with self.assertRaises(ValueError):
            B.expected(RUN, 544, 'mstop', '00000000')

    def test_cli_prepare_embeds_binding_and_preserves_reader(self):
        dest = folder()/'prepared'
        argv = ['launcher', 'prepare', '--run', RUN, '--namespace', '8865619b', '--step', '544',
                '--generation', 'mstop', '--families', 'a7', '--token', 'a000000001', '--destination', str(dest)]
        with patch.object(sys, 'argv', argv), redirect_stdout(io.StringIO()):
            L.main()
        cfg = json.loads((dest/'CONFIG.json').read_text())
        L.validate_request(cfg)
        script = (dest/'BATCH.sh').read_text()
        L.validate_batch(script, cfg)
        self.assertEqual(cfg['mode'], 'production')
        self.assertEqual(cfg['families'], ['a7'])
        self.assertEqual(cfg['extra']['items'], 2169)
        self.assertEqual(cfg['spec']['artifact']['path'], str(J.FSW/'ap/8865619b/runs/469ddece/m544/artifact.json'))
        encoded = re.search(r"raw=base64.b64decode\('([^']+)'", script)[1]
        boot = folder()
        with tarfile.open(fileobj=io.BytesIO(base64.b64decode(encoded))) as archive:
            for entry in archive:
                p = boot/entry.name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(archive.extractfile(entry).read())
        for name in ('binding.py', 'export_stage.py', 'orchard_launcher.py'):
            self.assertEqual((boot/'bootstrap'/name).read_bytes(), (ROOT/'kit/launcher'/name).read_bytes())
        self.assertEqual(json.loads((boot/'bootstrap/CONFIG.json').read_text())['spec']['export_binding'], B.expected(RUN, 544, 'mstop'))
        with patch.object(sys, 'argv', ['job', '--root', str(boot), '--config', str(boot/'bootstrap/CONFIG.json')]), patch.object(J, 'run', return_value=0) as run:
            with self.assertRaises(SystemExit) as stop:
                J.main()
            self.assertEqual(stop.exception.code, 0)
            run.assert_called_once()
        for old_run, step in (('359fcc3c', 200), ('359fcc3c', 100), ('17c4ffa4', 100)):
            old = L.prepare('a000000001', folder()/'prepared', step, run=old_run, families=['a7'])
            for field in ('payload_pins', 'payload_sha256', 'extra', 'assets'):
                self.assertEqual(cfg[field], old[field])
        for families in (None, ['main'], ['a7', 'main'], ['main', 'away', 'forward', 'a7']):
            with self.assertRaisesRegex(ValueError, 'a7 only'):
                L.prepare('a000000001', folder()/'prepared', 544, run=RUN, generation='mstop', families=families)
            if families is not None:
                bad = copy.deepcopy(cfg)
                bad['families'] = bad['spec']['families'] = families
                bad['plan_sha256'] = L.canonical(bad['spec'])
                with self.assertRaisesRegex(ValueError, 'a7 only'):
                    L.validate_request(bad)

    def transport(self, corrupt=None, claim=b'm544\n'):
        root = folder()
        (root/'archives').mkdir()
        (root/'bootstrap').mkdir()
        bound = B.expected(RUN, 544, 'mstop')
        chunks = [b'one', b'two', b'three', b'four']
        body = b''.join(chunks)
        digest = '0'*64 if corrupt == 'sha' else hashlib.sha256(body).hexdigest()
        size = len(body)+(1 if corrupt == 'size' else -1 if corrupt == 'overflow' else 0)
        receipt = root/'input.done'
        receipt.write_text(f'{OBJECT} {size} {digest}\n')
        claim_file = root/'input.claim'
        claim_file.write_bytes(claim)
        seen = []
        @contextmanager
        def stream(argv, env, log):
            seen.append(argv[-1])
            yield io.BytesIO(chunks[len(seen)-1])
        def path(value):
            return receipt if str(value) == bound['done'] else claim_file if str(value) == bound['claim'] else Path(value)
        cfg = dict(spec=dict(step=544, export_binding=bound, artifact={}, models={}), assets=dict(gcloud_config='fixture'))
        with patch.object(E, 'Path', path), patch.object(S, 'room') as room, patch.object(S, 'cloud_environment', return_value={}), patch.object(S, 'process_stream', stream), patch.object(E, 'stage_export', return_value=dict(artifact_sha256='a'*64)) as stage:
            if corrupt or claim != b'm544\n':
                with self.assertRaises(ValueError):
                    E.fetch_and_stage(root, cfg)
                stage.assert_not_called()
                self.assertFalse((root/'archives/export.tar').exists())
            else:
                E.fetch_and_stage(root, cfg)
                args = stage.call_args.args[0]
                self.assertEqual((args.run, args.step, args.full), (RUN, 544, True))
                self.assertEqual((root/'archives/export.tar').read_bytes(), body)
            if claim != b'm544\n':
                room.assert_not_called()
                self.assertEqual(seen, [])
            else:
                self.assertEqual(seen, ['gs://cmu-gpucloud-jjyeung/'+OBJECT+'.part%02d-of-04'%i for i in range(4)])

    def test_four_parts_require_whole_size_and_digest(self):
        for corrupt in (None, 'sha', 'size', 'overflow'):
            with self.subTest(corrupt=corrupt):
                self.transport(corrupt)

    def test_wrong_claim_refuses_before_reservation_or_cloud(self):
        self.transport(claim=b'm543\n')

    def test_lineage_and_stage_reject_other_steps(self):
        for step in (1, 100, 200, 543, 545, 1000):
            with self.assertRaisesRegex(ValueError, 'Export lineage differs'):
                E.logical_artifact(None, str(J.FSW/f'ap/8865619b/runs/{RUN}/m{step}/artifact.json'), step)
            with self.assertRaisesRegex(ValueError, 'Require an allowed run and positive step'):
                E.stage_export(NS(run=RUN, step=step, root='/tmp/unused'))

    def test_full_checker_and_archive_admission_at_544(self):
        spec = importlib.util.spec_from_file_location('step544_checker', ROOT/'kit/reader/out/export_check.py')
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        for bad in (None, 'artifact_step', 'weights_path', 'shard_hash', 'tensor_shape', 'tar_step'):
            with self.subTest(bad=bad):
                root = folder()
                job = root/'job'
                logical = str(J.FSW/'ap/8865619b/runs/469ddece/m544/artifact.json')
                physical = J.physical(job, logical)
                base = root/'base'
                base.mkdir()
                def tensor(shape):
                    header = json.dumps({'weight': dict(dtype='BF16', shape=shape, data_offsets=[0, 2])}).encode()
                    return struct.pack('<Q', len(header))+header+b'00'
                (base/'model.safetensors').write_bytes(tensor([1]))
                shard = tensor([2] if bad == 'tensor_shape' else [1])
                index = json.dumps(dict(weight_map={'weight': 'model.safetensors'})).encode()
                manifest = json.dumps(dict(schema='full-ft-export-v1', dtype='bfloat16', tensor_count=1,
                    index=dict(name='model.safetensors.index.json', sha256=hashlib.sha256(index).hexdigest()),
                    files=[dict(name='model.safetensors', bytes=len(shard), tensors=1,
                                sha256='0'*64 if bad == 'shard_hash' else hashlib.sha256(shard).hexdigest())])).encode()
                artifact = json.dumps(dict(schema='carrier-c1-artifact-v1', step=543 if bad == 'artifact_step' else 544,
                    full_weights=dict(path=str(root/'wrong.json' if bad == 'weights_path' else physical.parent/'full_weights/full_weights.json'),
                                      sha256=hashlib.sha256(manifest).hexdigest()))).encode()
                data = {'artifact.json': artifact, 'heads.pt': b'fixture', 'full_weights/full_weights.json': manifest,
                        'full_weights/model.safetensors.index.json': index, 'full_weights/model.safetensors': shard}
                archive = root/'input.tar'
                with tarfile.open(archive, 'w') as tf:
                    for name, value in data.items():
                        entry = tarfile.TarInfo(('m543/' if bad == 'tar_step' else 'm544/')+name)
                        entry.size = len(value)
                        tf.addfile(entry, io.BytesIO(value))
                done = root/'COMPLETE.json'
                done.write_text(json.dumps(dict(object=OBJECT, bytes=archive.stat().st_size, sha256=S.sha(archive))))
                def check(root, artifact, digest, step, full, receipt_dir, bwrap):
                    self.assertTrue(full)
                    return checker.check_export(J.physical(root, artifact), digest, base, step)
                args = NS(root=str(job), run=RUN, step=544, tar=str(archive), done=str(done), full=True, bwrap='fixture')
                with patch.object(E.T, 'writable', side_effect=Path), patch.object(E, 'completed_local', side_effect=lambda p, tar=False: Path(p)), patch.object(S, 'room'), patch.object(E, 'run_export_checker', side_effect=check) as called:
                    if bad:
                        with self.assertRaises(ValueError):
                            E.stage_export(args)
                        if bad == 'tar_step':
                            called.assert_not_called()
                    else:
                        result = E.stage_export(args)
                        self.assertEqual((result['status'], result['checker']['status'], result['checker']['step']), ('complete', 'VERIFIED', 544))
                        self.assertEqual(result['artifact_sha256'], hashlib.sha256(artifact).hexdigest())
                        with self.assertRaisesRegex(ValueError, 'no overwrite or retry'):
                            E.stage_export(args)


if __name__ == '__main__':
    unittest.main()
