"""Read frozen teacher sources with the light census acceptance rule."""
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from . import answer_fullpool_ingest as ingest
from . import compact_counted_v1 as compact
from tools.gtmeasure.room_labels import parse_label
from tools.gtmeasure.formats import UNIT_METERS

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'collector'))
import census  # noqa: E402; local, offline collector grading only


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def pin(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


def read_json(path):
    return compact.decode_json(Path(path).read_bytes())


def read_jsonl(path):
    with Path(path).open('rb') as stream:
        for line in stream:
            if line.strip():
                yield compact.decode_json(line)


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(compact.canonical_bytes(value))


class FrameError(ValueError):
    def __init__(self, reason, path):
        self.reason = reason
        super().__init__(f'{reason}: {path}')


class Frames:
    """Hash each unchanged frame once, using a single serialized reader."""
    def __init__(self):
        self.checked = {}
        self.bytes_read = 0

    def check(self, frame):
        path = Path(frame['path'])
        if not path.is_absolute():
            raise FrameError('frame_hash_mismatch', path)
        try:
            stat = path.stat()
            identity = (stat.st_size, stat.st_mtime_ns, stat.st_ino)
            previous = self.checked.get(str(path))
            if previous and previous[0] == identity:
                digest = previous[1]
            else:
                digest = sha(path)
                if path.stat() != stat:
                    raise FrameError('frame_changed_during_read', path)
                self.checked[str(path)] = (identity, digest)
                self.bytes_read += stat.st_size
        except FileNotFoundError:
            raise FrameError('missing_frames', path) from None
        if digest != frame['sha256']:
            raise FrameError('frame_hash_mismatch', path)

    def row(self, row):
        from .compact_control import validate_rgb
        validate_rgb(row['student_input'])
        for frame in row['student_input']['frames']:
            self.check(frame)


def snapshot_terminals(run_root, limit, destination):
    """Freeze filenames once; attempts without a terminal in this list are out of scope."""
    run_root = Path(run_root).resolve()
    cutoff = datetime.now(timezone.utc)
    cutoff_ns = int(cutoff.timestamp() * 1_000_000_000)
    records = []
    with os.scandir(run_root / 'terminals') as entries:
        for entry in entries:
            if not re.fullmatch(r'[A-Za-z0-9_.-]+__b(?:16384|32768)\.json', entry.name):
                continue
            stat = entry.stat(follow_symlinks=False)
            if not entry.is_file(follow_symlinks=False) or stat.st_mtime_ns > cutoff_ns:
                continue
            records.append({'name': entry.name, 'mtime_ns': stat.st_mtime_ns,
                            'size_bytes': stat.st_size})
    records.sort(key=lambda r: r['name'])
    qids = sorted({record['name'].rsplit('__b', 1)[0] for record in records})
    chosen = set(qids[:limit] if limit else qids)
    result = {'schema': 'answer-fullpool-terminal-snapshot-v1', 'timestamp': cutoff.isoformat(),
              'run_root': str(run_root), 'terminal_list': records, 'limit_per_root': limit,
              'selected_qids': sorted(chosen), 'terminal_count': len(records),
              'later_terminals_out_of_scope': True, 'decisions': [],
              'acceptance_policy': 'light_census.py strict select_attempt; no tolerance-tier expansion',
              'archive_not_reverified': True}
    write_json(destination, result)
    return result


def root_b_decisions(snapshot, members, gold):
    """Adapt light_attempts/decide_light to a parameterized run root and frozen terminals.

    select_attempt, grade, cap, mechanical, and perceptual checks are the existing
    collector functions. Archive completeness uses exactly the two existence
    checks in light_census.py, and never reads journals or event trees eagerly.
    """
    root = Path(snapshot['run_root'])
    terminals = defaultdict(list)
    for record in snapshot['terminal_list']:
        terminals[record['name'].rsplit('__b', 1)[0]].append(record)
    for qid in snapshot['selected_qids']:
        try:
            items, terminal_pins, failures = [], [], []
            for record in terminals[qid]:
                path = root / 'terminals' / record['name']
                before = path.stat()
                if (before.st_mtime_ns, before.st_size) != (record['mtime_ns'], record['size_bytes']):
                    raise ValueError('snapshot_terminal_changed')
                payload = path.read_bytes()
                if path.stat() != before:
                    raise ValueError('snapshot_terminal_changed')
                terminal = compact.decode_json(payload)
                budget = int(record['name'].rsplit('__b', 1)[1].split('.')[0])
                adir = root / 'attempts' / qid / f'b{budget}'
                if terminal['question_id'] != qid or terminal['budget'] != budget or Path(terminal['output']) != adir:
                    raise ValueError('terminal_identity_mismatch')
                terminal_pins.append({'path': str(path), 'sha256': hashlib.sha256(payload).hexdigest()})
                trace_path = adir / 'finalized' / qid / f'trace_{qid}.json'
                if not trace_path.is_file():
                    failures.append({'budget': budget, 'reason': 'partial_or_missing_final'})
                    continue
                before_trace = trace_path.stat()
                cutoff = datetime.fromisoformat(snapshot['timestamp']).timestamp()
                if before_trace.st_mtime > cutoff:
                    raise ValueError('trace_newer_than_terminal_snapshot')
                payload = trace_path.read_bytes()
                if trace_path.stat() != before_trace:
                    raise ValueError('trace_changed_during_read')
                trace = compact.decode_json(payload)
                receipt = trace.get('run_receipt') or {}
                if receipt.get('fixture_only') or receipt.get('round') != 1313 or trace.get('question_id') != qid:
                    raise ValueError('census_native_identity')
                archive = adir / 'archive'
                items.append({'budget': budget, 'trace': trace, 'payload': payload,
                              'trace_path': str(trace_path), 'trace_sha256': hashlib.sha256(payload).hexdigest(),
                              'archive_complete': (archive / 'journal.jsonl').exists()
                              and (archive / 'artifact_refs.jsonl').exists()})
            if qid not in members or qid not in gold:
                raise ValueError('missing_pinned_membership_or_gold')
            decision = {'id': qid, **census.select_attempt(members[qid], gold[qid], items),
                        'source': 'light', 'archive_not_reverified': True,
                        'baseline': {'status': 'pending', 'records': []},
                        'terminals': terminal_pins, 'partial_attempts': failures}
            chosen = next((item for item in items if item['budget'] == decision.get('chosen_budget')), None)
            decision['archive_present'] = bool(chosen and chosen['archive_complete'])
            yield decision, chosen['payload'] if chosen else None
        except (ValueError, KeyError, TypeError, OSError) as error:
            yield {'id': qid, 'accepted': False, 'reason': 'census_refusal',
                   'detail': str(error), 'archive_not_reverified': True}, None


def check_membership(row, member):
    scene = member.get('source_scene_name', member['scene_name'].split('__', 1)[-1])
    expected = (member['id'], member['dataset'], scene, member['question_type'],
                member['question'], member.get('options') or [])
    actual = (row['qid'], row['dataset'], row['scene'], row['category'],
              row['student_input']['question'], row['student_input']['options'])
    if actual != expected:
        raise ValueError('pinned_membership_identity_mismatch')


def fresh_row(decision, payload, run_root, frames, commit, config_sha):
    trace_path = ingest.allowed_path(decision['trace_path'], run_root, decision['trace_path'])
    if not trace_path.is_relative_to(Path(run_root).resolve() / 'attempts'):
        raise ValueError('trace_outside_parameterized_run_root')
    raw, member, final = ingest.authenticate_trace(decision, payload)
    receipt = raw['run_receipt']['scene_receipt']
    media = ingest.rgb_metadata(receipt['path'], receipt['sha256'], run_root, frames.check)
    scene_receipt = read_json(receipt['path'])
    if raw['run_receipt']['student_inputs']['frames'] != scene_receipt['frames']:
        raise ValueError('raw_and_scene_rgb_selections_differ')
    # Same question, options, media and row schema as stage-1 source_payload.
    return {'qid': decision['id'], 'dataset': member['dataset'],
            'scene': member.get('source_scene_name', member['scene_name'].split('__', 1)[-1]),
            'category': member['question_type'],
            'student_input': {'question': member['question'], 'options': member.get('options') or [], **media},
            'native_answer_archive': final, 'target': final['target'],
            'sources': {'raw': {'path': decision['trace_path'], 'sha256': decision['trace_sha256']}},
            'generation_commit': commit, 'validation_commit': commit,
            'config_sha256': config_sha, 'ingestion_schema': ingest.SCHEMA}


def room_labels(path, expected_sha):
    """Use the fixed room-label parser and exact-scan identity, once per build."""
    labels, invalid = defaultdict(list), set()
    hasher = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for number, raw in enumerate(stream, 1):
            hasher.update(raw)
            row = compact.decode_json(raw)
            if row.get('question_type') != 'absolute_size_room':
                continue
            video = Path(row.get('video', ''))
            if len(video.parts) != 2 or video.suffix != '.mp4':
                continue
            key = (video.parent.name, video.stem)
            try:
                label = parse_label(row)
                labels[key].append({**label, 'source_line': number,
                                    'source_line_sha256': hashlib.sha256(raw).hexdigest()})
            except (ValueError, InvalidOperation, KeyError, TypeError, AttributeError):
                invalid.add(key)
    if hasher.hexdigest() != expected_sha:
        raise ValueError('room_label_authority_sha256')
    result = {}
    for key, records in labels.items():
        if key not in invalid and len({Decimal(r['value_si_decimal']) for r in records}) == 1:
            result[key] = records[0]
    return result


def check_room(row, answer, labels):
    label = labels.get((row['dataset'], row['scene']))
    if label is None:
        raise ValueError('room_label_missing_or_conflicting')
    unit = census.requested_unit({'question_type': row['category'], 'question': row['student_input']['question']})
    unit_name = {'m2': 'square meters', 'ft2': 'square feet'}[unit]
    match = re.fullmatch(r'\s*(' + census.NUMBER + r')\s*(.*?)\s*', answer)
    if not match or (match[2] and census.UNITS.get(match[2].lower().rstrip('.')) != unit):
        raise ValueError('room_label_answer_units')
    expected = Decimal(label['value_si_decimal']) / UNIT_METERS[unit_name]
    # Retain only exact corrected-label agreement. Do not manufacture a native answer
    # or apply the census's 5% tolerance to room labels. Unverifiable rounding drops.
    if Decimal(match[1]) != expected:
        raise ValueError('room_label_mismatch')
    return label
