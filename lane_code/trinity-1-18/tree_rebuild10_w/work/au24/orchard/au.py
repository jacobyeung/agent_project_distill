#!/usr/bin/env python3
"""Pinned CPU audit. Modes: s (stage/run), r (one tree), d (local fixture)."""
import argparse
import base64
import collections
import contextlib
import gzip
import hashlib
import importlib.abc
import importlib.machinery
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import resource
import signal
import sqlite3
import subprocess
import sys
import tarfile
import time

LIMIT = 15 * 1024**3
resource.setrlimit(resource.RLIMIT_AS, (LIMIT, LIMIT))
sys.dont_write_bytecode = True


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(4 << 20), b''):
            h.update(b)
    return h.hexdigest()


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.au_0')
    with temp.open('w') as f:
        json.dump(value, f, sort_keys=True, indent=2, allow_nan=False)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp, path)


def read(path):
    return json.loads(Path(path).read_text())


def checked(path, spec):
    if spec.get('bytes') is not None and path.stat().st_size != spec['bytes']:
        raise ValueError('E_SIZE_' + spec.get('sha256', '')[:16])
    if spec.get('sha256') and sha(path) != spec['sha256']:
        raise ValueError('E_HASH_' + spec['sha256'][:16])
    return path


def locate(pool, spec):
    for rel in spec['paths']:
        p = PurePosixPath(rel)
        if p.is_absolute() or '..' in p.parts:
            raise ValueError('E_PATH')
        candidate = pool / rel
        # Read only the explicitly named pool paths, including existing pool aliases.
        if candidate.is_file():
            return candidate
    return None


def copy_stream(src, dst, spec):
    h, count = hashlib.sha256(), 0
    with dst.open('wb') as f:
        for b in iter(lambda: src.read(4 << 20), b''):
            h.update(b)
            count += len(b)
            f.write(b)
    if spec.get('bytes') is not None and count != spec['bytes']:
        raise ValueError('E_SIZE_' + spec.get('sha256', '')[:16])
    if spec.get('sha256') and h.hexdigest() != spec['sha256']:
        raise ValueError('E_HASH_' + spec['sha256'][:16])
    return dict(sha256=h.hexdigest(), bytes=count)


def stage_pin(pool, work, spec):
    dst = work / ('k_' + spec['sha256'])
    src = locate(pool, spec)
    if src is not None:
        with src.open('rb') as f:
            evidence = copy_stream(f, dst, spec)
        return dst, dict(evidence, source=str(src))
    arc = spec.get('archive')
    if arc is None:
        raise ValueError('E_MISSING_' + spec['sha256'][:16])
    src = locate(pool, arc)
    if src is None:
        raise ValueError('E_MISSING_' + arc.get('sha256', spec['sha256'])[:16])
    checked(src, arc)
    wanted = arc['member']
    found = False
    with tarfile.open(src, 'r:*') as t:
        for m in t:
            if m.name.removeprefix('./') != wanted:
                continue
            if found or not m.isfile():
                raise ValueError('E_MEMBER')
            with t.extractfile(m) as f:
                evidence = copy_stream(f, dst, spec)
            found = True
    if not found:
        raise ValueError('E_MEMBER_MISSING_' + spec['sha256'][:16])
    return dst, dict(evidence, source=str(src), member=wanted,
                     archive_sha256=arc.get('sha256'),
                     verification='member_sha256_and_size')


def extract_tree(src, dest, spec):
    checked(src, spec)
    dest.mkdir(parents=True, exist_ok=True)
    inventory = {}
    with tarfile.open(src, 'r:*') as t:
        for m in t:
            name = PurePosixPath(m.name)
            if (not m.isfile() or name.is_absolute() or '..' in name.parts
                    or m.name in inventory or m.size > 16000000):
                raise ValueError('E_TREE_MEMBER')
            raw = t.extractfile(m).read()
            h = hashlib.sha256(raw).hexdigest()
            if spec['files'].get(m.name) != h:
                raise ValueError('E_TREE_FILE')
            inventory[m.name] = h
            # The module loader preserves imports without creating descriptive paths.
            target = dest / ('k_' + h)
            if not target.exists():
                target.write_bytes(raw)
    value = hashlib.sha256(json.dumps(inventory, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    if inventory != spec['files'] or value != spec['seal']:
        raise ValueError('E_TREE_SEAL')
    return value


class TreeFinder(importlib.abc.MetaPathFinder):
    def __init__(self, root, files):
        self.root, self.files = Path(root), files

    def find_spec(self, fullname, path=None, target=None):
        rel = fullname.replace('.', '/')
        package = rel + '/__init__.py'
        module = rel + '.py'
        name = package if package in self.files else module
        if name not in self.files:
            if any(n.startswith(rel + '/') for n in self.files):
                result = importlib.machinery.ModuleSpec(fullname, None, is_package=True)
                result.submodule_search_locations = [str(self.root)]
                return result
            return None
        filename = str(self.root / ('k_' + self.files[name]))
        loader = importlib.machinery.SourceFileLoader(fullname, filename)
        return importlib.util.spec_from_file_location(fullname, filename, loader=loader,
            submodule_search_locations=[str(self.root)] if name == package else None)


def census(path, expected_count=None, expected_types=None, pulse=lambda n: None):
    fps, by_group, types, count = {}, {}, collections.Counter(), 0
    with sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro&immutable=1', uri=True) as db:
        db.execute('PRAGMA cache_size=-16384')
        for (encoded,) in db.execute('SELECT row FROM rows ORDER BY i'):
            row = json.loads(encoded)
            key = row['dataset'] + '/' + row['scene']
            value = row.get('student_input', {}).get('fps')
            if type(value) in (float, int) and math.isfinite(value) and value > 0:
                fps[key] = value if key not in fps or fps[key] == value else 'conflicting_rates'
                by_group.setdefault(row['dataset'], set()).add(value)
            types[row['routing']['question_type'] + ':' + row['routing']['category']] += 1
            count += 1
            if count % 2000 == 0:
                pulse(count)
    if expected_count is not None and count != expected_count:
        raise ValueError('E_COUNT')
    if expected_types is not None and dict(types) != expected_types:
        raise ValueError('E_TYPES')
    return dict(fps=fps, groups={k: sorted(v) for k, v in by_group.items()}, rows=count)


def empty_result(label, spec):
    return dict(status='PENDING', tree=label, seal=spec['seal'], rows=0,
                passed=0, transformed=0, deferred=0, reasons={}, steps={},
                examples={}, top_reasons=[], sources={})


def audit(api, frames, rows, result, persist):
    """The same three calls, catch types, and success-only counters as native audit."""
    result['status'] = 'RUNNING'
    steps = result['steps'] = {k: dict(attempted=0, passed=0, deferred=0, reasons={})
        for k in ('direct_transform', 'frames.resolve', 'routing.direct_row')}
    result['transform_changed_before_later_checks'] = 0
    last = time.monotonic()
    persist()
    with gzip.open(rows, 'rt') as stream:
        for line in stream:
            result['rows'] += 1
            # Native json decoding occurs outside the three-call exception handler.
            raw = json.loads(line)
            step = 'direct_transform'
            try:
                steps[step]['attempted'] += 1
                transformed, changed = api.direct_transform(raw)
                steps[step]['passed'] += 1
                result['transform_changed_before_later_checks'] += int(changed)
                step = 'frames.resolve'
                steps[step]['attempted'] += 1
                inputs, _ = frames.resolve(transformed)
                steps[step]['passed'] += 1
                step = 'routing.direct_row'
                steps[step]['attempted'] += 1
                api.routing.direct_row({**transformed, 'student_input': inputs})
                steps[step]['passed'] += 1
                result['transformed'] += int(changed)
                result['passed'] += 1
            except (ValueError, KeyError, TypeError) as error:
                result['deferred'] += 1
                text = type(error).__name__ + ': ' + str(error)
                result['reasons'][text] = result['reasons'].get(text, 0) + 1
                item = steps[step]
                item['deferred'] += 1
                item['reasons'][text] = item['reasons'].get(text, 0) + 1
                examples = result['examples'].setdefault(text, [])
                if len(examples) < 3:
                    examples.append(dict(qid=raw.get('qid'), reason=text, step=step))
            if result['rows'] % 200 == 0 or time.monotonic() - last >= 5:
                persist()
                last = time.monotonic()
    result['status'] = 'COMPLETE'
    result['failure_exceeds_one_percent'] = result['deferred'] > 0.01 * result['rows']
    persist()


def rankings(result):
    result['top_reasons'] = [dict(reason=k, count=v, examples=result['examples'][k])
        for k, v in sorted(result['reasons'].items(), key=lambda kv: (-kv[1], kv[0]))]


def worker(work, output, manifest, label):
    spec = manifest['trees'][label]
    path = output / ('AUDIT_TREE_' + label + '.json')
    result = empty_result(label, spec)
    def persist():
        rankings(result)
        dump(path, result)
    def stopped(signum, frame):
        result.update(status='INTERRUPTED', signal=signum)
        persist()
        raise SystemExit(128 + signum)
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1):
        signal.signal(sig, stopped)
    persist()
    try:
        state = read(work / 'k_0.json')
        result['inputs'] = state['evidence']
        if label == 'P':
            result['run_evidence'] = manifest['p_evidence']
        result['legacy_rows'] = state['fps']['rows']
        result['sources'] = manifest['sources']
        for item in result['sources'].values():
            item['audit_status'] = 'NOT_ROWS' if item['kind'] != 'rows' else 'RUNNING'
        sys.meta_path.insert(0, TreeFinder(work / ('k_' + label), spec['files']))
        if (work / 'k_n').is_dir():
            sys.path.insert(0, str(work / 'k_n'))
        from student_pilot import s1_routing as api
        if 'trace_format/contracts.py' in spec['files']:
            from trace_format.contracts import contract_epoch, new_contracts, heading_plane_min
            epoch = contract_epoch(new_contracts(), heading_plane_min=heading_plane_min())
        else:
            epoch = contextlib.nullcontext()
        import numpy, torch
        torch.set_num_threads(8)
        torch.set_num_interop_threads(1)
        result['runtime'] = dict(python=sys.version.split()[0], numpy=numpy.__version__, torch=torch.__version__)
        if (work / 'k_n').is_dir() and numpy.__version__ != '2.2.6':
            raise ValueError('E_OVERLAY_VERSION')
        pins = state['pins']
        with epoch:
            frames = api.Frames(pins['frame_map'], pins['frame_plan'], state['fps']['fps'],
                                pins['fps_authority'], state['fps']['groups'])
            result['status'] = 'FRAMES_READY'
            persist()
            audit(api, frames, pins['rows']['path'], result, persist)
        if result['rows'] != manifest['sources']['ROUTE_direct']['declared_rows']:
            raise ValueError('E_ROWS')
        result['sources']['ROUTE_direct']['audit_status'] = 'COMPLETE'
        result['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        persist()
        return 0
    except BaseException as error:
        if result['status'] != 'INTERRUPTED':
            result.update(status='ERROR', error=type(error).__name__ + ': ' + str(error))
        persist()
        return 1


def runtime(pool, work, spec):
    src = locate(pool, spec)
    if src is None:
        raise ValueError('E_RUNTIME_MIRROR_' + spec['sha256'][:16])
    checked(src, spec)
    dest = work / 'k_v'
    dest.mkdir()
    # Match the kit's extractor for its authenticated runtime, including interpreter links.
    # The hash was checked before extraction; no downloads or package installation occur.
    subprocess.run(['tar', '-xf', str(src), '-C', str(dest)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    candidates = [dest / spec['native_prefix'] / spec['native_python'],
                  dest / spec['native_python']]
    for p in candidates:
        if p.is_file():
            return p
    raise ValueError('E_RUNTIME_LAYOUT')


def stage(work, output, manifest):
    pool = Path(manifest['pool'])
    work.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    results = {label: empty_result(label, spec) for label, spec in manifest['trees'].items()}
    for value in results.values():
        value['sources'] = {name: dict(item, audit_status='NOT_ROWS' if item['kind'] != 'rows' else 'PENDING')
                            for name, item in manifest['sources'].items()}
    state = dict(pins={}, evidence={}, fps={})
    def persist():
        for label, value in results.items():
            dump(output / ('AUDIT_TREE_' + label + '.json'), value)
    def stopped(signum, frame):
        for value in results.values():
            value.update(status='INTERRUPTED', signal=signum)
        persist()
        raise SystemExit(128 + signum)
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1):
        signal.signal(sig, stopped)
    persist()
    try:
        # Fail cheaply when required mirrors are absent, before copying the large store.
        for key in ('runtime',):
            if locate(pool, manifest[key]) is None:
                raise ValueError('E_RUNTIME_MIRROR_' + manifest[key]['sha256'][:16])
        rs = manifest['pins']['rows']
        if locate(pool, rs) is None and locate(pool, rs['archive']) is None:
            raise ValueError('E_ROWS_MIRROR_' + rs['archive']['sha256'][:16])
        for key, spec in manifest['pins'].items():
            for value in results.values():
                value.update(status='STAGING', current_pin=spec['sha256'])
            persist()
            dst, evidence = stage_pin(pool, work, spec)
            state['pins'][key] = dict(path=str(dst), sha256=spec['sha256'])
            state['evidence'][key] = evidence
        def pulse(n):
            for value in results.values():
                value.update(status='CENSUS', legacy_rows_seen=n)
            persist()
        state['fps'] = census(state['pins']['legacy']['path'], manifest['legacy_count'],
                              manifest['legacy_types'], pulse)
        dump(work / 'k_0.json', state)
        dump(output / 'au_0.json', dict(inputs=state['evidence'],
             legacy_rows=state['fps']['rows'], groups=state['fps']['groups']))
        available = []
        for label, spec in manifest['trees'].items():
            src = locate(pool, spec)
            if src is None and label == 'P':
                results[label].update(status='UNAVAILABLE', error='E_P_ARCHIVE_MISSING')
                continue
            if src is None:
                raise ValueError('E_C_ARCHIVE_MISSING')
            extract_tree(src, work / ('k_' + label), spec)
            available.append(label)
        persist()
        executable = runtime(pool, work, manifest['runtime'])
        np = locate(pool, manifest['np'])
        if np is None:
            raise ValueError('E_OVERLAY_MISSING')
        checked(np, manifest['np'])
        with tarfile.open(np, 'r:*') as t:
            t.extractall(work / 'k_n', filter='data')
    except BaseException as error:
        for value in results.values():
            if value['status'] != 'INTERRUPTED':
                value.update(status='ERROR', error=type(error).__name__ + ': ' + str(error))
        persist()
        return 1
    # A fresh process per tree prevents cross-tree imports and releases frame-map memory.
    # Workers own their output files; the parent never overwrites their partial counts.
    child = None
    interruption = None
    def forward(signum, frame):
        nonlocal interruption
        interruption = signum
        if child is not None and child.poll() is None:
            child.send_signal(signum)
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1):
        signal.signal(sig, forward)
    codes = []
    for label in available:
        if interruption is not None:
            results[label].update(status='INTERRUPTED', signal=interruption)
            dump(output / ('AUDIT_TREE_' + label + '.json'), results[label])
            codes.append(1)
            continue
        try:
            child = subprocess.Popen([str(executable), '-I', '-s', '-B',
                str(Path(__file__).resolve()), 'r', str(work), str(output), label],
                env=os.environ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            rc = child.wait()
            child = None
            codes.append(rc)
            path = output / ('AUDIT_TREE_' + label + '.json')
            value = read(path)
            if rc and value['status'] not in ('ERROR', 'INTERRUPTED'):
                value.update(status='ERROR', error='E_WORKER_EXIT', exit_code=rc)
                dump(path, value)
        except Exception as error:
            results[label].update(status='ERROR', error=type(error).__name__)
            dump(output / ('AUDIT_TREE_' + label + '.json'), results[label])
            codes.append(1)
    return int(any(codes))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=['s', 'r', 'd'])
    p.add_argument('work', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('label', nargs='?', choices=['C', 'P'])
    a = p.parse_args()
    manifest = read(a.work / 'k_d.json') if a.mode == 'd' else read(Path(__file__).with_name('k.json'))
    if a.mode == 's':
        expected = Path(manifest['pool']) / 'x_22c714e1/o' / os.environ['SLURM_JOB_ID']
        if a.output != expected:
            raise ValueError('E_OUTPUT')
        return stage(a.work, a.output, manifest)
    return worker(a.work, a.output, manifest, a.label)


if __name__ == '__main__':
    raise SystemExit(main())
