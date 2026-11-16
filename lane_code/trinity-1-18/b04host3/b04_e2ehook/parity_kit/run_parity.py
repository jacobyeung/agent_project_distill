"""One reader process per card; append complete, scored items and resume by key."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import time

from parity_kit.common import (C8R, DENSE, FRAMES, LANE, OLD_LOAD, REQUEST, TASKS, install, key, pin, policy, read, rows, sha, tasks, write)
from parity_kit.provenance import digest, receipt_digest, runtime_identity, validate_rows


def arguments(cpu=False):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--settings', required=True)
    p.add_argument('--arm', choices=['own_depth', 'scale_head'], required=True)
    group = p.add_mutually_exclusive_group()
    group.add_argument('--keys', help='JSON list or one key per line')
    group.add_argument('--types', nargs='+')
    p.add_argument('--out', required=True)
    p.add_argument('--device', default='cpu' if cpu else 'cuda:0')
    return p.parse_args()


def select(settings, keys=None, types=None):
    selected = tasks(settings)
    if keys is not None:
        wanted = set(keys)
        missing = wanted - {key(t) for t in selected}
        if missing:
            raise ValueError('unknown keys: ' + str(sorted(missing)))
        selected = [t for t in selected if key(t) in wanted]
    if types:
        missing = set(types) - {t['question_type'] for t in selected}
        if missing:
            raise ValueError('unknown types: ' + str(sorted(missing)))
        selected = [t for t in selected if t['question_type'] in types]
    if not selected:
        raise ValueError('empty selection')
    return selected


def configure_output(out):
    """Contain caches and temporary output of imported libraries under the output directory."""
    out.mkdir(parents=True, exist_ok=True)
    os.environ['TMPDIR'] = str(LANE / 'work/tmp')
    for env, name in [('XDG_CACHE_HOME', 'cache'), ('HF_HOME', 'hf'),
                      ('TRITON_CACHE_DIR', 'triton'), ('TORCH_HOME', 'torch')]:
        path = out / name
        path.mkdir(exist_ok=True)
        os.environ[env] = str(path)
    install()


def run(settings, selected, out, *, device, settings_path=None):
    out = Path(out).resolve()
    configure_output(out)
    # The lock lives in OUT and stays present; flock prevents simultaneous appenders.
    with (out / 'RUN.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        request = read(settings.get('request', REQUEST))
        if (request['decode_budget'] != policy().DECODE_BUDGET or request['prompt_flag'] is not None
                or request['arm'] not in ('unflagged', 'paired') or request['layout'] != 'duplicate'):
            raise ValueError('request prompt, budget, arm, or layout differs from 170056')
        artifact_spec = settings['artifact_manifest']
        if isinstance(artifact_spec, str):
            artifact_spec = read(artifact_spec)
        inputs = {n: pin(settings.get(n, default)) for n, default in
                  [('frames_json', FRAMES), ('dense_manifest', DENSE)]}
        inputs['config'] = pin(settings['config'])
        inputs['request'] = pin(settings.get('request', REQUEST))
        inputs['tasks'] = [pin(p) for p in settings.get('tasks', TASKS)]
        inputs['settings'] = settings
        inputs['runtime_code'] = [pin(p) for directory in ('parity_kit', 'e2e_reader')
                                  for p in sorted((LANE / directory).glob('*.py'))] + [
                                      pin(C8R / 'reader_policy.py')]
        restore = read(Path(settings['export_dir']) / 'RESTORE.json')
        dense = read(settings.get('dense_manifest', DENSE))['captures']
        runtime = runtime_identity(settings, device)
        receipt = dict(schema='parity-load-v2', arm=settings['arm'], device=device, inputs=inputs,
                       settings_sha256=digest(settings), runtime_identity=runtime,
                       runtime_identity_sha256=digest(runtime),
                       artifact_manifest=artifact_spec, restore=restore,
                       restore_pin=pin(Path(settings['export_dir']) / 'RESTORE.json'),
                       parity_selection=read(settings.get('old_load_receipt', OLD_LOAD))['parity_selection'],
                       keys=[key(t) for t in selected],
                       dense_frame_counts={key(t): len(dense[t['native']]['frames']) for t in selected},
                       decode_budget=dict(thinking_tokens=2048, answer_tokens=64, max_new_tokens=16384),
                       reader_differences=['CallHook detects calls up to 1024 tokens; Orchard uses 96.',
                                          'CallHook has no 200-call limit.',
                                          'Unserved calls emit no response; room has no server.',
                                          'Own-depth scaling omits the Orchard depth range gate.',
                                          'Ground/gap use the configured SAM3/selector socket.',
                                          'Use each capture\'s pinned 32 or 64 dense frames; never fabricate extra frames.'])
        receipt_path = out / 'LOAD_RECEIPT.json'
        if receipt_path.exists() and read(receipt_path) != receipt:
            raise ValueError('resume load receipt differs; use a new output directory')
        if receipt_path.exists() and sha(receipt_path) != receipt_digest(receipt):
            raise ValueError('resume load receipt bytes differ; use a new output directory')
        journal = out / 'items.jsonl'
        existing = rows(journal) if journal.exists() else []
        if existing and not receipt_path.exists():
            raise ValueError('cannot resume items without a load receipt')
        binding = validate_rows(existing, receipt, receipt_digest(receipt))
        done = {r['key'] for r in existing}
        write(receipt_path, receipt)
        pending = [t for t in selected if key(t) not in done]
        if not pending:
            return existing
        from e2e_reader.parity import make_real
        t0 = time.perf_counter()
        gen = make_real(settings['export_dir'], artifact_spec, selected, device=device, settings=settings)
        write(out / 'LOAD_TIMING.json', dict(seconds=time.perf_counter() - t0))
        with journal.open('a') as f:
            for task in pending:
                result = gen(task)
                if result['key'] != key(task) or result.get('arm', settings['arm']) != settings['arm']:
                    raise ValueError('generated item key or arm differs')
                result.update(binding)
                f.write(json.dumps(result, allow_nan=False) + '\n')
                f.flush()
                os.fsync(f.fileno())
                existing.append(result)
                print(json.dumps(dict(key=result['key'], scores=result['scores'], seconds=result['seconds'])), flush=True)
        return existing


def main():
    a = arguments()
    settings = dict(read(a.settings), arm=a.arm)
    keys = None
    if a.keys:
        text = Path(a.keys).read_text()
        keys = json.loads(text) if text.lstrip().startswith('[') else text.split()
    run(settings, select(settings, keys, a.types), a.out, device=a.device, settings_path=a.settings)


if __name__ == '__main__':
    main()
