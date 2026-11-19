"""Verify package hashes and apply each patch only to copied input tools."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile

PACKAGE = Path(__file__).resolve().parents[1]
L = PACKAGE.parent
NAMES = ('dry_count.py', 'lane_code_filter.py')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(path):
    return {line.split()[1]: line.split()[0] for line in path.read_text().splitlines()}


def main():
    pre = hashes(PACKAGE / 'PREIMAGE.sha256')
    post = hashes(PACKAGE / 'POSTIMAGE.sha256')
    inputs = hashes(L / 'in/TOOLS.sha256')
    assert set(pre) == set(post) == set('tools/' + n for n in NAMES)
    for name in NAMES:
        assert pre['tools/' + name] == inputs[name] == digest(L / 'in/tools' / name)
        assert post['tools/' + name] == digest(PACKAGE / 'tools' / name)
    print('PASS PREIMAGE matches supplied hashes and input bytes; POSTIMAGE matches replacement bytes')
    sums = hashes(PACKAGE / 'SHA256SUMS')
    files = {p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob('*')
             if p.is_file() and p.name != 'SHA256SUMS'}
    assert set(sums) == files
    assert all(digest(PACKAGE / name) == value for name, value in sums.items())
    print('PASS SHA256SUMS: complete coverage and all %d hashes verify' % len(sums))
    root = Path(tempfile.mkdtemp(prefix='tmp_package_', dir=str(L / 'work')))
    (root / 'tools').mkdir()
    assert set(p.name for p in (PACKAGE / 'patches').iterdir()) == set(n + '.diff' for n in NAMES)
    for name in NAMES:
        shutil.copyfile(str(L / 'in/tools' / name), str(root / 'tools' / name))
        result = subprocess.run(['patch', '-p1', '--batch', '--forward', '-i',
                                 str(PACKAGE / 'patches' / (name + '.diff'))], cwd=str(root),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        assert result.returncode == 0, (result.stdout, result.stderr)
        assert (root / 'tools' / name).read_bytes() == (PACKAGE / 'tools' / name).read_bytes()
    print('PASS both unified patches reproduce complete replacements from copied inputs')
    saved = L / 'out_round1'
    assert all(digest(saved / name) == value for name, value in hashes(saved / 'SHA256SUMS').items())
    print('PASS preserved out_round1 matches every original package checksum')


if __name__ == '__main__':
    main()
