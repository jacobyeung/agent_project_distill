"""Opaque-word scan: shipped files, decoded transport, lane scripts and every Orchard-side output of the dry run."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parent
# K3d's deny list, extended with the rank 1 package's list and this kit's terms.
WORDS = ('split', 'revsi', 'vsibench', 'scannet', 'arkit', 'distill', 'qgen', 'sam', 'qwen', 'h1', 'h10', 'head',
         'routing', 'faithful', 'devs1', 'g3t', 'camera', 'displacement', 'rotation', 'movement', 'distance', 'r0',
         'direction', 'own', 'room', 'selector', 'parity', 'benchmark', 'dataset', 'model', 'tower', 'coverage',
         'orchard',
         'vsi', 'depth', 'ground', 'mask', 'reader', 'student', 'teacher', 'bench', 'k1', 't1', 'dev', 'devs',
         'vggt', 'scene', 'scannetpp', 'arkitscenes', 'gravity', 'pilot', 'carrier', 'lever', 'rank1', 'lane')
EXEMPT = '--exclude=orchard-community-4'


def scan(text):
    tokens = re.findall(r'[A-Za-z][A-Za-z0-9]*', text)
    return sorted({t for t in tokens if any(w == t.lower() or len(w) > 3 and t.lower().startswith(w) for w in WORDS)})


def main(dry_dirs):
    build = json.loads((ROOT/'BUILD.json').read_text())
    checked = []

    def inspect(name, raw):
        hits = scan(raw.decode('latin1'))
        checked.append(dict(file=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), hits=hits))
        assert not hits, (name, hits)

    for name in build['placed']['files']:
        raw = (ROOT/name).read_bytes()
        if name == '8.gz':
            import gzip
            import numpy as np
            plane = np.frombuffer(gzip.decompress(raw), dtype='<f2')
            assert plane.size == 60*32*51*51 and np.isfinite(plane).all()
            checked.append(dict(file=name, bytes=len(raw), numeric_only=True))
            continue
        inspect(name, raw)
        if name.endswith('.py'):
            compile(raw, name, 'exec')
    script = (ROOT/'o_place.sh').read_text()
    body = script.split("<<'PY'\n", 1)[1].rsplit('\nPY', 1)[0]
    tree = ast.parse(body)
    encoded = next(n.value.value for n in tree.body if isinstance(n, ast.Assign) and n.targets[0].id == 'ASSETS')
    inspect('o_place.sh:text', script.replace(encoded, '').encode())
    blob = base64.b64decode(encoded, validate=True)
    with tarfile.open(fileobj=io.BytesIO(blob), mode='r:gz') as archive:
        assert sorted(archive.getnames()) == sorted(build['placed']['files'])
        for item in archive:
            assert item.isfile() and archive.extractfile(item).read() == (ROOT/item.name).read_bytes()
    for name in build['lane_scripts']:
        raw = (ROOT/name).read_bytes()
        if name != 'o_place.sh':
            assert raw.count(EXEMPT.encode()) == (1 if name in ('o_cpu.sh', 'o_sub0.sh', 'o_sub1.sh') else 0)
            inspect(name, raw.replace(EXEMPT.encode(), b''))
        subprocess.run(['bash', '-n', str(ROOT/name)], check=True)
    for name in ('o_cpu.sh', 'o_sub0.sh', 'o_sub1.sh'):
        text = (ROOT/name).read_text()
        assert '--mem=200G' in text and '--time=00:50:00' in text and EXEMPT in text and '--no-requeue' in text
        assert 'test -z "$q"' in text and text.index('test -z "$q"') < text.index('reply=')
        assert ('--gres=gpu:1' in text) == (name != 'o_cpu.sh')
        assert 'advanced' not in text and 'a15_cot_ap'+build['token'] in text
    outputs = 0
    for d in dry_dirs:
        for path in sorted(Path(d).iterdir()):
            if path.is_file() and path.suffix in ('.json', '.err', '.txt'):
                inspect(str(path.relative_to(Path(d).parent.parent)), path.read_bytes())
                outputs += 1
    assert outputs, 'no dry-run outputs scanned'
    (ROOT/'SCAN_K5.json').write_text(json.dumps(dict(words=WORDS, checks=len(checked), files=checked), indent=1)+'\n')
    print('scan passed', len(checked))


if __name__ == '__main__':
    main(sys.argv[1:])
