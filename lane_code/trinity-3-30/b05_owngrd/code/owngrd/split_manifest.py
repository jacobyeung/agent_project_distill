"""Filter a teacher manifest by K1 split and issue a fresh eligibility receipt."""
import argparse
from collections import Counter

from .common import atomic_write_json, read_json, sha256_file
from .eligibility import Gate


def split_manifest(source, split, output):
    if split not in ('train', 'heldout', 'all'):
        raise ValueError('Unknown K1 split')
    manifest = read_json(source)
    captures = [c for c in manifest['captures'] if split == 'all' or c['k1_split'] == split]
    manifest['captures'] = captures
    manifest['gate_receipt'] = Gate(manifest['gate_root']).admit(captures)
    manifest['source'] = dict(manifest=str(source), manifest_sha256=sha256_file(source), split=split)
    manifest['counts'] = dict(captures=len(captures), names=sum(len(c['names']) for c in captures),
        by_role=dict(Counter(n['role'] for c in captures for n in c['names'])),
        by_split=dict(Counter(c['k1_split'] for c in captures)))
    atomic_write_json(output, manifest)
    return manifest


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--in', dest='source', required=True)
    ap.add_argument('--split', choices=('train', 'heldout', 'all'), required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args(argv)
    split_manifest(a.source, a.split, a.out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
