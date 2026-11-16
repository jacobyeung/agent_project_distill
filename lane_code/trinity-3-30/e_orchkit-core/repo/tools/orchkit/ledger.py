#!/usr/bin/env python3
"""The job ledger (orchkit-ledger-v1): one line under 1 KB per event, appended under a lock.

    ledger.py append --row ROW.json [--ledger PATH]
    ledger.py lookup --token TOKEN [--ledger PATH]
    ledger.py live [--partition general ...] [--ledger PATH]
    ledger.py import --from OLD_LEDGER --lane L --out NEW.jsonl

The production ledger is B/ORCHARD_LEDGER.jsonl on Trinity, never on the batch host. The path comes
from --ledger, else ORCHKIT_LEDGER, else the production default. Tests always pass a temporary path.
Python 3.6-safe, standard library only.
"""
import argparse
import json
import os
import re
import sys

if __package__ in (None, ''):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import orchkit  # noqa: F401
    __package__ = 'orchkit'  # noqa: A001
from . import util  # noqa: E402

SCHEMA = 'orchkit-ledger-v1'
PRODUCTION = ('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/'
              'ORCHARD_LEDGER.jsonl')
FIELDS = ('schema', 'utc', 'event', 'token', 'job_name', 'job_id', 'lane', 'meaning',
          'kit_pins_sha256', 'config_sha256', 'payload_sha256', 'partition', 'gpus', 'time_limit_s', 'pool', 'gcs',
          'state')
EVENTS = ('minted', 'submitted', 'ended')
TOKEN = re.compile(r'^[0-9a-f]{16}\Z')
JOB_NAME = re.compile(r'^a15_cot_ap[0-9a-f]{16}\Z')
HEX64 = re.compile(r'^[0-9a-f]{64}\Z')
PREFIX = 'a15_cot_ap'
MAX_BYTES = 1024
ENDED_STATES = ('COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT', 'OUT_OF_MEMORY', 'NODE_FAIL',
                'PREEMPTED', 'BOOT_FAIL', 'DEADLINE', 'ENDED')


class LedgerError(ValueError):
    pass


def ledger_path(explicit=None):
    return explicit or os.environ.get('ORCHKIT_LEDGER') or PRODUCTION


def make_row(event, token, **fields):
    """A complete v1 row with every field present (unknown ones null)."""
    row = dict((name, None) for name in FIELDS)
    row.update(schema=SCHEMA, utc=util.utc_iso(), event=event, token=token,
               job_name=PREFIX + token if token else None)
    for key, value in fields.items():
        if key not in FIELDS:
            raise LedgerError('unknown ledger field %r' % key)
        row[key] = value
    return row


def validate(row, strict=True):
    """Raise LedgerError unless row is a v1 row. strict also requires a minted-format token."""
    if not isinstance(row, dict) or set(row) != set(FIELDS):
        raise LedgerError('ledger row keys differ: %s' % sorted(set(row or {}) ^ set(FIELDS)))
    if row['schema'] != SCHEMA or row['event'] not in EVENTS:
        raise LedgerError('bad schema or event')
    if strict:
        if not isinstance(row['token'], str) or not TOKEN.match(row['token']):
            raise LedgerError('token must be 16 lowercase hex')
        if row['job_name'] != PREFIX + row['token'] or not JOB_NAME.match(row['job_name']):
            raise LedgerError('job_name must be %s plus the token' % PREFIX)
        for key in ('kit_pins_sha256', 'config_sha256', 'payload_sha256'):
            if row[key] is not None and not HEX64.match(str(row[key])):
                raise LedgerError('%s must be 64 hex or null' % key)
        if row['job_id'] is not None and type(row['job_id']) is not int:
            raise LedgerError('job_id must be an integer or null')
    if len(util.canonical_json(row)) + 1 > MAX_BYTES:
        raise LedgerError('ledger row is above %d bytes' % MAX_BYTES)
    return row


def append(row, path=None, strict=True):
    validate(row, strict)
    return util.append_jsonl_locked(ledger_path(path), row, max_bytes=MAX_BYTES)


def read_rows(path=None):
    """Every parseable row; a broken line is reported as {'_broken': line_number}."""
    path = ledger_path(path)
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, 'rb') as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line.decode('utf-8')))
            except (ValueError, UnicodeDecodeError):
                rows.append({'_broken': number})
    return rows


def lookup(token, path=None):
    token = token[len(PREFIX):] if token.startswith(PREFIX) else token
    return [row for row in read_rows(path) if row.get('token') == token]


def live(path=None, partitions=None):
    """Rows of jobs that were submitted and have no ended row, optionally on given partitions."""
    submitted, ended = {}, set()
    for row in read_rows(path):
        if row.get('schema') != SCHEMA:
            continue
        if row.get('event') == 'submitted':
            submitted[row['token']] = row
        elif row.get('event') == 'ended':
            ended.add(row['token'])
    out = []
    for token, row in sorted(submitted.items()):
        if token in ended:
            continue
        if partitions and row.get('partition') not in partitions:
            continue
        out.append(row)
    return out


# ---------------------------------------------------------------- import of the five old schemas

def _seconds(value):
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.match(r'^(\d+-)?\d+:\d\d:\d\d$', value):
        days = 0
        if '-' in value:
            head, value = value.split('-', 1)
            days = int(head)
        hours, minutes, seconds = (int(part) for part in value.split(':'))
        return ((days * 24 + hours) * 60 + minutes) * 60 + seconds
    return None


MAPPED = ('utc', 'token', 'tokens', 'job_name', 'job_id', 'meaning', 'partition', 'gpus', 'time',
          'allocation_seconds', 'pool', 'gcs', 'cloud', 'object', 'status', 'submitted', 'purpose')


def _fit(row):
    """Shorten meaning until the row fits in one 1 KB line."""
    while len(util.canonical_json(row)) + 1 > MAX_BYTES:
        text = row['meaning'] or ''
        cut = len(text) - (len(util.canonical_json(row)) + 1 - MAX_BYTES) - 4
        if cut <= 0:
            row['meaning'] = None
            break
        row['meaning'] = text[:cut] + '...'
    return row


def import_row(old, lane):
    """Map one row of an old ledger schema to v1 rows (a row naming several tokens gives several)."""
    tokens = old.get('tokens') if isinstance(old.get('tokens'), list) else [old.get('token')]
    extra = dict((key, value) for key, value in old.items() if key not in MAPPED)
    meaning = old.get('meaning', old.get('purpose'))
    if not isinstance(meaning, str) and meaning is not None:
        meaning = util.canonical_json(meaning).decode('utf-8')
    if extra:
        meaning = (meaning + ' ' if meaning else '') + 'extra=' + util.canonical_json(extra).decode('utf-8')
    status = old.get('status')
    job_id = old.get('job_id')
    if isinstance(job_id, str) and job_id.isdigit():
        job_id = int(job_id)
    if not isinstance(job_id, int):
        job_id = None
    if isinstance(status, str) and status.upper().split()[0].rstrip(',') in ENDED_STATES:
        event = 'ended'
    elif job_id is not None or old.get('submitted') is True:
        event = 'submitted'
    else:
        event = 'minted'
    destination = str(old.get('destination') or '')
    if '/test_' in destination or '/tmp' in destination:
        state = 'test-prepare'
    else:
        state = status if isinstance(status, str) else 'imported'
    rows = []
    for token in tokens:
        token = str(token) if token is not None else None
        name = old.get('job_name')
        if token and token.startswith(PREFIX):
            token = token[len(PREFIX):]
        if name is None and token and re.match(r'^[0-9a-z]+$', token):
            name = PREFIX + token
        gcs = old.get('gcs', old.get('cloud', old.get('object')))
        row = dict((field, None) for field in FIELDS)
        row.update(schema=SCHEMA, utc=old.get('utc'), event=event, token=token, job_name=name,
                   job_id=job_id, lane=lane, meaning=meaning, partition=old.get('partition'),
                   gpus=old.get('gpus'),
                   time_limit_s=_seconds(old.get('time', old.get('allocation_seconds'))),
                   pool=old.get('pool'), gcs=gcs, state=state)
        rows.append(_fit(row))
    return rows


def import_ledger(source, lane):
    rows, broken = [], []
    with open(str(source), 'rb') as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                old = json.loads(line.decode('utf-8'))
            except (ValueError, UnicodeDecodeError):
                broken.append(number)
                continue
            for row in import_row(old, lane):
                validate(row, strict=False)
                rows.append(row)
    return rows, broken


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = parser.add_subparsers(dest='command')
    p_append = sub.add_parser('append')
    p_append.add_argument('--row', required=True)
    p_append.add_argument('--ledger')
    p_lookup = sub.add_parser('lookup')
    p_lookup.add_argument('--token', required=True)
    p_lookup.add_argument('--ledger')
    p_live = sub.add_parser('live')
    p_live.add_argument('--partition', action='append')
    p_live.add_argument('--ledger')
    p_import = sub.add_parser('import')
    p_import.add_argument('--from', dest='source', required=True)
    p_import.add_argument('--lane', required=True)
    p_import.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'append':
            print(append(util.read_json(args.row), args.ledger))
            return 0
        if args.command == 'lookup':
            for row in lookup(args.token, args.ledger):
                print(json.dumps(row, sort_keys=True))
            return 0
        if args.command == 'live':
            for row in live(args.ledger, args.partition):
                print(json.dumps(row, sort_keys=True))
            return 0
        if args.command == 'import':
            if os.path.abspath(args.out) == os.path.abspath(PRODUCTION):
                raise LedgerError('import never writes the production ledger')
            rows, broken = import_ledger(args.source, args.lane)
            seen = set()
            if os.path.exists(args.out):
                for row in read_rows(args.out):
                    seen.add(util.canonical_json(row))
            added = 0
            for row in rows:
                key = util.canonical_json(row)
                if key in seen:
                    continue
                seen.add(key)
                util.append_jsonl_locked(args.out, row, max_bytes=MAX_BYTES)
                added += 1
            print(json.dumps({'source': args.source, 'lane': args.lane, 'rows': len(rows),
                              'added': added, 'broken_lines': broken}, sort_keys=True))
            return 0
    except (LedgerError, OSError, ValueError) as err:
        sys.stderr.write('ledger: %s\n' % err)
        return 2
    parser.print_help()
    return 2


if __name__ == '__main__':
    sys.exit(main())
