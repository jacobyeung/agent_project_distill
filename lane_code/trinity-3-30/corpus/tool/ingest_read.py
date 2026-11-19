#!/usr/bin/env python3
"""Archive one evaluation return without importing its reader or model code."""
import argparse
import collections
import fcntl
import gzip
import hashlib
import io
import json
import os
import re
import sqlite3
import sys
import tarfile
import tempfile
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.join(ROOT, 't')
LIMIT = 32 * 1024 * 1024


def dumps(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(dumps(value).encode('utf-8')).hexdigest()


def fingerprint(path):
    h, size = hashlib.sha256(), 0
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
            size += len(b)
    return dict(path=os.path.abspath(path), sha256=h.hexdigest(), bytes=size)


def writable(path):
    path = os.path.realpath(path)
    if not (path.startswith('/scratch/') or path.startswith('/dev/shm/')):
        raise ValueError('Writes must stay on node-local /scratch or /dev/shm, not ' + path)
    return path


def readable(path):
    path = os.path.realpath(path)
    if path == '/home' or path.startswith('/home/') or re.match(r'^/data[^/]*(/|$)', path):
        raise ValueError('Reading /home or /data* is prohibited')
    return path


def temp_path(suffix, directory=SCRATCH):
    os.makedirs(writable(directory), exist_ok=True)
    fd, path = tempfile.mkstemp(prefix='.corpus-', suffix=suffix, dir=directory)
    os.close(fd)
    return path


class HashedReader(io.RawIOBase):
    def __init__(self, stream):
        self.stream, self.hash, self.size = stream, hashlib.sha256(), 0

    def readable(self):
        return True

    def readinto(self, b):
        data = self.stream.read(len(b))
        b[:len(data)] = data
        self.hash.update(data)
        self.size += len(data)
        return len(data)


class JSONStream:
    """Incremental JSON decoder; streams top-level items/rows arrays."""
    def __init__(self, stream):
        self.stream, self.buf, self.eof = stream, '', False
        self.decoder = json.JSONDecoder()

    def more(self):
        chunk = self.stream.read(65536)
        self.eof = not chunk
        self.buf += chunk
        if len(self.buf) > LIMIT:
            raise ValueError('One JSON value exceeds 32 MiB')

    def peek(self):
        self.buf = self.buf.lstrip()
        while not self.buf and not self.eof:
            self.more()
            self.buf = self.buf.lstrip()
        return self.buf[:1]

    def eat(self, char):
        if self.peek() != char:
            raise ValueError('Expected JSON delimiter ' + char)
        self.buf = self.buf[1:]

    def value(self):
        self.peek()
        while True:
            try:
                value, end = self.decoder.raw_decode(self.buf)
                # A number may end at the current chunk boundary.
                if end == len(self.buf) and not self.eof:
                    self.more()
                    continue
                self.buf = self.buf[end:]
                return value
            except ValueError:
                if self.eof:
                    raise
                self.more()

    def array(self):
        self.eat('[')
        if self.peek() != ']':
            while True:
                yield self.value()
                if self.peek() != ',':
                    break
                self.eat(',')
        self.eat(']')

    def document(self, callback):
        if self.peek() == '[':
            for row in self.array():
                callback('items', row)
            result = {}
        else:
            self.eat('{')
            result = {}
            if self.peek() != '}':
                while True:
                    key = self.value()
                    self.eat(':')
                    if key in ('items', 'rows') and self.peek() == '[':
                        for row in self.array():
                            callback(key, row)
                    else:
                        result[key] = self.value()
                    if self.peek() != ',':
                        break
                    self.eat(',')
            self.eat('}')
        if self.peek():
            raise ValueError('Trailing JSON content')
        return result


KIT_ROW = re.compile(r'^(.*?)/a0/results/([^/]+)/(?:0/)?items_a0\.jsonl(?:\.gz)?$')
ROUTE_ROW = re.compile(r'^metadata/reads/([^/]+)/metadata/journals/([^/]+)/([^/]+)/items\.jsonl(?:\.gz)?$')


class Store:
    def __init__(self):
        self.path = temp_path('.sqlite')
        self.db = sqlite3.connect(self.path)
        self.db.executescript('''PRAGMA journal_mode=OFF; PRAGMA cache_size=-16384;
        PRAGMA temp_store=FILE;
        CREATE TABLE records(path TEXT, seq INTEGER, data TEXT, id TEXT);
        CREATE INDEX record_path ON records(path);
        CREATE INDEX record_id ON records(id,path);
        CREATE TABLE docs(path TEXT PRIMARY KEY, data TEXT);
        CREATE TABLE tasks(id TEXT, hash TEXT, path TEXT, data TEXT);
        CREATE INDEX task_id ON tasks(id);
        CREATE TABLE normalized(read TEXT, family TEXT, id TEXT, arm TEXT, data TEXT,
                                PRIMARY KEY(read,family,id,arm));''')
        self.sources = []
        self.errors = []
        self.sequence = 0

    def doc(self, path, default=None):
        row = self.db.execute('SELECT data FROM docs WHERE path=?', (path,)).fetchone()
        return json.loads(row[0]) if row else ({} if default is None else default)

    def rows(self, path):
        for (data,) in self.db.execute('SELECT data FROM records WHERE path=? ORDER BY seq', (path,)):
            yield json.loads(data)

    def record(self, path, row):
        item_id = row.get('id', row.get('key')) if isinstance(row, dict) else None
        if item_id is not None:
            item_id = str(item_id).split(':', 1)[-1]
        self.db.execute('INSERT INTO records VALUES (?,?,?,?)', (path, self.sequence, dumps(row), item_id))
        self.sequence += 1
        if isinstance(row, dict) and 'question' in row and 'id' in row:
            self.db.execute('INSERT INTO tasks VALUES (?,?,?,?)',
                            (str(row['id']), digest(row), path, dumps(row)))

    def consume(self, path, binary):
        stream = gzip.GzipFile(fileobj=binary) if path.endswith('.gz') else binary
        text = io.TextIOWrapper(stream, encoding='utf-8')
        try:
            if path.endswith(('.jsonl', '.jsonl.gz')):
                while True:
                    line = text.readline(LIMIT + 1)
                    if not line:
                        break
                    if len(line) > LIMIT:
                        raise ValueError('JSONL record exceeds 32 MiB')
                    if line.strip():
                        try:
                            self.record(path, json.loads(line))
                        except ValueError:
                            # A torn final record is evidence of a partial return.
                            self.errors.append('Malformed JSONL in ' + path)
                            self.record(path + ':unparsed', {'text': line})
            else:
                value = JSONStream(text).document(lambda key, row: self.record(path, row))
                self.db.execute('INSERT INTO docs VALUES (?,?)', (path, dumps(value)))
        finally:
            text.detach()

    def load(self, source, inputs=False):
        source = readable(source)
        if os.path.isdir(source) and not inputs:
            if os.path.isfile(os.path.join(source, 'result.tar.gz')):
                source = os.path.join(source, 'result.tar.gz')
            elif os.path.isdir(os.path.join(source, 'x')):
                source = os.path.join(source, 'x')
        def selected(name):
            if inputs:
                return name.endswith(('.jsonl', '.jsonl.gz')) or (name.endswith('.json') and
                       ('/items/' in '/' + name or re.search(r'(^|/)a/\d+\.json$', name)))
            return bool(KIT_ROW.match(name) or ROUTE_ROW.match(name) or
                        re.search(r'(^|/)(SPEC|SUMMARY|COMPLETE|ITEMS)\.(json|jsonl)$', name) or
                        re.search(r'/report/[^/]+\.json$', name) or
                        (name.startswith('metadata/') and name.endswith('.json') and
                         '/frames/' not in name))
        def consume(name, raw):
            logical = ('inputs/' if inputs else '') + name
            hashed = HashedReader(raw)
            buffered = io.BufferedReader(hashed)
            self.consume(logical, buffered)
            while buffered.read(1024 * 1024):
                pass
            self.sources.append(dict(path=source, member=name if not os.path.isdir(source) else None,
                                     logical=logical, sha256=hashed.hash.hexdigest(), bytes=hashed.size))
        if os.path.isdir(source):
            for root, dirs, files in os.walk(source, followlinks=False):
                dirs[:] = sorted(d for d in dirs if not os.path.islink(os.path.join(root, d)))
                for name in sorted(files):
                    full = os.path.join(root, name)
                    rel = os.path.relpath(full, source).replace(os.sep, '/')
                    if selected(rel):
                        if os.path.islink(full):
                            raise ValueError('Source symlink refused: ' + full)
                        with open(full, 'rb') as raw:
                            consume(rel, raw)
                        self.sources[-1]['path'] = full
        else:
            with open(source, 'rb') as raw:
                hashed = HashedReader(raw)
                buffered = io.BufferedReader(hashed)
                with tarfile.open(fileobj=buffered, mode='r|*') as archive:
                    for member in archive:
                        name = member.name
                        while name.startswith('./'):
                            name = name[2:]
                        if name.startswith('x/'):
                            name = name[2:]
                        if name.startswith('/') or '..' in name.split('/'):
                            raise ValueError('Unsafe tar member: ' + name)
                        if member.isfile() and selected(name):
                            consume(name, archive.extractfile(member))
                while buffered.read(1024 * 1024):
                    pass
                self.sources.append(dict(path=source, sha256=hashed.hash.hexdigest(), bytes=hashed.size))
        self.db.commit()

    def paths(self):
        return [r[0] for r in self.db.execute('SELECT path FROM docs UNION SELECT DISTINCT path FROM records ORDER BY path')]


def completion_issues(obj, path):
    issues = []
    if isinstance(obj, dict):
        if obj.get('complete') is False:
            issues.append(path + ': complete=false')
        if 'completed' in obj and 'expected' in obj and obj['completed'] != obj['expected']:
            issues.append(path + ': completed != expected')
        for key, value in obj.items():
            issues.extend(completion_issues(value, path + '.' + key))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            issues.extend(completion_issues(value, path + '.' + str(i)))
    return issues


def base_item(row):
    result = {k: row.get(k) for k in ('question_type', 'question', 'options', 'room', 'scene')}
    result['truth'] = dict(scored=row.get('ground_truth', row.get('answer')),
                           released=row.get('released_answer'), released_in_options=row.get('released_answer_in_options'),
                           stratum=row.get('stratum'), scorer=row.get('scorer'), units=row.get('units', row.get('unit')))
    return result


def kit_arm(row):
    return dict(answer=row.get('extracted_answer'), response_text=row.get('response_text'),
                trace=row.get('raw_generation'), tool_calls=row.get('tool_calls'),
                finish_reason=row.get('finish_reason'), output_tokens=row.get('output_tokens'),
                prompt_tokens=row.get('prompt_tokens'), hit_cap=row.get('hit_token_cap'),
                parse_failed=row.get('parse_failed'), score=row.get('score'), scores=row.get('scores'))


def routed_arm(row):
    out = row.get('output') or {}
    budget = out.get('decode_budget') or {}
    tokens = out.get('tokens')
    text = out.get('text')
    # Journals do not store the extracted answer. Preserve only an explicit final segment.
    response = out.get('response_text')
    if response is None and text and '</think>' in text:
        response = text.rsplit('</think>', 1)[1].replace('<|im_end|>', '').strip()
    scores = out.get('scores')
    cap = out.get('hit_token_cap')
    if cap is None and (budget or 'finish' in out):
        cap = bool(budget.get('fired') or out.get('finish') in ('length', 'max_tokens', 'max_calls'))
    return dict(answer=out.get('extracted_answer', out.get('answer', response)), response_text=response,
                trace=text, tool_calls=(out.get('calls') or {}).get('records'),
                finish_reason=out.get('finish'), output_tokens=len(tokens) if isinstance(tokens, list) else tokens,
                prompt_tokens=out.get('prompt_tokens'), hit_cap=cap, parse_failed=out.get('parse_failed'),
                score=scores.get('answer') if scores else out.get('score'), scores=scores,
                identity={k: row.get(k) for k in ('arm', 'mode', 'intervention')}, output_arm=out.get('arm'))


class Adapter:
    name = None

    def __init__(self, store):
        self.store, self.issues = store, list(store.errors)
        self.paths = store.paths()
        if 'COMPLETE.json' not in self.paths:
            self.issues.append('Missing COMPLETE.json')
        if 'SUMMARY.json' not in self.paths:
            self.issues.append('Missing SUMMARY.json')
        for path in self.paths:
            if path.endswith(('SUMMARY.json', 'COMPLETE.json')):
                self.issues.extend(completion_issues(store.doc(path), path))

    def put(self, read, family, item_id, arm, value):
        try:
            self.store.db.execute('INSERT INTO normalized VALUES (?,?,?,?,?)',
                                  (read, family, str(item_id), arm, dumps(value)))
        except sqlite3.IntegrityError:
            raise ValueError('Duplicate item/arm: ' + repr((read, family, item_id, arm)))

    def check_row(self, row, path):
        if row.get('complete') is False or ('status' in row and str(row['status']).lower() != 'complete'):
            self.issues.append('Incomplete row in ' + path + ': ' + str(row.get('id')))


class KitAdapter(Adapter):
    name = 'kit'

    @staticmethod
    def detects(paths):
        return 'SPEC.json' in paths or any(KIT_ROW.match(p) for p in paths)

    def metadata(self, read):
        spec = self.store.doc('SPEC.json')
        binding, artifact = spec.get('export_binding', {}), spec.get('artifact', {})
        launch = self.store.doc('metadata/ORCHARD_LAUNCHER.json')
        card = launch.get('initial_card', {})
        builds = sorted(set(self.store.doc(f + '/COMPLETE.json').get('source_sha256')
                            for f in spec.get('families', [])
                            if self.store.doc(f + '/COMPLETE.json').get('source_sha256')))
        return dict(export=dict(run=binding.get('run'), step=binding.get('step', spec.get('step')),
                    generation=binding.get('generation'), artifact_id=artifact.get('artifact_id'),
                    artifact_sha256=artifact.get('sha256')), job_id=card.get('job'), date=card.get('utc'),
                    reader_build=builds[0] if len(builds) == 1 else None,
                    serving=dict(models=spec.get('models'), scope=spec.get('scope'))), \
                    dict(export='SPEC.json', job_id='metadata/ORCHARD_LAUNCHER.json', serving='SPEC.json',
                    date='metadata/ORCHARD_LAUNCHER.json', reader_build='<family>/COMPLETE.json:source_sha256')

    def prepare(self):
        counts = collections.Counter()
        type_counts = collections.Counter()
        families = set(self.store.doc('SPEC.json').get('families', []))
        for path in self.paths:
            match = KIT_ROW.match(path)
            if not match:
                continue
            family, directory = match.groups()
            families.add(family)
            arm = {'0': 'full', 'budget_2048': 'B2048', 'budget_4096': 'B4096'}.get(directory, directory)
            for row in self.store.rows(path):
                self.check_row(row, path)
                value = base_item(row)
                value.update(arm=kit_arm(row), raw=row, source_file=path, original_arm=directory)
                report_path = family + '/report/' + ('ON16k' if arm == 'full' else arm) + '.json'
                report_row = self.store.db.execute('SELECT data FROM records WHERE path=? AND id=?',
                                                   (report_path, str(row.get('id')))).fetchone()
                if report_row and value['arm']['scores'] is None:
                    value['arm']['scores'] = json.loads(report_row[0]).get('scores')
                self.put('', family, row.get('id', row.get('example_id', row.get('key'))), arm, value)
                counts[(family, arm)] += 1
                type_counts[(family, arm, row.get('question_type'))] += 1
        summary = self.store.doc('SUMMARY.json')
        for family in sorted(families):
            marker = family + '/COMPLETE.json'
            if marker not in self.paths:
                self.issues.append('Missing ' + marker)
            expected = summary.get('families', {}).get(family, {}).get('items')
            if expected is None:
                expected = self.store.doc(marker).get('items')
            # These kit returns declare full generation plus both scored budgets.
            for arm in ('full', 'B2048', 'B4096'):
                if expected is not None and counts[(family, arm)] < expected:
                    self.issues.append('%s/%s: %s < expected %s' % (family, arm, counts[(family, arm)], expected))
                population = self.store.doc(marker).get('population', {})
                if not population:
                    population = self.store.doc('SPEC.json').get('population', {}).get(family, {})
                for typ, total in population.get('types', {}).items():
                    if type_counts[(family, arm, typ)] < total:
                        self.issues.append('%s/%s/%s: rows below expected %s' % (family, arm, typ, total))
        count = self.store.db.execute('SELECT count(*) FROM (SELECT DISTINCT family,id FROM normalized)').fetchone()[0]
        if count < summary.get('items', 0):
            self.issues.append('Total item count below SUMMARY.items')
        return ['']


class RoutedAdapter(Adapter):
    name = 'routed'

    @staticmethod
    def detects(paths):
        return any(ROUTE_ROW.match(p) or re.match(r'^metadata/reads/[^/]+/SUMMARY.json$', p) for p in paths)

    def metadata(self, read):
        pin = self.store.doc('metadata/EXPORT_PIN.json')
        identity = self.store.doc('metadata/reads/' + read + '/metadata/IDENTITY.json')
        settings = self.store.doc('metadata/reads/' + read + '/metadata/0.json')
        serving = dict(identity=identity, settings=settings, cards=self.store.doc('metadata/CARDS.json'))
        item_set = self.store.doc('metadata/reads/' + read + '/metadata/a/3.json').get('name')
        return dict(set=item_set, export=dict(run=pin.get('run'), step=pin.get('step'), generation=pin.get('member_directory'),
                    artifact_id=pin.get('artifact_id'), artifact_sha256=pin.get('artifact', {}).get('sha256')),
                    serving=serving, reader_build=self.store.doc('metadata/IDENTITY.json').get('operator_sha256'),
                    job_id=self.store.doc('metadata/RETURN_ID.json').get('job')), \
                    dict(set='metadata/reads/' + read + '/metadata/a/3.json:name',
                         export='metadata/EXPORT_PIN.json', serving='metadata/reads/' + read + '/metadata',
                         reader_build='metadata/IDENTITY.json:operator_sha256', job_id='metadata/RETURN_ID.json')

    def task(self, row, path):
        item_id = str(row['id'])
        mapping_path = path.rsplit('/', 1)[0] + '/item_mapping.json'
        record = self.store.db.execute('SELECT data FROM records WHERE path=? AND id=?',
                                       (mapping_path, item_id)).fetchone()
        mapping = json.loads(record[0]) if record else None
        candidates = self.store.db.execute('SELECT hash,path,data FROM tasks WHERE id=? ORDER BY path', (item_id,))
        exact, fallback = [], []
        for h, source, data in candidates:
            task = json.loads(data)
            if mapping and h == mapping.get('task_sha256'):
                exact.append((task, source))
            else:
                fallback.append((task, source))
        pool = exact or fallback
        if not pool:
            raise ValueError('Missing question/truth for ' + item_id + '; supply --inputs')
        first = base_item(pool[0][0])
        if not exact and any(base_item(x[0]) != first for x in pool[1:]):
            raise ValueError('Ambiguous task ID without matching task_sha256: ' + item_id)
        return pool[0][0], pool[0][1], mapping, bool(exact)

    def prepare(self):
        reads, counts = set(), collections.Counter()
        for path in self.paths:
            match = ROUTE_ROW.match(path)
            if not match:
                continue
            read, typ, shard = match.groups()
            reads.add(read)
            for row in self.store.rows(path):
                self.check_row(row, path)
                task, task_path, mapping, verified = self.task(row, path)
                value = base_item(task)
                out = row.get('output') or {}
                value['question_type'] = out.get('question_type', row.get('question_type', row.get('type', value['question_type'])))
                value['truth']['stratum'] = out.get('stratum', value['truth']['stratum'])
                arm = str(row.get('arm') or out.get('arm') or row.get('mode') or 'unknown')
                # Non-default interventions are distinct scored arms.
                mode = row.get('mode')
                intervention = row.get('intervention') or {}
                name = intervention.get('name') if isinstance(intervention, dict) else intervention
                if mode not in (None, 'none') or name not in (None, 'none'):
                    arm += ':' + dumps(dict(mode=mode, intervention=intervention))
                value.update(arm=routed_arm(row), raw=row, input=task, mapping=mapping,
                             task_hash_verified=verified, source_file=path, input_file=task_path)
                self.put(read, task.get('family') or '', row['id'], arm, value)
                counts[(read, typ, shard)] += 1
            journal_summary = self.store.doc(path.rsplit('/', 1)[0] + '/SUMMARY.json')
            if counts[(read, typ, shard)] < journal_summary.get('expected', 0):
                self.issues.append(path + ': rows below expected')
        declared = self.store.doc('SUMMARY.json').get('reads', [])
        reads.update(str(r['read']) for r in declared)
        for read in sorted(reads):
            path = 'metadata/reads/' + read + '/SUMMARY.json'
            summary = self.store.doc(path)
            if path not in self.paths:
                self.issues.append('Missing ' + path)
            expected = summary.get('expected', next((r.get('expected', 0) for r in declared if str(r['read']) == read), 0))
            if sum(n for (r, t, s), n in counts.items() if r == read) < expected:
                self.issues.append('Read ' + read + ': rows below expected')
            for shard in summary.get('shards', []):
                key = (read, str(shard['type']), str(shard['shard']).split('/')[0])
                if counts[key] < shard.get('expected', 0):
                    self.issues.append('Missing/short shard ' + repr(key))
        return sorted(reads)


ADAPTERS = [KitAdapter, RoutedAdapter]


def metadata(args, adapter, read, read_id, supplied):
    auto, origin = adapter.metadata(read)
    result, provenance = {}, {}
    fields = ('read_id', 'set', 'vehicle', 'official', 'export', 'arms', 'serving', 'reader_build',
              'job_id', 'date', 'purpose', 'reported_by', 'notes')
    for key in fields:
        value = auto.get(key)
        source = origin.get(key, 'return') if value is not None else 'absent'
        if key in supplied:
            if isinstance(value, dict) and isinstance(supplied[key], dict):
                value = dict(value, **supplied[key])
                source = 'meta+return'
            else:
                value = supplied[key]
                source = 'meta'
        cli = getattr(args, key, None)
        if cli is not None:
            value, source = cli, 'cli'
        result[key], provenance[key] = value, source
    result['read_id'] = read_id
    provenance['read_id'] = 'cli' if args.read_id else 'meta'
    export = {k: None for k in ('run', 'step', 'artifact_id', 'artifact_sha256', 'generation')}
    export.update(result['export'] or {})
    result['export'] = export
    return result, provenance


def write_json(path, value):
    path = writable(path)
    temporary = temp_path('.json', os.path.dirname(path))
    with open(temporary, 'w', encoding='utf-8') as f:
        f.write(dumps(value) + '\n')
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, path)


def publish(temp, target):
    target = writable(target)
    info = fingerprint(temp)
    with open(target + '.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if os.path.exists(target):
            if fingerprint(target)['sha256'] != info['sha256']:
                raise FileExistsError('Different bytes already exist: ' + target)
            return 'SAME', info
        os.rename(temp, target)
    return 'WROTE', info


def emit(args, store, adapter, read, read_id, supplied):
    meta, provenance = metadata(args, adapter, read, read_id, supplied)
    root = writable(args.out)
    for sub in ('reads', 'index'):
        os.makedirs(writable(os.path.join(root, sub)), exist_ok=True)
    target = os.path.join(root, 'reads', read_id + '.jsonl.gz')
    temporary = temp_path('.jsonl.gz', os.path.join(root, 'reads'))
    count, families, types, stats = 0, collections.Counter(), collections.Counter(), {}
    partial = bool(adapter.issues)
    cursor = store.db.execute('SELECT family,id,arm,data FROM normalized WHERE read=? ORDER BY family,id,arm', (read,))
    def lines():
        current, row = None, None
        for family, item_id, arm, data in cursor:
            value = json.loads(data)
            if current != (family, item_id):
                if row is not None:
                    yield row
                current = family, item_id
                row = {k: meta[k] for k in ('read_id', 'official', 'export', 'vehicle', 'set', 'serving', 'job_id', 'date')}
                row.update({k: value[k] for k in ('question_type', 'question', 'options', 'room', 'scene', 'truth')})
                row.update(schema='corpus-v1', partial=partial, family=family or None, item_id=item_id,
                           arms={}, raw={'input': value.get('input')}, reader=dict(format=adapter.name,
                           build=meta['reader_build'], source_files=[]))
                row['raw']['source'] = {}
                row['raw']['records'] = {}
                for source, record in store.db.execute('SELECT path,data FROM records WHERE id=? ORDER BY path,seq', (item_id,)):
                    if (source == 'ITEMS.jsonl' or source.startswith(family + '/')) and not KIT_ROW.match(source):
                        row['raw']['records'].setdefault(source, []).append(json.loads(record))
                if value.get('mapping') is not None:
                    row['raw']['mapping'] = value['mapping']
                    row['reader']['task_hash_verified'] = value['task_hash_verified']
            row['arms'][arm] = value['arm']
            row['raw'][arm] = value['raw']
            row['raw']['source'][arm] = dict(file=value['source_file'], original_arm=value.get('original_arm'))
            row['reader']['source_files'].append(value['source_file'])
            if value.get('input_file'):
                row['reader']['source_files'].append(value['input_file'])
        if row is not None:
            yield row
    with open(temporary, 'wb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, compresslevel=6, mtime=0) as gz:
            for row in lines():
                row['reader']['source_files'] = sorted(set(row['reader']['source_files']))
                gz.write((dumps(row) + '\n').encode('utf-8'))
                count += 1
                families[row['family']] += 1
                types[row['question_type']] += 1
                for arm, value in row['arms'].items():
                    s = stats.setdefault(arm, dict(items=0, scored=0, sum=0.0))
                    s['items'] += 1
                    if isinstance(value['score'], (int, float)):
                        s['scored'] += 1
                        s['sum'] += value['score']
        raw.flush()
        os.fsync(raw.fileno())
    state, info = publish(temporary, target)
    for s in stats.values():
        s['mean_score'] = s.pop('sum') / s['scored'] if s['scored'] else None
    index = dict(meta, schema='corpus-index-v1', provenance=provenance, status='partial' if partial else 'complete',
                 partial=partial, partial_reasons=sorted(set(adapter.issues)), item_count=count,
                 arm_stats=stats, families={k or 'null': v for k, v in families.items()},
                 question_types={k or 'null': v for k, v in types.items()},
                 sources=sorted(store.sources, key=dumps), output=dict(path='reads/' + read_id + '.jsonl.gz',
                 sha256=info['sha256'], bytes=info['bytes']), tool_version=fingerprint(__file__)['sha256'],
                 raw_metadata={p: store.doc(p) for p in store.paths() if p.endswith('.json')})
    index['unparsed_records'] = {p: list(store.rows(p)) for p in store.paths() if p.endswith(':unparsed')}
    index_path = os.path.join(root, 'index', read_id + '.json')
    if state != 'SAME' or not os.path.exists(index_path):
        write_json(index_path, index)
    return dict(result=state, read_id=read_id, item_count=count, bytes=info['bytes'], sha256=info['sha256'])


def validate_id(value):
    if not value or not re.match(r'^[A-Za-z0-9][A-Za-z0-9_.-]*$', value):
        raise ValueError('read_id must contain only letters, numbers, _, . and -')
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command')
    ing = sub.add_parser('ingest')
    ing.add_argument('--source', required=True)
    ing.add_argument('--format', choices=['auto'] + [a.name for a in ADAPTERS], default='auto')
    ing.add_argument('--inputs')
    ing.add_argument('--archive-partial', action='store_true')
    ing.add_argument('--read-index')
    for flag in ('set', 'vehicle', 'purpose', 'reported-by', 'job-id'):
        ing.add_argument('--' + flag)
    ing.add_argument('--official', action='store_true', default=None)
    lost = sub.add_parser('lost')
    idx = sub.add_parser('index')
    for p in (ing, lost):
        p.add_argument('--read-id')
        p.add_argument('--meta', required=p is lost)
    for p in (ing, lost, idx):
        p.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    if args.command is None:
        parser.error('Choose ingest, lost, or index')
    start = time.monotonic()
    try:
        root = writable(args.out)
        if args.command == 'index':
            directory = os.path.join(root, 'index')
            temp = temp_path('.jsonl', root)
            count = 0
            with open(temp, 'w', encoding='utf-8') as f:
                for name in sorted(os.listdir(directory)):
                    if name.endswith('.json') and not name.startswith('.'):
                        with open(os.path.join(directory, name), encoding='utf-8') as source:
                            record = json.load(source)
                        if record['read_id'] != name[:-5]:
                            raise ValueError('Index filename/read_id mismatch: ' + name)
                        f.write(dumps(record) + '\n')
                        count += 1
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp, os.path.join(root, 'INDEX.jsonl'))
            print(dumps(dict(index_entries=count)))
            return 0
        supplied = {}
        if args.meta:
            with open(readable(args.meta), encoding='utf-8') as f:
                supplied = json.load(f)
        read_id = validate_id(args.read_id or supplied.get('read_id'))
        if args.command == 'lost':
            entry = dict(supplied, read_id=read_id)
            entry.setdefault('status', 'lost')
            if entry['status'] not in ('lost', 'orchard_only'):
                raise ValueError('lost status must be lost or orchard_only')
            entry.update(schema='corpus-index-v1', output=None, sources=[fingerprint(args.meta)],
                         tool_version=fingerprint(__file__)['sha256'],
                         provenance={k: 'meta' for k in supplied})
            entry['provenance']['read_id'] = 'cli' if args.read_id else 'meta'
            path = writable(os.path.join(root, 'index', read_id + '.json'))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if os.path.exists(path):
                with open(path, encoding='utf-8') as f:
                    if json.load(f) != entry:
                        raise FileExistsError('Index entry already exists: ' + path)
            else:
                write_json(path, entry)
            print(dumps(dict(result='INDEX', read_id=read_id, status=entry['status'])))
            return 0
        store = Store()
        try:
            store.load(args.source)
            if args.inputs:
                store.load(args.inputs, inputs=True)
            if args.meta:
                store.sources.append(fingerprint(args.meta))
            candidates = [a for a in ADAPTERS if a.name == args.format or
                          (args.format == 'auto' and a.detects(store.paths()))]
            if len(candidates) != 1:
                raise ValueError('Cannot identify one format; use --format')
            adapter = candidates[0](store)
            reads = adapter.prepare()
            store.db.commit()
            if args.read_index is not None:
                if args.read_index not in reads:
                    raise ValueError('Unknown read index ' + args.read_index)
                reads = [args.read_index]
            if adapter.issues and not args.archive_partial:
                print(dumps(dict(error='partial return', reasons=sorted(set(adapter.issues)))), file=sys.stderr)
                return 2
            for read in reads:
                ident = read_id + '.r' + read if len(reads) > 1 else read_id
                result = emit(args, store, adapter, read, ident, supplied)
                result['seconds'] = round(time.monotonic() - start, 3)
                print(dumps(result))
            return 0
        finally:
            store.db.close()
    except FileExistsError as exc:
        print(str(exc), file=sys.stderr)
        return 3
    except (ValueError, OSError, tarfile.TarError, sqlite3.Error) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
