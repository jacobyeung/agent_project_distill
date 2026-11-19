"""Select unfinished D IDs from an authenticated published partial return."""
import argparse
import json
from pathlib import Path
from dbuild.make_items_d import subset
from return_tools import read, unpack, load, validate_manifest
from fetch_validation import digest


def make(items, package, archive, exit_path, receipt, work, out):
    parent, expected = validate_manifest(items, package)
    if parent.get('remainder'):
        raise ValueError('Use the full D parent manifest')
    ex = unpack(archive, exit_path, receipt, package, work)
    rows, meta = load(work, items, package)
    if ex['complete'] or len(rows) == parent['count']:
        raise ValueError('Return is complete; no remainder needed')
    provenance = dict(parent_plan=expected['plan'], parent_token=expected['token'],
                      parent_items_sha256=digest(items),
                      partial_archive_sha256=digest(archive),
                      partial_return_token=ex['token'], export_binding=expected['export_binding'])
    result = subset(parent, sorted(rows), provenance)
    with Path(out).open('x') as stream:
        json.dump(result, stream, sort_keys=True, indent=1, allow_nan=False)
        stream.write('\n')
    return dict(completed=len(rows), remaining=result['count'], items=str(out),
                items_sha256=digest(out), provenance=provenance)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('items','package','archive','exit','receipt','work','out'):
        p.add_argument('--'+name, required=True)
    a = p.parse_args()
    print(json.dumps(make(a.items,a.package,a.archive,a.exit,a.receipt,a.work,a.out), sort_keys=True))


if __name__ == '__main__':
    main()
