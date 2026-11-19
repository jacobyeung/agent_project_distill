"""Row-range wrapper around the unchanged approved rscan module."""
from concurrent.futures import ProcessPoolExecutor
from contextlib import closing
import importlib.util
import json
import multiprocessing
import os
from pathlib import Path
import sqlite3


def layout(connection):
    tables = ['sqlite_schema'] + [r[0] for r in connection.execute(
        "SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name COLLATE BINARY")]
    return [(name, connection.execute('SELECT count(*) FROM '+quote(name)).fetchone()[0]) for name in tables]


def quote(value):
    return '"'+value.replace('"','""')+'"'


def shard(path, words, part, parts, scanner_module, limit=100000):
    m = scanner_module
    path, words = Path(path).absolute(), Path(words)
    if path.suffix == '.jsonl':
        return shard_jsonl(path, words, part, parts, m, limit)
    if type(part) is not int or type(parts) is not int or not 0 <= part < parts:
        raise ValueError('Invalid shard')
    before = m.stamp(path); m.no_journal(path)
    s = m.Scanner(json.loads(words.read_bytes()), limit)
    result = m.Summary(limit)
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)) as conn, conn:
        conn.execute('PRAGMA query_only=ON'); conn.execute('PRAGMA trusted_schema=OFF')
        if conn.execute('PRAGMA journal_mode').fetchone()[0].lower() == 'wal':
            raise ValueError('WAL is not admitted')
        conn.execute('BEGIN')
        tables = layout(conn)
        total = sum(n for _, n in tables)
        start, end = total*part//parts, total*(part+1)//parts
        if part == 0:
            result.add(s.check(str(path), '$file', 'name'))
        scan_ranges(path, words, start, end, m, limit, result, tables=tables)
        digest = m.sha(path); m.no_journal(path)
    if before != m.stamp(path):
        raise ValueError('Input changed')
    return dict(schema='rscan-shard-v1',path=str(path),sha256=digest,bytes=before[2],format='sqlite',
        complete=True, checked=result.checked,hits=result.hits,advisory=result.advisory,
        hit_list=result.locations,hits_truncated=result.hits>len(result.locations),
        scanner_sha256=m.sha(m.__file__),words_sha256=m.sha(words),wrapper_sha256=m.sha(__file__),
        shard=part,shards=parts,start=start,end=end,rows=total,tables=len(tables))


def scan_ranges(path, words, start, end, m, limit, result, tables=None, offsets=None):
    """Merge contiguous worker summaries in row order, retaining the first hits."""
    workers = min(len(os.sched_getaffinity(0)), end-start)
    if not workers:
        return
    raw_words = words.read_bytes()
    tasks = []
    for i in range(workers):
        lo, hi = start+(end-start)*i//workers, start+(end-start)*(i+1)//workers
        tasks.append((path, m.__file__, raw_words, limit, lo, hi, tables,
                      offsets[lo] if offsets is not None else None))
    with ProcessPoolExecutor(max_workers=workers,
                             mp_context=multiprocessing.get_context('spawn')) as pool:
        for checked, hits, advisory, locations in pool.map(scan_range, tasks):
            summary = m.Summary(limit)
            summary.checked, summary.hits, summary.advisory = checked, hits, advisory
            summary.locations = locations
            result.add(summary)


def scan_range(task):
    path, scanner_path, raw_words, limit, start, end, tables, byte_start = task
    spec = importlib.util.spec_from_file_location('rs', scanner_path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    s = m.Scanner(json.loads(raw_words), limit); result = m.Summary(limit)
    if tables is not None:
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)) as conn, conn:
            conn.execute('PRAGMA query_only=ON'); conn.execute('PRAGMA trusted_schema=OFF')
            if conn.execute('PRAGMA journal_mode').fetchone()[0].lower() == 'wal':
                raise ValueError('WAL is not admitted')
            conn.execute('BEGIN')
            offset = 0
            conn.text_factory = lambda raw: raw.decode('utf-8','replace')
            for ti, (table, n) in enumerate(tables):
                lo, hi = max(0, start-offset), min(n, end-offset)
                offset += n
                if hi <= lo:
                    continue
                columns = conn.execute('SELECT * FROM '+quote(table)+' LIMIT 0').description
                projection = ["CASE WHEN typeof(%s)='text' THEN %s END" % (quote(c[0]),quote(c[0])) for c in columns]
                cursor = conn.execute('SELECT '+','.join(projection)+' FROM '+quote(table)+' LIMIT ? OFFSET ?', (hi-lo, lo))
                for ri, row in enumerate(cursor, lo+1):
                    for ci, value in enumerate(row):
                        if isinstance(value,str):
                            result.add(s.check(value, f't{ti}/r{ri}/c{ci}', 'sqlite-text'))
    else:
        with path.open('rb') as stream:
            stream.seek(byte_start)
            for i in range(start, end):
                text = stream.readline().decode('utf-8','replace').removesuffix('\n')
                if m.LINES.search(text):
                    raise ValueError('Generated JSONL must use only LF record separators')
                if not text.strip():continue
                try:value=json.loads(text)
                except ValueError:result.add(s.check(text,'line:'+str(i+1),'line'))
                else:result.add(s.walk(value,'line:'+str(i+1),paths_only=True))
    return result.checked, result.hits, result.advisory, result.locations


def merge(reports, scanner_module):
    if not reports:
        raise ValueError('Empty merge')
    first=reports[0];parts=first['shards']
    if len(reports)!=parts or {r['shard'] for r in reports} != set(range(parts)):
        raise ValueError('Incomplete or duplicate shards')
    keys=('path','sha256','bytes','format','scanner_sha256','words_sha256','wrapper_sha256','shards','rows','tables')
    expected=0;hits=[];checked=advisory=0
    for r in sorted(reports,key=lambda r:r['shard']):
        if (r.get('schema')!='rscan-shard-v1' or r.get('complete') is not True or r.get('hits_truncated') is not False
            or r['hits']!=len(r['hit_list']) or any(r[k]!=first[k] for k in keys)
            or (r['start'],r['end']) != (first['rows']*r['shard']//parts,first['rows']*(r['shard']+1)//parts)
            or r['start']!=expected):
            raise ValueError('Shard identity, range or completeness differs')
        expected=r['end'];checked+=r['checked'];advisory+=r['advisory'];hits.extend(r['hit_list'])
    if expected!=first['rows'] or len({(h['kind'],h['location']) for h in hits})!=len(hits):
        raise ValueError('Coverage or hit census differs')
    return dict(schema='rscan-v1',**{k:first[k] for k in keys if k not in ('shards','wrapper_sha256') and (first['format']=='sqlite' or k not in ('rows','tables'))},
        complete=True,checked=checked,hits=len(hits),advisory=advisory,hit_list=hits,hits_truncated=False,
        status='LEAK' if hits else 'CLEAN',sharded=dict(parts=parts,wrapper_sha256=first['wrapper_sha256']))


def shard_jsonl(path, words, part, parts, m, limit=100000):
    """Canonical generated JSONL only; preserve approved line numbering and walks."""
    if type(part) is not int or type(parts) is not int or not 0 <= part < parts:
        raise ValueError('Invalid shard')
    before=m.stamp(path); offsets=[0]
    digest=__import__('hashlib').sha256()
    with path.open('rb') as stream:
        for raw in stream:
            digest.update(raw);offsets.append(offsets[-1]+len(raw))
    rows=len(offsets)-1;start,end=rows*part//parts,rows*(part+1)//parts
    scanner=m.Scanner(json.loads(words.read_bytes()),limit);result=m.Summary(limit)
    if part==0:result.add(scanner.check(str(path),'$file','name'))
    scan_ranges(path, words, start, end, m, limit, result, offsets=offsets)
    if before!=m.stamp(path):raise ValueError('Input changed')
    return dict(schema='rscan-shard-v1',path=str(path),sha256=digest.hexdigest(),bytes=before[2],format='jsonl',
        complete=True,checked=result.checked,hits=result.hits,advisory=result.advisory,
        hit_list=result.locations,hits_truncated=result.hits>len(result.locations),
        scanner_sha256=m.sha(m.__file__),words_sha256=m.sha(words),wrapper_sha256=m.sha(__file__),
        shard=part,shards=parts,start=start,end=end,rows=rows,tables=0)
