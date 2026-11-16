"""Read-only SQLite table scanner over a byte range that may be split across files or sit inside a tar.

Stdlib only. Used where the store cannot be opened by sqlite3 without first copying it
(raw byte splits `x.p00, x.p01, ...`, or an uncompressed tar member). It walks the table
b-tree of one table in rowid order and yields decoded records. Interior/leaf table pages and
overflow chains are supported; index b-trees are never read. WAL files are not consulted, so
the store must be a checkpointed, immutable file (the case for every sealed row store).

usage (CLI): sqlro.py TABLE OFFSET PART [PART ...]   -> prints rowcount and first record keys
"""
import os
import struct
import sys


class SplitFile:
    """Random access over concatenated parts, starting at a byte offset (e.g. a tar member)."""

    def __init__(self, parts, offset=0, length=None):
        self.parts = [(p, os.path.getsize(p)) for p in parts]
        self.offset = offset
        self.total = sum(n for _, n in self.parts)
        self.length = self.total - offset if length is None else length
        self.handles = {}

    def pread(self, off, n):
        if off < 0 or off + n > self.length:
            raise ValueError('read outside the store')
        off += self.offset
        out = []
        base = 0
        for path, size in self.parts:
            if n == 0:
                break
            if off < base + size:
                local = off - base
                take = min(n, size - local)
                fh = self.handles.get(path)
                if fh is None:
                    fh = self.handles[path] = open(path, 'rb')
                out.append(os.pread(fh.fileno(), take, local))
                if len(out[-1]) != take:
                    raise IOError('short read')
                off += take
                n -= take
            base += size
        if n:
            raise IOError('read past the parts')
        return b''.join(out)

    def close(self):
        for fh in self.handles.values():
            fh.close()


def varint(buf, i):
    v = 0
    for k in range(8):
        b = buf[i + k]
        v = (v << 7) | (b & 0x7F)
        if b < 0x80:
            return v, i + k + 1
    return (v << 8) | buf[i + 8], i + 9


class Store:
    def __init__(self, src):
        self.src = src
        h = src.pread(0, 100)
        if h[:16] != b'SQLite format 3\x00':
            raise ValueError('not an SQLite file')
        ps = struct.unpack('>H', h[16:18])[0]
        self.page_size = 65536 if ps == 1 else ps
        self.reserved = h[20]
        if struct.unpack('>I', h[56:60])[0] not in (0, 1):
            raise ValueError('only UTF-8 stores are supported')
        if h[18] == 2 or h[19] == 2:
            raise ValueError('WAL-mode store: checkpoint first')
        self.usable = self.page_size - self.reserved

    def page(self, n):
        return self.src.pread((n - 1) * self.page_size, self.page_size)

    def payload(self, page, i):
        P, i = varint(page, i)
        return P, i

    def _cell_record(self, page, ptr):
        P, i = varint(page, ptr)
        rowid, i = varint(page, i)
        U = self.usable
        X = U - 35
        if P <= X:
            return rowid, page[i:i + P]
        M = ((U - 12) * 32 // 255) - 23
        K = M + ((P - M) % (U - 4))
        local = K if K <= X else M
        data = [page[i:i + local]]
        nxt = struct.unpack('>I', page[i + local:i + local + 4])[0]
        need = P - local
        while need > 0:
            if nxt == 0:
                raise ValueError('overflow chain ends early')
            ov = self.page(nxt)
            nxt = struct.unpack('>I', ov[:4])[0]
            take = min(need, U - 4)
            data.append(ov[4:4 + take])
            need -= take
        return rowid, b''.join(data)

    def scan(self, root):
        """Yield (rowid, raw record) of a table b-tree in rowid order."""
        stack = [root]
        while stack:
            n = stack.pop()
            page = self.page(n)
            hdr = 100 if n == 1 else 0
            kind = page[hdr]
            ncell = struct.unpack('>H', page[hdr + 3:hdr + 5])[0]
            if kind == 0x0D:
                ptrs = struct.unpack('>%dH' % ncell, page[hdr + 8:hdr + 8 + 2 * ncell])
                for ptr in ptrs:
                    yield self._cell_record(page, ptr)
            elif kind == 0x05:
                right = struct.unpack('>I', page[hdr + 8:hdr + 12])[0]
                ptrs = struct.unpack('>%dH' % ncell, page[hdr + 12:hdr + 12 + 2 * ncell])
                children = [struct.unpack('>I', page[p:p + 4])[0] for p in ptrs] + [right]
                stack.extend(reversed(children))
            else:
                raise ValueError('unexpected page type %d at page %d' % (kind, n))

    @staticmethod
    def decode(rec):
        hsize, i = varint(rec, 0)
        types = []
        while i < hsize:
            t, i = varint(rec, i)
            types.append(t)
        pos = hsize
        out = []
        for t in types:
            if t == 0:
                out.append(None)
            elif 1 <= t <= 6:
                n = (1, 2, 3, 4, 6, 8)[t - 1]
                out.append(int.from_bytes(rec[pos:pos + n], 'big', signed=True))
                pos += n
            elif t == 7:
                out.append(struct.unpack('>d', rec[pos:pos + 8])[0])
                pos += 8
            elif t in (8, 9):
                out.append(t - 8)
            elif t >= 12:
                n = (t - 12) // 2 if t % 2 == 0 else (t - 13) // 2
                v = rec[pos:pos + n]
                out.append(v if t % 2 == 0 else v.decode('utf-8'))
                pos += n
            else:
                raise ValueError('reserved serial type')
        return out

    def tables(self):
        out = {}
        for rowid, rec in self.scan(1):
            typ, name, tbl, root, sql = self.decode(rec)
            if typ == 'table':
                out[name] = (root, sql)
        return out

    def rows(self, table):
        root, sql = self.tables()[table]
        for rowid, rec in self.scan(root):
            vals = self.decode(rec)
            yield rowid, vals


def tar_member(tar_path, name):
    """(offset, size) of an uncompressed tar member, read from headers only."""
    import tarfile
    with tarfile.open(tar_path, 'r:') as t:
        for m in t:
            if m.name == name:
                return m.offset_data, m.size
    raise KeyError(name)


if __name__ == '__main__':
    table, offset, parts = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
    s = Store(SplitFile(parts, offset))
    n = 0
    for rowid, vals in s.rows(table):
        n += 1
    print(n)
