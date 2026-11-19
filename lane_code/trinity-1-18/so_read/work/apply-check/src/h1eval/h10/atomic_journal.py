"""Durable per-item commits; the JSONL file is a recoverable projection.

The caller holds writer.lock throughout recovery and commit. Immutable settings,
export, source, shard count and membership remain bound by environment.json.
"""
import hashlib
import json
import os
from pathlib import Path
import uuid


def encoded(value):
    return (json.dumps(value, allow_nan=False)+'\n').encode()


def key(row):
    return (row['id'], row['arm'], row['mode'])


def file_key(row):
    return hashlib.sha256(encoded(key(row))).hexdigest()


def atomic_write(path, data):
    path = Path(path)
    temp = path.with_name('.'+path.name+'.pending.'+uuid.uuid4().hex)
    with temp.open('xb') as stream:
        stream.write(data);stream.flush();os.fsync(stream.fileno())
    os.replace(temp, path)
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


class AtomicJournal:
    def __init__(self, root):
        self.root = Path(root)
        self.directory = self.root/'committed'
        self.directory.mkdir(exist_ok=True)
        # Persist the directory entry before any per-item commit can be acknowledged.
        fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)
        self.rows = []
        self.done = {}

    def read(self):
        entries = []
        for path in self.directory.glob('*.json'):
            value = json.loads(path.read_bytes())
            row = value['row']
            if (value.get('schema') != 1 or row.get('complete') is not True
                    or type(value['sequence']) is not int
                    or path.stem != file_key(row)
                    or value['sha256'] != hashlib.sha256(encoded(row)).hexdigest()):
                raise ValueError('Corrupt committed item: '+str(path))
            entries.append(value)
        entries.sort(key=lambda r:r['sequence'])
        if [e['sequence'] for e in entries] != list(range(len(entries))):
            raise ValueError('Committed item sequences have gaps or duplicates')
        self.rows = [e['row'] for e in entries]
        self.done = {key(row):row for row in self.rows}
        if len(self.done) != len(self.rows):raise ValueError('Duplicate committed keys')
        return list(self.rows)

    def recover(self):
        rows = self.read()
        path = self.root/'items.jsonl'
        expected = b''.join(map(encoded,rows))
        if path.exists():
            old = path.read_bytes()
            if old == expected:return rows
            # Preserve all divergent bytes, including an incomplete UTF-8/JSON tail.
            preserved = self.root/('items.jsonl.recovery.'+hashlib.sha256(old).hexdigest())
            if not preserved.exists():atomic_write(preserved,old)
            # A complete line absent from the commit store is not a torn projection.
            for line in old.splitlines(keepends=True):
                if not line.endswith(b'\n'):break
                row = json.loads(line)
                if key(row) not in self.done or encoded(self.done[key(row)]) != encoded(row):
                    raise ValueError('JSONL has an item absent from its commit store')
        atomic_write(path,expected)
        return rows

    def commit(self, row):
        if row.get('complete') is not True:raise ValueError('Cannot commit incomplete read')
        k = key(row)
        if k in self.done:
            if encoded(self.done[k]) != encoded(row):raise ValueError('Conflicting duplicate commit')
            return
        value = dict(schema=1, sequence=len(self.rows), row=row,
                     sha256=hashlib.sha256(encoded(row)).hexdigest())
        atomic_write(self.directory/(file_key(row)+'.json'),encoded(value))
        self.rows.append(row);self.done[k] = row


def scene_selected(items, index, count):
    """Assign whole scenes to shards, balancing item counts without changing row order."""
    groups = {}
    for item in items:
        if not item.get('room_key'):raise ValueError('Scene sharding requires room_key')
        groups.setdefault(item['room_key'],[]).append(item)
    totals = [0]*count;owners = {}
    for scene, rows in sorted(groups.items(), key=lambda p:(-len(p[1]),p[0])):
        owner = min(range(count),key=lambda i:(totals[i],i))
        owners[scene] = owner;totals[owner] += len(rows)
    return [r for r in items if owners[r['room_key']] == index]
