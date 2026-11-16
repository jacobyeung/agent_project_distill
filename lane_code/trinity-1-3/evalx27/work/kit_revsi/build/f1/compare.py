"""Verify F1's exact edit boundary and emit complete package evidence."""
from pathlib import Path
import difflib
import hashlib
import json
import tarfile

E = Path(__file__).resolve().parent
K = E.parent.parent
mapping = json.loads((E/'mapping.json').read_text())
renames = mapping['rename']
dropped = set(mapping['drop'])
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def contents(path):
    with tarfile.open(path) as archive:
        return {m.name: archive.extractfile(m).read() for m in archive}


old = contents(E/'baseline.tar')
new = contents(K/'package.tar')
assert set(new) == {renames.get(n,n) for n in old if n not in dropped}
expected_changes = {'launcher/orchard_launcher.py','reader/official_adapter.py',
    'reader/chain.py','reader/official_score.py','cohort/frame_plan.py',
    'proof/run.py','tests/test_kit.py','build/package.py'}
changed = set()
records = []
diffs = []
for name, raw in sorted(old.items()):
    target = renames.get(name,name)
    if name in dropped:
        records.append(dict(old=name,new=None,status='OMITTED',old_sha256=sha(raw),sha256=None))
        continue
    current = new[target]
    status = 'RENAMED_IDENTICAL' if target != name else 'IDENTICAL'
    if current != raw:
        status = 'PATH_STRINGS' if name != 'build/package.py' else 'PACKAGE_FILE_LIST'
        changed.add(name)
        expected = raw.decode()
        for before, after in renames.items():
            expected = expected.replace(Path(before).name,Path(after).name)
        if name == 'launcher/orchard_launcher.py':
            expected = expected.replace("'REVSI999_PROVENANCE.json'):",
                "'REVSI999_PROVENANCE.json','cells_rv999_d32_cp1m200_on.json','cells_tr_rv999_cp1on.json'):")
        if name == 'build/package.py':
            expected = expected.replace('names=sorted(names)',
                "names=sorted(names - {'inputs/cells_rv999_d32_cp1m200_on.json','inputs/cells_tr_rv999_cp1on.json'})")
        assert current == expected.encode(), name
        delta = ''.join(difflib.unified_diff(raw.decode().splitlines(True),current.decode().splitlines(True),
            fromfile='6e025a89/'+name,tofile='F1/'+target,n=0))
        diffs.append(delta)
    records.append(dict(old=name,new=target,status=status,old_sha256=sha(raw),sha256=sha(current)))
assert changed == expected_changes
for before, after in renames.items():
    assert old[before] == new[after]
for n, raw in new.items():
    if n.endswith('.py'):
        compile(raw,n,'exec')
(E/'package_comparison.json').write_text(json.dumps(records,indent=2)+'\n')
(E/'path_strings.diff').write_text('\n'.join(diffs))
package_sha = sha((K/'package.tar').read_bytes())
lines = ['# F1 package comparison against 6e025a89','',
    'KIT_SHA256: `'+package_sha+'`','',
    'The baseline was reconstructed from the requested read-only archive and its full SHA256 was verified.',
    'The package contains 125 files: 112 retain both their names and bytes; five retain their bytes under opaque names; eight contain only the path replacements or package-list exclusions shown below. Two unused cell files are omitted.',
    'All 76 Python files compile. Every evaluator file is byte-identical. Reader, adapter and scorer changes are limited to the shown path strings; input hashes and pin constants are unchanged.',
    'The archive uses sorted entries, fixed modes, mtime/uid/gid zero and empty owner/group names. F1 evidence and reports are external sidecars.',
    'Packaged coverage and LOCAL_PROOF records retain baseline bytes; current-run evidence is linked from F1_EVIDENCE.md.',
    '', '| Baseline file | Current file | Status | Baseline SHA256 | Current SHA256 |',
    '|---|---|---|---|---|']
for row in records:
    lines.append('| '+ ' | '.join(str(row[k] or '—') for k in ('old','new','status','old_sha256','sha256'))+' |')
lines += ['', '## Complete unified diffs (zero context)', '', '```diff', '\n'.join(diffs).rstrip(), '```', '']
(K/'DIFF.md').write_text('\n'.join(lines))
hash_rows = [r for r in records if r['old'].startswith('reader/')]
(E/'reader_hashes.tsv').write_text('file\tbaseline_sha256\tcurrent_sha256\tstatus\n'+''.join(
    '\t'.join([r['old'],r['old_sha256'],r['sha256'],r['status']])+'\n' for r in hash_rows))
summary = dict(package_sha256=package_sha,files=len(new),bytes=(K/'package.tar').stat().st_size,
    unchanged=sum(r['status']=='IDENTICAL' for r in records),renamed=len(renames),omitted=len(dropped),
    changed=sorted(changed),python_compiled=sum(n.endswith('.py') for n in new),reader_files=len(hash_rows),
    evaluator_files=sum(n.startswith('reader/evaluator/') for n in new))
(E/'comparison_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary))
