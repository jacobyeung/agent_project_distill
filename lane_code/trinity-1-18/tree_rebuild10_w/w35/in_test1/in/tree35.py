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
f = new/'student_pilot/r1_training.py'; text = f.read_text()
assert text.count(OLD_LINE) == 1 and text.splitlines(keepends=True)[97] == OLD_LINE
f.write_text(text.replace(OLD_LINE, NEW_LINE))
files_new = inventory(new); seal = digest(files_new)
changed = sorted(k for k in set(files_old) | set(files_new) if files_old.get(k) != files_new.get(k))
assert changed == ['student_pilot/r1_training.py'], changed
tar = OUT/('t_' + seal[:16] + '.tar'); archive(new, tar, files_new, compress=True)
check_archive(dict(path=str(tar), sha256=sha(tar)), files_new)
out.update(new_seal=seal, new_tar=str(tar), new_tar_sha256=sha(tar), new_tar_bytes=tar.stat().st_size,
           changed=changed, r1_training_old=files_old[changed[0]], r1_training_new=files_new[changed[0]],
           new_line_number=98, check_archive='ok')
import difflib
(OUT/'TREE_DIFF.patch').write_text(''.join(difflib.unified_diff(text.splitlines(True), f.read_text().splitlines(True),
    'a/student_pilot/r1_training.py', 'b/student_pilot/r1_training.py')))
assert len(f.read_text().splitlines()) == len(text.splitlines()) and f.read_text().splitlines()[98] == text.splitlines()[98]
out['line_count_same'] = True
(OUT/'TREE35.json').write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
print(json.dumps(out, indent=1, sort_keys=True))
