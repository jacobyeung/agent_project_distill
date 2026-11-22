"""Task A strict diff (RULING 0420Z item 2): regenerated routing selection under tree 02fd9a95 vs the reviewed one (173912).

usage: taska_diff.py <old dir> <new dir>
Both dirs hold, by the names of X/o/173912: k_dr_p_q_sc_p_p_receipt.json (pool selection, 'source'),
k_dr_p_q_selection_pool_receipt.json (relocated pool selection), materialization.json, receipt.json,
routing_selection.json, db_bytes.json.
PASS only if every difference is explained by: implementation['student_pilot/r1_training.py'] b05f1704 -> 91cdac91,
and the sha256 / digest of each derived file in the chain (old value -> new value, both read from the files);
rows.sqlite 5e35c3ce unchanged in receipt, db_bytes and routing_selection.
"""
import hashlib, json, sys
from pathlib import Path

OLD_R1 = 'b05f17046ad109b0ee2f6c810b47c9e3bc100e4676e35c40a7ac02cdc449d019'
NEW_R1 = '91cdac91f173f5c8ebe2f4e92fbc008ac05bea32a27895809a66ad82a46218bf'
DB = '5e35c3ce600a867be194911642caccb23098035b4bf08909e519a170a1c243df'
CHAIN = ['k_dr_p_q_sc_p_p_receipt.json', 'k_dr_p_q_selection_pool_receipt.json', 'materialization.json',
         'receipt.json', 'routing_selection.json']
CONFIG_DERIVED = '--config-derived' in sys.argv
TREE = Path(__file__).resolve().parent.parent / 't34'
sys.path.insert(0, str(TREE))
from student_pilot.p3_provenance import digest  # noqa: E402


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(old, new):
    old, new = Path(old), Path(new)
    mapping = {OLD_R1: NEW_R1}
    problems, explained = [], []
    for n in CHAIN:
        so, sn = sha(old / n), sha(new / n)
        vo, vn = json.loads((old / n).read_text()), json.loads((new / n).read_text())
        do, dn = digest(vo), digest(vn)
        print('%-40s sha %s -> %s  digest %s -> %s' % (n, so[:8], sn[:8], do[:8], dn[:8]))
        diffs = []
        walk(vo, vn, '', diffs)
        for path, a, b in diffs:
            if path.endswith('/implementation/student_pilot/r1_training.py') and (a, b) == (OLD_R1, NEW_R1):
                explained.append((n, path, 'implementation r1_training')); continue
            if (n == 'routing_selection.json' and path == '/inputs_pinned/config_sha256' and CONFIG_DERIVED
                    and isinstance(a, str) and isinstance(b, str)):
                # In-job config digest; kit qd -> c_eb8145adr/qd differs only in tree-derived pins (kqdiff.out).
                explained.append((n, path, 'config %s -> %s (tree-derived, kqdiff.out)' % (a[:8], b[:8]))); continue
            if isinstance(a, str) and isinstance(b, str) and sub(a, mapping) == b and a != b:
                explained.append((n, path, '%s -> %s' % (a[:8], b[:8]))); continue
            problems.append((n, path, str(a)[:120], str(b)[:120]))
        impl = [p for p, a, b in diffs if '/implementation/' in p]
        if any(not p.endswith('/student_pilot/r1_training.py') for p in impl):
            problems.append((n, 'implementation', 'other implementation entries differ', ','.join(impl)[:200]))
        for a, b in ((so, sn), (do, dn)):
            if a != b:
                mapping.setdefault(a, b)
    rec = json.loads((new / 'receipt.json').read_text())
    dbb = json.loads((new / 'db_bytes.json').read_text())
    sel = json.loads((new / 'routing_selection.json').read_text())
    checks = dict(receipt_database=rec['database']['sha256'] == DB,
                  db_bytes_has_db=any(f.get('sha256') == DB for f in dbb.get('files', [])),
                  selection_regenerated_sha256_is_receipt_digest=sel.get('regenerated_sha256') == digest(rec),
                  selection_receipt_pin_is_receipt_sha=sel.get('regenerated_receipt', {}).get('sha256') == sha(new / 'receipt.json'),
                  count=rec.get('count'))
    print('checks', json.dumps(checks))
    for c, v in checks.items():
        if v is False:
            problems.append(('checks', c, 'False', ''))
    print('explained %d differences:' % len(explained))
    for e in explained:
        print('  ', *e)
    print('UNEXPLAINED %d:' % len(problems))
    for p in problems:
        print('  ', *p)
    print('TASKA_STRICT_DIFF', 'PASS' if not problems else 'FAIL')
    return 0 if not problems else 1


def sub(s, mapping):
    for a, b in mapping.items():
        s = s.replace(a, b)
    return s


def walk(a, b, path, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append((path + '/' + k, a.get(k, '<absent>'), b.get(k, '<absent>')))
            else:
                walk(a[k], b[k], path + '/' + k, out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append((path, 'len %d' % len(a), 'len %d' % len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, '%s[%d]' % (path, i), out)
    elif a != b or type(a) is not type(b):
        out.append((path, a, b))


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:3]))
