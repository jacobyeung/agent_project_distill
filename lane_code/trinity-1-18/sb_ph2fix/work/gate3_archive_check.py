"""Compare archived files and GPU manifest rows; write the two-file patch."""
import difflib
import hashlib
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT/'out/sb_ph2fix2.tar'
EXPECTED = '3440a9ff995e6420a345f848f2bb9a0aee5c23ef04b6d31f57e6712e437e3b94'
CHANGES = {'sb_mask_phrase/part2/gate.py', 'sb_mask_phrase/part2/test_part2.py'}


def digest(stream):
    h = hashlib.sha256()
    for block in iter(lambda: stream.read(8 << 20), b''):
        h.update(block)
    return h.hexdigest()


with ARCHIVE.open('rb') as stream:
    archive_sha = digest(stream)
print('archive_sha256', archive_sha, flush=True)
assert archive_sha == EXPECTED
inventory = json.loads((ROOT/'out/STAGING_PART2.json').read_text())['inventory']
staged = {r['staged_path']: r for r in inventory}
seen = set()
differences = []
patch = []
regular = 0
with tarfile.open(ARCHIVE, 'r|') as tar:
    for member in tar:
        name = member.name
        path = ROOT/name
        assert path.is_relative_to(ROOT) and '..' not in Path(name).parts
        if member.isfile():
            regular += 1
            with tar.extractfile(member) as stream:
                if name in CHANGES:
                    original = stream.read()
                    original_sha = hashlib.sha256(original).hexdigest()
                    patch.extend(difflib.unified_diff(original.decode().splitlines(True),
                                                     path.read_text().splitlines(True),
                                                     fromfile='a/'+name, tofile='b/'+name))
                else:
                    original_sha = digest(stream)
            if path.is_file() and not path.is_symlink():
                with path.open('rb') as stream:
                    current_sha = digest(stream)
            else:
                current_sha = 'MISSING_OR_NOT_REGULAR'
            if current_sha != original_sha:
                differences.append(name)
                print('DIFF', name, original_sha, current_sha, flush=True)
            if name in staged:
                row = staged[name]
                assert member.size == row['bytes'] and original_sha == row['sha256'], name
                if name not in CHANGES:
                    assert current_sha == row['sha256'], name
                seen.add(name)
        elif member.issym():
            if not path.is_symlink() or str(path.readlink()) != member.linkname:
                differences.append(name)
                print('DIFF_SYMLINK', name, flush=True)
        elif member.isdir():
            assert path.is_dir(), name
        else:
            raise AssertionError(('unexpected archive member type', name, member.type))
assert seen == staged.keys(), sorted(staged.keys()-seen)
assert CHANGES <= set(differences)
(ROOT/'out/GATE3.patch').write_text(''.join(patch))
print('regular_members', regular)
print('verified_archive_staged_files', len(seen))
print('unchanged_workspace_staged_files', len(seen-CHANGES))
print('patch_files', ', '.join(sorted(CHANGES)))
print('all_archive_member_differences', ', '.join(differences))
