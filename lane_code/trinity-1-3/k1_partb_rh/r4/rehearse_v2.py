"""CPU phase/transport rehearsal; separately report every substituted boundary."""
from copy import deepcopy
import dis
import json
import os
from pathlib import Path
import sys
import time
import types
import uuid

ROOT = Path(__file__).resolve().parent
META = Path(os.environ.get('A_META', '/scratch/jjyeung/orch_n30/k1_ops3/work/partb/meta/e10fbb95.tar'))

def statements(code):
    result = {line for _,line in dis.findlinestarts(code) if line > 0}
    for child in code.co_consts:
        if isinstance(child, types.CodeType):
            result |= statements(child)
    return result

def main():
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    run = ROOT / 'evidence' / ('v2_' + uuid.uuid4().hex[:10])
    run.mkdir(parents=True)
    hits = {}
    prefixes = (str(ROOT), '/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a',
                '/scratch/jjyeung/orch_cd/k1_build/work/kit_k1a',
                '/scratch/jjyeung/orch_cd/evalx/work/milestone/native_package_s24_05',
                '/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872')
    def trace(frame, event, arg):
        name = frame.f_code.co_filename
        if not name.endswith('.py') or not name.startswith(prefixes):
            return None
        if event == 'line':
            hits.setdefault(name, set()).add(frame.f_lineno)
        return trace
    sys.settrace(trace)
    evidence = dict(full_job_rehearsal=False, synthetic=True, substitutions=[], failures=[])
    try:
        import job_support as H
        import phase_worker as W
        from rh_coverage import instrument_observer
        instrument_observer(W, hits)
        evidence['observer_coverage'] = 'Executed AST probes in the in-memory observer; source bytes unchanged'
        sys.path[:0] = [str(W.KIT / 'work'), str(W.KIT / 'native_kit')]
        import bindings as B
        import boundaries
        import k1_phases as F
        import k1_pipeline as P
        from PIL import Image
        S, R, NS, J = H.native()
        import stage_fixture
        evidence['staging_controller'] = stage_fixture.run(run / 'staging')
        config = json.loads((ROOT / 'packet/CONFIG.json').read_text())
        config['deadline_unix'] = None
        production = B.load(ROOT / 'manifest_v2/a40fbc19.json')
        metadata = config['assets']['small_objects'][1]
        mapping = {}
        trainer_archive = ROOT / 'payload/a845b1789.tar'
        if trainer_archive.is_file() and H.sha(trainer_archive) == config['assets']['trainer']['sha256']:
            mapping[config['assets']['trainer_logical_archive']] = str(trainer_archive)
        model_archive = Path(os.environ.get('A_MODEL', str(ROOT / 'inputs/model.tar')))
        if model_archive.is_file():
            model_pin = config['assets']['small_objects'][3]
            assert model_archive.stat().st_size == model_pin['bytes'] and H.sha(model_archive) == model_pin['sha256']
            inventory = H.unpack(S, model_archive, run / 'model')
            NS.verify_inventory(inventory, model_pin['members'])
            for member in inventory:
                assert member.startswith('fsw/')
                mapping[str(J.FSW / member.removeprefix('fsw/'))] = str(run / 'model' / member)
        real = META.exists() and META.stat().st_size == metadata['bytes']
        if real:
            assert H.sha(META) == metadata['sha256']
            # Native copy_parts verifies the archive before native extraction.
            local = dict(metadata, path=str(META))
            S.copy_parts([local], run / 'a.tar', lambda p: Path(p['path']).open('rb'), expected_sha=metadata['sha256'])
            inventory = H.unpack(S, run / 'a.tar', run / 'metadata')
            NS.verify_inventory(inventory, metadata['members'])
            for member in inventory:
                if member.startswith('fsw/'):
                    logical = str(J.FSW / member.removeprefix('fsw/'))
                elif member.startswith('sj/'):
                    logical = str(J.SJ / member.removeprefix('sj/'))
                else:
                    raise ValueError('Unexpected metadata namespace')
                mapping[logical] = str(run / 'metadata' / member)
            try:
                evidence['prepared'] = W.prepared(production, mapping)
            except Exception as error:
                evidence['prepared'] = dict(passed=False, type=type(error).__name__, error=str(error))
                tb = error.__traceback__
                while tb:
                    if tb.tb_frame.f_code.co_filename.endswith('/read_runtime.py') and tb.tb_frame.f_code.co_name == 'prepared':
                        evidence['prepared'].update(last_native_line=tb.tb_lineno,
                            config_identity=tb.tb_frame.f_locals.get('identity'),
                            all_native_guards_before_model_lookup_passed=tb.tb_lineno == 71)
                    tb = tb.tb_next
        else:
            evidence['prepared'] = dict(passed=False, reason='Metadata archive missing or wrong size',
                                       expected_bytes=metadata['bytes'], actual_bytes=META.stat().st_size if META.exists() else None)
        if not evidence['prepared'].get('passed'):
            evidence['substitutions'].append('prepared unavailable: independent fixture execution only')
            W.prepared = lambda *args, **kwargs: dict(passed=False, skipped=True, reason=evidence['prepared'])
        # Fixture input changes are confined to a separately hashed manifest.
        image = run / 'a.png'
        Image.new('RGB', (4,4), (20,30,40)).save(image)
        fixture = deepcopy(production)
        for capture in fixture['captures']:
            for frame in capture['dense_frames']:
                frame.update(B.pin(image))
            capture['model_row']['student_input']['frames'] = [dict(capture['dense_frames'][i]) for i in capture['anchor_slots']]
        if not real:
            small = run / 'a.json'
            H.dump(small, dict(synthetic=True))
            fixture['gpu'].update(config=B.pin(small), data_receipt=B.pin(small))
        H.dump(run / 'manifest.json', fixture)
        short = deepcopy(fixture)
        short['captures'] = short['captures'][:6]
        evidence['substitutions'] += ['9600 anchor reads use one synthetic image', 'six-capture phase subset after full 300-capture fixture preflight',
                                     'CPU.own replaces the GPU boundary', 'fixture monotonic clock', 'local cloud and pool stand-ins',
                                     'production runtime/bootstrap and export/base staging not executed']
        clock = types.SimpleNamespace(now=0.)
        class Boundary(boundaries.CPU):
            def __init__(self):
                self.calls = []
            def own(self, capture, images, state):
                self.calls.append(capture['canonical'])
                clock.now += 1
                return super().own(capture, images, state)
        boundary = Boundary()
        original_time = F.time
        F.time = types.SimpleNamespace(monotonic=lambda: clock.now, time=time.time)
        config.update(manifest=str(run / 'manifest.json'), manifest_sha256=H.sha(run / 'manifest.json'),
                      metadata_mapping=mapping, pool=str(run / 'pool'), cloud=str(run / 'cloud'),
                      pointer=str(run / 'pool/a.json'), started_unix=time.time(), captures_unchanged=False)
        evidence['probe'] = H.probe(config['pool'], run)
        try:
            config['source'] = str(run / 'first')
            one = W.run(config, dict(manifest=short, boundary=boundary, max_seconds=3))
            assert one['code'] == 4 and len(boundary.calls) == 3 and one['canary_returned']
            pins = {p.name: H.sha(p) for p in (run / 'first/native/probe').glob('*/PHASE_COMPLETE.json')}
            config['source'] = str(run / 'second')
            two = W.run(config, dict(manifest=short, boundary=boundary, max_seconds=100))
            assert two['code'] == 0 and len(boundary.calls) == 6 and two['canary_returned']
            assert len(list((run / 'second/native/probe').glob('*/PHASE_COMPLETE.json'))) == 6
            for p in (run / 'first/native/probe').glob('*/PHASE_COMPLETE.json'):
                assert H.sha(p) == H.sha(run / 'second/native/probe' / p.parent.name / p.name)
            evidence['resume'] = dict(first=one['code'], second=two['code'], total_boundary_calls=len(boundary.calls),
                                      first_commits=3, final_commits=6, restored=True, first_receipts_unchanged=True)
            evidence['canary'] = json.loads((run / 'first/metadata/CANARY.json').read_text())
            evidence['returns'] = [one['return_receipt'], two['return_receipt']]
            for returned in evidence['returns']:
                assert json.loads((Path(returned['local_return']) / 'EXIT.json').read_text())['synthetic'] is True
            config.update(source=str(run / 'failure'), pointer=str(run / 'pool/no_resume.json'), canary_limit_seconds=0)
            try:
                W.run(config, dict(manifest=short, boundary=boundary, max_seconds=100))
            except ValueError:
                assert (run / 'failure/native/probe/STOP').is_file()
                assert len(list((run / 'failure/native/probe').glob('*/PHASE_COMPLETE.json'))) == 3
                evidence['canary_failure_stops'] = True
            else:
                raise AssertionError('Failed canary continued')
            config.update(source=str(run / 'budget_first'), pointer=str(run / 'pool/b.json'),
                          canary_limit_seconds=3000, started_unix=time.time())
            class BudgetBoundary(Boundary):
                def own(self, capture, images, state):
                    value = super().own(capture, images, state)
                    if len(self.calls) == 1:
                        config['started_unix'] = time.time() - 40000
                    return value
            bounded = BudgetBoundary()
            stopped = W.run(config, dict(manifest=short, boundary=bounded, max_seconds=100))
            assert stopped['code'] == 4 and len(bounded.calls) == 1
            assert (run / 'budget_first/native/probe/STOP').read_text().strip() == 'RESUME'
            config.update(source=str(run / 'budget_second'), started_unix=time.time())
            resumed = W.run(config, dict(manifest=short, boundary=bounded, max_seconds=100))
            assert resumed['code'] == 0 and len(bounded.calls) == 6
            evidence['allocation_budget_resume'] = dict(passed=True, first_commits=1, final_calls=6,
                                                        marker='RESUME', no_deletion=True)
            config.update(source=str(run/'expired'),pointer=str(run/'pool/expired.json'),
                          started_unix=time.time(),deadline_unix=time.time()-1)
            expired_boundary = Boundary()
            expired = W.run(config, dict(manifest=short,boundary=expired_boundary,max_seconds=100))
            assert expired['code'] == 4 and not expired_boundary.calls
            assert (run/'expired/native/probe/STOP').read_text().strip() == 'RESUME'
            assert not (run/'expired/FAILED.json').exists()
            assert (run/'pool/expired.json').is_file()
            config.update(source=str(run/'expired_resume'),started_unix=time.time(),deadline_unix=None)
            resumed_empty = W.run(config, dict(manifest=short,boundary=expired_boundary,max_seconds=100))
            assert resumed_empty['code'] == 0 and len(expired_boundary.calls) == 6
            evidence['expired_deadline'] = dict(passed=True,captures=0,marker='RESUME',pointer_advanced=True,
                                               resumed_captures=6)
        finally:
            F.time = original_time
        evidence['component_rehearsal_passed'] = True
    except Exception as error:
        evidence['failures'].append(dict(type=type(error).__name__, message=str(error)))
        import traceback
        (run / 'failure.log').write_text(traceback.format_exc())
    finally:
        sys.settrace(None)
    for name in ('batch_entry.py','stage_job.py','phase_worker.py','job_support.py','phase_support.py'):
        hits.setdefault(str(ROOT / name), set())
    hits.setdefault(str(W.NATIVE / 'read_runtime.py'), set())
    hits.setdefault('/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872/student_pilot/carrier_c1_decode.py', set())
    coverage = {}
    for filename, observed in sorted(hits.items()):
        if not Path(filename).is_file():
            continue
        possible = statements(compile(Path(filename).read_text(), filename, 'exec'))
        coverage[filename] = dict(executed=len(observed & possible), total=len(possible),
                                  sha256=H.sha(filename), executed_lines=sorted(observed & possible), unexecuted_lines=sorted(possible-observed))
    H.dump(run / 'COVERAGE.json', coverage)
    H.dump(run / 'RESULT.json', evidence)
    H.dump(ROOT / 'evidence/V2_LATEST.json', dict(run=str(run)))
    print(json.dumps(dict(run=str(run), passed=evidence.get('component_rehearsal_passed', False),
                          prepared=evidence.get('prepared'), failures=evidence['failures'])))
    return 0 if evidence.get('component_rehearsal_passed') else 1

if __name__ == '__main__':
    raise SystemExit(main())
