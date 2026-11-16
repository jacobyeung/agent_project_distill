#!/usr/bin/env python3
"""Stream the listed k6tk frames as one tar on stdout (runs on the Orchard login node; stdlib only; reads only).

usage: pull.py LIST STORE
LIST : one frame per line; the first 64-hex token on each line is the frame sha256 (other text is ignored).
STORE: the k6tk store root (MEMBERS.tsv.gz maps sha -> shard; shards live in parts/<tag>/<shard>.tar).
Each member keeps its store name <sha[:2]>/<sha>.png. A member whose bytes do not hash to its sha, or a listed sha the
store lacks, stops the stream with a nonzero exit. Shards are read by seeking past unwanted
members, and a shard is left as soon as its last wanted member is out. Progress goes to stderr.
"""
import gzip
import hashlib
import io
import re
import sys
import tarfile
from pathlib import Path


def main(listing, store):
    store = Path(store)
    want = []
    for line in Path(listing).read_text().splitlines():
        m = re.search(r'\b[0-9a-f]{64}\b', line)
        if m:
            want.append(m.group(0))
    want = sorted(set(want))
    shard_of = {}
    wanted = set(want)
    with gzip.open(store / 'MEMBERS.tsv.gz', 'rt') as stream:
        for line in stream:
            sha, shard = line.rstrip('\n').split('\t')[:2]
            if sha in wanted:
                shard_of[sha] = shard
    missing = wanted - set(shard_of)
    if missing:
        sys.exit(f'pull: {len(missing)} listed frames are not in the store, e.g. {sorted(missing)[0]}')
    by_shard = {}
    for sha, shard in shard_of.items():
        by_shard.setdefault(shard, set()).add(sha)
    print(f'pull: {len(want)} frames from {len(by_shard)} shards', file=sys.stderr, flush=True)
    out = tarfile.open(fileobj=sys.stdout.buffer, mode='w|', format=tarfile.USTAR_FORMAT)
    done = 0
    for shard in sorted(by_shard):
        path = store / 'parts' / shard.split('_')[0] / shard
        left = set(by_shard[shard])
        with tarfile.open(path, mode='r:') as tf:
            for member in tf:
                if not left:
                    break
                sha = Path(member.name).stem
                if not member.isfile() or sha not in left:
                    continue
                data = tf.extractfile(member).read()
                if hashlib.sha256(data).hexdigest() != sha:
                    sys.exit(f'pull: {member.name} in {shard} does not match its sha')
                info = tarfile.TarInfo(f'{sha[:2]}/{sha}.png')
                info.size, info.mtime, info.mode = len(data), member.mtime, 0o644
                out.addfile(info, io.BytesIO(data))
                left.discard(sha)
                done += 1
        if left:
            sys.exit(f'pull: {len(left)} frames not found inside {shard}')
        print(f'pull: {shard} done, {done}/{len(want)}', file=sys.stderr, flush=True)
    out.close()
    sys.stdout.buffer.flush()


if __name__ == '__main__':
    main(*sys.argv[1:3])
