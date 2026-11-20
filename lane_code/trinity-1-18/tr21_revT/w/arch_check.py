import sys, hashlib, tarfile
from pathlib import Path, PurePosixPath
expected = {}
for line in Path('patched.files.sha256').read_text().splitlines():
    h, n = line.split('  ', 1); expected[n] = h
p = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24v/out/kit_n_go/k/t_e047002134f979bd.tar')
files = {}
with tarfile.open(p, 'r:*') as a:
    for m in a:
        assert m.isfile() and not PurePosixPath(m.name).is_absolute() and '..' not in PurePosixPath(m.name).parts
        files[m.name] = hashlib.sha256(a.extractfile(m).read()).hexdigest()
print('archive members', len(files), 'equals patched tree inventory:', files == expected)
