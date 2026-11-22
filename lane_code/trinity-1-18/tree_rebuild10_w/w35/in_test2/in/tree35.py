"""fix21: tree T-mil. Extract the kit's sealed tree tar, prove the archive writer reproduces it, apply the one-line
patch to student_pilot/r1_training.py, and write the new tar with the tree's own inventory/archive/check_archive.
Usage: tree35.py <base kit> <work dir>   (work dir must not exist). Prints JSON."""
import sys, json, tarfile, hashlib, os
from pathlib import Path
KIT = Path(sys.argv[1]).resolve(); OUT = Path(sys.argv[2]).resolve()
OLD_SEAL = '9d2bbb8ad209d91e21e56121785f62b0dddf3c8d9f14db8d23daf6dcd1d3591b'
OLD_TAR = '5f2d77c4bc9905d877a259b666ac4a7fa6005de538730b806ceb249468699e38'
OLD_LINE = "    if recipe['milestones'] != [100, 200, 400, 600, 800, 1000]:\n"
NEW_LINE = ("    if not (recipe['milestones'] and all(type(m) is int for m in recipe['milestones']) and list(recipe['milestones']) == sorted(set(recipe['milestones'])) and set(recipe['milestones']) <= {100, 200, 400, 600, 800, 1000}):\n")
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not OUT.exists(); OUT.mkdir(parents=True)
old_tar = KIT/'k/t_e047002134f979bd.tar'; assert sha(old_tar) == OLD_TAR
old = OUT/'old'; new = OUT/'new'
with tarfile.open(old_tar) as t: t.extractall(old, filter='data')
with tarfile.open(old_tar) as t: t.extractall(new, filter='data')
sys.path.insert(0, str(old))
from student_pilot.source_seal import inventory, archive, check_archive
from student_pilot.p3_provenance import digest
out = {}
files_old = inventory(old); out['old_seal'] = digest(files_old); assert out['old_seal'] == OLD_SEAL
archive(old, OUT/'old_rebuilt.tar', files_old, compress=True)
out['archive_writer_reproduces_5f2d77c4'] = sha(OUT/'old_rebuilt.tar') == OLD_TAR; assert out['archive_writer_reproduces_5f2d77c4']
EDITS = [('student_pilot/r1_training.py', 98, OLD_LINE, NEW_LINE)]
if len(sys.argv) > 3 and sys.argv[3] == 'timeout':
    EDITS += [('student_pilot/carrier_c1_run.py', 2874,
               "    # Training collectives fail fast (15 min). Only the startup barriers and broadcasts, while\n",
               "    # Training collectives fail fast (30 min). Only the startup barriers and broadcasts, while\n"),
              ('student_pilot/carrier_c1_run.py', 2876,
               "    dist.init_process_group('gloo' if cpu else 'nccl', timeout=datetime.timedelta(seconds=30 if cpu else 900))\n",
               "    dist.init_process_group('gloo' if cpu else 'nccl', timeout=datetime.timedelta(seconds=30 if cpu else 1800))\n")]
import difflib
diffs = []
before = {}
for rel, n, old_line, new_line in EDITS:
    f = new/rel; text = f.read_text(); before.setdefault(rel, text)
    lines = text.splitlines(keepends=True)
    assert lines[n-1] == old_line and text.count(old_line) == 1, (rel, n)
    lines[n-1] = new_line; f.write_text(''.join(lines))
for rel, text in before.items():
    after = (new/rel).read_text()
    assert len(after.splitlines()) == len(text.splitlines())
    diffs.append(''.join(difflib.unified_diff(text.splitlines(True), after.splitlines(True), 'a/'+rel, 'b/'+rel)))
out['edits'] = [dict(file=r, line=n) for r, n, _, _ in EDITS]
out['line_count_same'] = True
files_new = inventory(new); seal = digest(files_new)
changed = sorted(k for k in set(files_old) | set(files_new) if files_old.get(k) != files_new.get(k))
assert changed == sorted({e[0] for e in EDITS}), changed
tar = OUT/('t_' + seal[:16] + '.tar'); archive(new, tar, files_new, compress=True)
check_archive(dict(path=str(tar), sha256=sha(tar)), files_new)
out.update(new_seal=seal, new_tar=str(tar), new_tar_sha256=sha(tar), new_tar_bytes=tar.stat().st_size,
           changed=changed, changed_files={k: [files_old[k], files_new[k]] for k in changed},
           r1_training_old=files_old['student_pilot/r1_training.py'], r1_training_new=files_new['student_pilot/r1_training.py'], check_archive='ok')
(OUT/'TREE_DIFF.patch').write_text(''.join(diffs))
(OUT/'TREE35.json').write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
print(json.dumps(out, indent=1, sort_keys=True))
