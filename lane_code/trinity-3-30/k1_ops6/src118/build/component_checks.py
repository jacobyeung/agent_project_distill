"""CPU component evidence, explicitly not a complete production-job rehearsal."""
import ast
from copy import deepcopy
import dis
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import time
import types
import uuid

from build_sources import ROOT, KIT, MANIFEST, TOWER


def executable_lines(code):
    result = {line for _, line in dis.findlinestarts(code) if line > 0}
    for value in code.co_consts:
        if isinstance(value, types.CodeType):
            result.update(executable_lines(value))
    return result


def main():
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('CPU checks require CUDA_VISIBLE_DEVICES to be empty')
    run = ROOT / 'evidence' / ('check_' + uuid.uuid4().hex[:10])
    run.mkdir()
    native = ROOT / 'reference/sj/orch_cd/evalx/work/milestone'
    sys.path[:0] = [str(KIT / 'work'), str(KIT / 'native_kit'), str(native), str(native / 'orchard_native')]
    monitored = {str(p) for base in (KIT / 'work', KIT / 'native_kit', native,
                                    native / 'orchard_native') for p in base.glob('*.py')}
    monitored.update(str(ROOT / p) for p in ('phase_support.py', 'component_checks.py'))
    hits = {name: set() for name in monitored}

    def trace(frame, event, arg):
        if event == 'line' and frame.f_code.co_filename in hits:
            hits[frame.f_code.co_filename].add(frame.f_lineno)
        return trace

    sys.settrace(trace)
    try:
        import phase_support as support
        import bindings as B
        import boundaries
        import k1_phases as F
        import k1_pipeline as P
        import verify_sources
        import orchard_stage as S
        import orchard_results as R
        import native_stage as NS
        from PIL import Image

        evidence = dict(scope='CPU component checks only', full_job_rehearsal=False,
                        synthetic=True, source_files=verify_sources.verify())
        manifest = B.load(MANIFEST)
        evidence['binding'] = support.compare_binding(B, F, manifest, B.load(TOWER))
        evidence['space'] = support.space_report(dict(workspace=ROOT, staging=run, output=run))
        try:
            support.require_manifest_pins(manifest)
        except ValueError as error:
            evidence['production_admission_refusal'] = str(error)
        else:
            raise AssertionError('The production manifest must fail before staging')

        # Directly exercise the unchanged byte-hash guard with the impossible pin.
        receipt = run / 'a.json'
        receipt.write_text('{"fixture": true}\n')
        try:
            B.checked(dict(path=str(receipt), sha256=manifest['gpu']['data_receipt']['sha256']))
        except ValueError as error:
            evidence['impossible_pin_refusal'] = str(error)
        else:
            raise AssertionError('Literal REQUIRED cannot pass SHA256 validation')

        # Stage a tiny local object through the native transfer and extraction code.
        object_file = run / 'a.tar'
        with tarfile.open(object_file, 'w') as archive:
            data = b'fixture transport\n'
            entry = tarfile.TarInfo('a.bin')
            entry.size = len(data)
            archive.addfile(entry, io.BytesIO(data))
        pin = dict(path=str(object_file), bytes=object_file.stat().st_size, sha256=B.sha(object_file))
        staged = run / 'b.tar'
        evidence['staging'] = S.copy_parts([pin], staged, lambda p: Path(p['path']).open('rb'),
                                            expected_sha=pin['sha256'])
        evidence['extracted'] = S.unpack(staged, run / 'unpacked')
        evidence['path_mapping'] = str(NS.physical(run, str(KIT)))
        assert evidence['path_mapping'] == str(run / 'sj' / KIT.relative_to('/scratch/jjyeung'))

        # Exercise check_manifest on all 300 captures with tiny, explicitly synthetic
        # frame and metadata pins. This is a distinct manifest, never a production pin.
        image = run / 'frame.png'
        Image.new('RGB', (4, 4), color=(20, 30, 40)).save(image)
        fixture = deepcopy(manifest)
        image_pin = B.pin(image)
        for capture in fixture['captures']:
            for frame in capture['dense_frames']:
                frame.update(image_pin)
            capture['model_row']['student_input']['frames'] = [
                dict(capture['dense_frames'][i]) for i in capture['anchor_slots']]
        fixture['gpu'].update(config=B.pin(receipt), data_receipt=B.pin(receipt))
        P.check_manifest(fixture, 'own')
        evidence['fixture_check_manifest'] = dict(captures=300, passed=True,
                                                 production_frames_checked=False,
                                                 preparation_validated=False)

        # Run the unchanged phase with six synthetic captures. A fixture clock
        # advances one second per boundary call, making max-seconds deterministic.
        fixture['captures'] = fixture['captures'][:6]
        source = run / 'return_source'
        output = source / 'native/probe'
        clock = types.SimpleNamespace(now=0.0)
        actual_time = F.time
        F.time = types.SimpleNamespace(monotonic=lambda: clock.now, time=time.time)

        class Fixture(boundaries.CPU):
            def __init__(self):
                self.calls = []

            def own(self, capture, images, state):
                self.calls.append(capture['canonical'])
                clock.now += 1
                return super().own(capture, images, state)

        boundary = Fixture()
        try:
            first = F.run(fixture, output, boundary, 'own', 3)
            assert first == 4 and len(boundary.calls) == 3
            committed = {str(p): B.sha(p) for p in output.glob('*/PHASE_COMPLETE.json')}
            evidence['canary'] = support.canary(B, F, fixture, output, True, 600)
            assert evidence['canary']['passed']
            support.refuse_incomplete(B, fixture, output)
            second = F.run(fixture, output, boundary, 'own', 100)
            assert second == 0 and len(boundary.calls) == 6
            assert all(B.sha(p) == digest for p, digest in committed.items())
        finally:
            F.time = actual_time
        evidence['resume'] = dict(first_returncode=first, second_returncode=second,
                                  first_commits=3, total_boundary_calls=len(boundary.calls),
                                  unchanged_commits=len(committed), clock='fixture monotonic clock',
                                  same_root=str(output), production_binding=False)
        evidence['budget_example'] = support.budget(1800, 116.8, 600)

        # Native publisher: preserve its pool code and emulate only cloud transport.
        # Put the phase root in a directory selected by unchanged chain_save.members.
        manifest_of_files = {str(p.relative_to(output)): B.sha(p)
                             for p in output.rglob('*') if p.is_file()}
        B.write(output / 'SHA256.json', manifest_of_files)
        B.write(source / 'COMPLETE.json', dict(plan_sha256=B.digest(fixture), synthetic=True))
        (source / 'logs').mkdir()
        (source / 'logs/job.log').write_text('CPU component fixture; no GPU or remote access.\n')
        pool = native / 'test_runs' / run.name
        pool.mkdir(parents=True)
        cloud = run / 'cloud'
        cloud.mkdir()

        def local_upload(local, token, names=('result.tar.gz', 'EXIT.json'), cloud_config=None):
            target = cloud / token
            target.mkdir(exist_ok=True)
            objects = {}
            for name in names:
                data = (Path(local) / name).read_bytes()
                (target / name).write_bytes(data)
                digest = B.sha(target / name)
                assert digest == B.sha(Path(local) / name)
                objects[name] = dict(bytes=len(data), sha256=digest, verified=True,
                                     generation='LOCAL_FIXTURE')
            return dict(verified=True, fixture=True, objects=objects)

        old_upload, old_operation = R.upload, R.pool_operation
        R.upload = local_upload
        # Inline the unchanged worker for coverage and avoid child-process timeouts
        # that could kill a child. No deadline/transport equivalence is claimed.
        R.pool_operation = lambda action, pool, token, local=None, timeout=60, rate=4*1024**2: R.pool_worker(
            action, pool, token, rate, local)
        try:
            returned = R.publish(source, pool, 'a' + uuid.uuid4().hex[:12], B.digest(fixture), 0,
                                 synthetic=True, mode='full')
        finally:
            R.upload, R.pool_operation = old_upload, old_operation
        assert returned['returned'] and set(returned['verified_channels']) == {'pool', 'gcs'}
        evidence['return'] = returned
        with tarfile.open(Path(returned['local_return']) / 'result.tar.gz') as archive:
            names = set(archive.getnames())
            assert 'native/probe/PROGRESS.jsonl' in names and 'logs/job.log' in names
            assert 'native/probe/SHA256.json' in names
        # A failed canary writes STOP, and the fixed phase exits at its boundary.
        failed_canary = support.canary(B, F, fixture, output, False, 600)
        assert not failed_canary['passed'] and (output / 'STOP').is_file()
        assert F.run(fixture, output, boundary, 'own', 100) == 4
        evidence['canary_failure_stops'] = True
        evidence['unexecuted_requirements'] = [
            'Real anchors and immutable-manifest check_manifest success',
            'In-job production preparation and read_runtime.prepared',
            'Production runtime/bootstrap and namespace execution',
            'Real GPU boundary, wall-clock longest-capture calibration',
            'Pool write probe, remote transports, job-end snapshot and next-job restoration',
            'Complete Orchard wrapper and submit packet']
    finally:
        sys.settrace(None)

    coverage = {}
    for filename, observed in sorted(hits.items()):
        code = compile(Path(filename).read_text(), filename, 'exec')
        statements = executable_lines(code)
        coverage[filename] = dict(executed_lines=sorted(observed & statements),
                                  unexecuted_lines=sorted(statements - observed),
                                  executed=len(observed & statements), total=len(statements))
    (run / 'COVERAGE.json').write_text(json.dumps(coverage, indent=2) + '\n')
    (run / 'RESULT.json').write_text(json.dumps(evidence, indent=2) + '\n')
    (ROOT / 'evidence/LATEST.json').write_text(json.dumps(dict(run=str(run)), indent=2) + '\n')
    print(json.dumps(dict(run=str(run), passed=True, full_job_rehearsal=False,
                         source_files=evidence['source_files'], resume=evidence['resume']), indent=2))


if __name__ == '__main__':
    main()
