"""Zip central-directory helpers copied from k6 wa.py (central_dir parsing, stamp); no network."""
import os, struct


def eocd(tail):
    i = tail.rfind(b"PK\x05\x06")
    if i < 0:
        raise RuntimeError("no eocd")
    n_entries, cd_size, cd_off = struct.unpack("<HII", tail[i + 10:i + 20])
    if cd_off == 0xFFFFFFFF or n_entries == 0xFFFF:
        j = tail.rfind(b"PK\x06\x06")
        n_entries, cd_size, cd_off = struct.unpack("<QQQ", tail[j + 32:j + 56])
    return n_entries, cd_size, cd_off


def parse_cd(cd):
    ents, p = [], 0
    while p + 46 <= len(cd) and cd[p:p + 4] == b"PK\x01\x02":
        method = struct.unpack("<H", cd[p + 10:p + 12])[0]
        csize, usize = struct.unpack("<II", cd[p + 20:p + 28])
        nl, el, cl = struct.unpack("<HHH", cd[p + 28:p + 34])
        lho = struct.unpack("<I", cd[p + 42:p + 46])[0]
        name = cd[p + 46:p + 46 + nl].decode("utf-8", "replace")
        extra = cd[p + 46 + nl:p + 46 + nl + el]
        if csize == 0xFFFFFFFF or usize == 0xFFFFFFFF or lho == 0xFFFFFFFF:
            q = 0
            while q + 4 <= len(extra):
                hid, hl = struct.unpack("<HH", extra[q:q + 4])
                if hid == 1:
                    vals = list(struct.unpack("<" + "Q" * (hl // 8), extra[q + 4:q + 4 + 8 * (hl // 8)]))
                    if usize == 0xFFFFFFFF: usize = vals.pop(0)
                    if csize == 0xFFFFFFFF: csize = vals.pop(0)
                    if lho == 0xFFFFFFFF: lho = vals.pop(0)
                q += 4 + hl
        ents.append((name, method, csize, lho, nl))
        p += 46 + nl + el + cl
    return ents


def stamp(name):
    b = os.path.basename(name)
    if not b.endswith(".png") or "_" not in b:
        return None
    try:
        return float(b[:-4].rpartition("_")[2])
    except ValueError:
        return None


def frames_of(ents):
    """wa.py's frame table: (ts, name, method, csize, lho, nl) sorted by ts, png members only."""
    fr = [(stamp(n), n, m, cs, lho, nl) for (n, m, cs, lho, nl) in ents]
    return sorted(f for f in fr if f[0] is not None)


def nearest(ts, t):
    """wa.py's pick: index of the member nearest t among searchsorted neighbours, or None."""
    import numpy as np
    j = int(np.searchsorted(ts, t))
    best = None
    for jj in (j - 1, j):
        if 0 <= jj < len(ts) and (best is None or abs(ts[jj] - t) < abs(ts[best] - t)):
            best = jj
    return best


def member_range(f):
    """Byte range [a, z] for one member, as wa.py's group bound for a single member."""
    _, _, _, cs, lho, nl = f
    return lho, lho + 30 + nl + cs + 1024
