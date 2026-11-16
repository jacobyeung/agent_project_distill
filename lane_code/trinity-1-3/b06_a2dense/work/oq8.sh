cd /project/community/jjyeung/okh7/b6d1 && nice -n 19 /project/community/jjyeung/cp4tk_fr/venv/bin/python -I - <<'PYEOF' | tail -1 | cut -c1-300
import types
sqlro = types.ModuleType('sqlro')
exec('"""Read-only SQLite table scanner over a byte range that may be split across files or sit inside a tar.\n\nStdlib only. Used where the store cannot be opened by sqlite3 without first copying it\n(raw byte splits `x.p00, x.p01, ...`, or an uncompressed tar member). It walks the table\nb-tree of one table in rowid order and yields decoded records. Interior/leaf table pages and\noverflow chains are supported; index b-trees are never read. WAL files are not consulted, so\nthe store must be a checkpointed, immutable file (the case for every sealed row store).\n\nusage (CLI): sqlro.py TABLE OFFSET PART [PART ...]   -> prints rowcount and first record keys\n"""\nimport os\nimport struct\nimport sys\n\n\nclass SplitFile:\n    """Random access over concatenated parts, starting at a byte offset (e.g. a tar member)."""\n\n    def __init__(self, parts, offset=0, length=None):\n        self.parts = [(p, os.path.getsize(p)) for p in parts]\n        self.offset = offset\n        self.total = sum(n for _, n in self.parts)\n        self.length = self.total - offset if length is None else length\n        self.handles = {}\n\n    def pread(self, off, n):\n        if off < 0 or off + n > self.length:\n            raise ValueError(\'read outside the store\')\n        off += self.offset\n        out = []\n        base = 0\n        for path, size in self.parts:\n            if n == 0:\n                break\n            if off < base + size:\n                local = off - base\n                take = min(n, size - local)\n                fh = self.handles.get(path)\n                if fh is None:\n                    fh = self.handles[path] = open(path, \'rb\')\n                out.append(os.pread(fh.fileno(), take, local))\n                if len(out[-1]) != take:\n                    raise IOError(\'short read\')\n                off += take\n                n -= take\n            base += size\n        if n:\n            raise IOError(\'read past the parts\')\n        return b\'\'.join(out)\n\n    def close(self):\n        for fh in self.handles.values():\n            fh.close()\n\n\ndef varint(buf, i):\n    v = 0\n    for k in range(8):\n        b = buf[i + k]\n        v = (v << 7) | (b & 0x7F)\n        if b < 0x80:\n            return v, i + k + 1\n    return (v << 8) | buf[i + 8], i + 9\n\n\nclass Store:\n    def __init__(self, src):\n        self.src = src\n        h = src.pread(0, 100)\n        if h[:16] != b\'SQLite format 3\\x00\':\n            raise ValueError(\'not an SQLite file\')\n        ps = struct.unpack(\'>H\', h[16:18])[0]\n        self.page_size = 65536 if ps == 1 else ps\n        self.reserved = h[20]\n        if struct.unpack(\'>I\', h[56:60])[0] not in (0, 1):\n            raise ValueError(\'only UTF-8 stores are supported\')\n        if h[18] == 2 or h[19] == 2:\n            raise ValueError(\'WAL-mode store: checkpoint first\')\n        self.usable = self.page_size - self.reserved\n\n    def page(self, n):\n        return self.src.pread((n - 1) * self.page_size, self.page_size)\n\n    def payload(self, page, i):\n        P, i = varint(page, i)\n        return P, i\n\n    def _cell_record(self, page, ptr):\n        P, i = varint(page, ptr)\n        rowid, i = varint(page, i)\n        U = self.usable\n        X = U - 35\n        if P <= X:\n            return rowid, page[i:i + P]\n        M = ((U - 12) * 32 // 255) - 23\n        K = M + ((P - M) % (U - 4))\n        local = K if K <= X else M\n        data = [page[i:i + local]]\n        nxt = struct.unpack(\'>I\', page[i + local:i + local + 4])[0]\n        need = P - local\n        while need > 0:\n            if nxt == 0:\n                raise ValueError(\'overflow chain ends early\')\n            ov = self.page(nxt)\n            nxt = struct.unpack(\'>I\', ov[:4])[0]\n            take = min(need, U - 4)\n            data.append(ov[4:4 + take])\n            need -= take\n        return rowid, b\'\'.join(data)\n\n    def scan(self, root):\n        """Yield (rowid, raw record) of a table b-tree in rowid order."""\n        stack = [root]\n        while stack:\n            n = stack.pop()\n            page = self.page(n)\n            hdr = 100 if n == 1 else 0\n            kind = page[hdr]\n            ncell = struct.unpack(\'>H\', page[hdr + 3:hdr + 5])[0]\n            if kind == 0x0D:\n                ptrs = struct.unpack(\'>%dH\' % ncell, page[hdr + 8:hdr + 8 + 2 * ncell])\n                for ptr in ptrs:\n                    yield self._cell_record(page, ptr)\n            elif kind == 0x05:\n                right = struct.unpack(\'>I\', page[hdr + 8:hdr + 12])[0]\n                ptrs = struct.unpack(\'>%dH\' % ncell, page[hdr + 12:hdr + 12 + 2 * ncell])\n                children = [struct.unpack(\'>I\', page[p:p + 4])[0] for p in ptrs] + [right]\n                stack.extend(reversed(children))\n            else:\n                raise ValueError(\'unexpected page type %d at page %d\' % (kind, n))\n\n    @staticmethod\n    def decode(rec):\n        hsize, i = varint(rec, 0)\n        types = []\n        while i < hsize:\n            t, i = varint(rec, i)\n            types.append(t)\n        pos = hsize\n        out = []\n        for t in types:\n            if t == 0:\n                out.append(None)\n            elif 1 <= t <= 6:\n                n = (1, 2, 3, 4, 6, 8)[t - 1]\n                out.append(int.from_bytes(rec[pos:pos + n], \'big\', signed=True))\n                pos += n\n            elif t == 7:\n                out.append(struct.unpack(\'>d\', rec[pos:pos + 8])[0])\n                pos += 8\n            elif t in (8, 9):\n                out.append(t - 8)\n            elif t >= 12:\n                n = (t - 12) // 2 if t % 2 == 0 else (t - 13) // 2\n                v = rec[pos:pos + n]\n                out.append(v if t % 2 == 0 else v.decode(\'utf-8\'))\n                pos += n\n            else:\n                raise ValueError(\'reserved serial type\')\n        return out\n\n    def tables(self):\n        out = {}\n        for rowid, rec in self.scan(1):\n            typ, name, tbl, root, sql = self.decode(rec)\n            if typ == \'table\':\n                out[name] = (root, sql)\n        return out\n\n    def rows(self, table):\n        root, sql = self.tables()[table]\n        for rowid, rec in self.scan(root):\n            vals = self.decode(rec)\n            yield rowid, vals\n\n\ndef tar_member(tar_path, name):\n    """(offset, size) of an uncompressed tar member, read from headers only."""\n    import tarfile\n    with tarfile.open(tar_path, \'r:\') as t:\n        for m in t:\n            if m.name == name:\n                return m.offset_data, m.size\n    raise KeyError(name)\n\n', sqlro.__dict__)
"""Metadata-only extraction of row clips from pinned row stores (no RGB read).

usage: python -I extract_meta.py SPEC.json OUT_DIR
SPEC: {"sources": [{"name": str, "stream": "vqa|routing|pointing|pose",
                    "kind": "sqlite" | "sqlite_parts" | "sqlite_tar" | "jsonl_gz_tar" | "jsonl",
                    "paths": [...], "member": str (tar kinds), "pose_prefix": str|null (pose only),
                    "limit": int|null}]}
Writes OUT_DIR/clips.jsonl.gz (one line per distinct clip signature), OUT_DIR/rows.jsonl.gz (one line per
row: source, stream, qid, dataset, scene, category, sig, selected), OUT_DIR/summary.json.
A clip signature is sha256 over (dataset, scene, fps, total, frame_indices, frame sha256s); paths are not
part of it (content identity never includes a path), but the distinct path roots seen are recorded.
Requires sqlro.py beside this file. Stdlib only (numpy not needed: the pose filter is reimplemented).
"""
import gzip
import hashlib
import json
import math
import os
import sys
import tarfile
import time



def dense_pose_row(row, target):
    """Same predicate as student_pilot.carrier_c1_sweep.dense_pose_row, without numpy."""
    sample = row.get('pose_sample', {})
    mask = target.get('camera_mask', [])
    camera = target.get('camera', [])
    return (row.get('category') == 'camera_pose_only'
            and sample.get('recording', {}).get('sampling', {}).get('variant') == 'all_frames32'
            and len(row.get('student_input', {}).get('frames', [])) == 32
            and isinstance(mask, list) and len(mask) == 32 and all(bool(m) for m in mask)
            and isinstance(camera, list) and len(camera) == 32
            and all(isinstance(c, list) and len(c) == 9 and all(isinstance(v, (int, float)) and math.isfinite(v) for v in c)
                    for c in camera))


DATASET_OF = {'scannet': 'd1', 'scannetpp': 'd2', 'arkitscenes': 'd3'}


def cat(row):
    value = row.get('question_type') or row.get('type') or row.get('category')
    return None if value is None else hashlib.sha1(str(value).encode()).hexdigest()[:10]


def root_of(path):
    parts = path.split('/')
    return '/'.join(parts[:3]) if len(parts) > 3 else path


def signature(row):
    si = row.get('student_input') or {}
    frames = si.get('frames') or []
    key = [row.get('dataset'), row.get('scene'), si.get('fps'), si.get('total_num_frames'),
           si.get('frame_indices'), [f.get('sha256') for f in frames]]
    return hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest(), key


def records(src):
    kind, paths = src['kind'], src['paths']
    if kind in ('sqlite', 'sqlite_parts'):
        store = sqlro.Store(sqlro.SplitFile(paths))
    elif kind == 'sqlite_tar':
        off, size = sqlro.tar_member(paths[0], src['member'])
        store = sqlro.Store(sqlro.SplitFile(paths, off, size))
    elif kind == 'jsonl_gz_tar':
        with tarfile.open(paths[0], 'r:') as t:
            for m in t:
                if m.isfile() and m.name.endswith('.jsonl.gz') and (not src.get('member') or m.name == src['member']):
                    with gzip.open(t.extractfile(m), 'rt') as fh:
                        for line in fh:
                            yield json.loads(line), {}, m.name
        return
    elif kind == 'jsonl':
        for p in paths:
            with (gzip.open(p, 'rt') if p.endswith('.gz') else open(p)) as fh:
                for line in fh:
                    yield json.loads(line), {}, os.path.basename(p)
        return
    else:
        raise ValueError('unknown kind ' + kind)
    cols = None
    for rowid, vals in store.rows(src.get('table', 'rows')):
        row = json.loads(vals[1])
        target = json.loads(vals[2]) if len(vals) > 2 and isinstance(vals[2], str) and src['stream'] == 'pose' else {}
        yield row, target, None


def main():
    spec, out = json.load(open(sys.argv[1])), sys.argv[2]
    os.makedirs(out, exist_ok=True)
    clips, summary = {}, {'sources': {}, 'started': time.time()}
    with gzip.open(os.path.join(out, 'rows.jsonl.gz'), 'wt') as rows_out:
        for src in spec['sources']:
            t0, n, sel, nosi = time.time(), 0, 0, 0
            for row, target, member in records(src):
                if src.get('limit') and n >= src['limit']:
                    break
                n += 1
                si = row.get('student_input')
                selected = True
                if src['stream'] == 'pose':
                    selected = dense_pose_row(row, target)
                    pre = src.get('pose_prefix')
                    if selected and pre is not None:
                        selected = all(f['path'].startswith(pre) for f in si['frames'])
                fi = row.get('frame_indices') if isinstance(row.get('frame_indices'), list) else (si or {}).get('frame_indices')
                if (not isinstance(si, dict) or not si.get('frames')) and isinstance(fi, list):
                    ds = row.get('dataset') or DATASET_OF.get(str(row.get('canonical', '')).split('/')[0])
                    key = [ds, row.get('scene'), None, None, fi, None]
                    sig = hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()
                    c = clips.get(sig)
                    if c is None:
                        c = clips[sig] = dict(sig=sig, dataset=ds, scene=key[1], fps=None, total=None,
                                              frame_indices=key[4], sha256=None, roots={}, rows=0, streams={},
                                              map_joined=True)
                    c['rows'] += 1
                    c['streams'][src['stream']] = c['streams'].get(src['stream'], 0) + 1
                    sel += selected
                    rows_out.write(json.dumps(dict(source=src['name'], stream=src['stream'], qid=row.get('qid'),
                                                   dataset=ds, scene=row.get('scene'), category=cat(row),
                                                   member=member, sig=sig, selected=selected, map_joined=True)) + '\n')
                    continue
                if not isinstance(si, dict) or not si.get('frames'):
                    nosi += 1
                    rows_out.write(json.dumps(dict(source=src['name'], stream=src['stream'], qid=row.get('qid'),
                                                   dataset=row.get('dataset'), scene=row.get('scene'),
                                                   category=cat(row),
                                                   member=member, sig=None, selected=selected)) + '\n')
                    continue
                sig, key = signature(row)
                c = clips.get(sig)
                if c is None:
                    c = clips[sig] = dict(sig=sig, dataset=key[0], scene=key[1], fps=key[2], total=key[3],
                                          frame_indices=key[4], sha256=key[5], roots={}, rows=0, streams={})
                c['rows'] += 1
                c['streams'][src['stream']] = c['streams'].get(src['stream'], 0) + 1
                for f in si['frames']:
                    r = root_of(f['path'])
                    c['roots'][r] = c['roots'].get(r, 0) + 1
                if src['stream'] == 'pose':
                    c.setdefault('paths', [f['path'] for f in si['frames']])
                sel += selected
                rows_out.write(json.dumps(dict(source=src['name'], stream=src['stream'], qid=row.get('qid'),
                                               dataset=row.get('dataset'), scene=row.get('scene'),
                                               category=cat(row),
                                               member=member, sig=sig, selected=selected)) + '\n')
            summary['sources'][src['name']] = dict(rows=n, selected=sel, without_student_input=nosi,
                                                   seconds=round(time.time() - t0, 1))
            print(json.dumps({src['name']: summary['sources'][src['name']]}), flush=True)
    with gzip.open(os.path.join(out, 'clips.jsonl.gz'), 'wt') as fh:
        for c in clips.values():
            fh.write(json.dumps(c, sort_keys=True) + '\n')
    summary['clips'] = len(clips)
    summary['finished'] = time.time()
    json.dump(summary, open(os.path.join(out, 'summary.json'), 'w'), indent=1)
    print('END', json.dumps(summary), flush=True)


import json as _j
_j.dump({'sources': [{'name': 's3', 'stream': 'routing_pool', 'kind': 'jsonl_gz_tar', 'paths': ['/home/jjyeung/okit/i/eb3429c5/eb3429c5.tar']}]}, open('spec3.json','w'))
sys.argv=['x','spec3.json','o3']
main()

PYEOF
ls -la o3
