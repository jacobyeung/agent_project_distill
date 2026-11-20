"""Scan every new remote file, including decoded placement members and runtime surfaces."""
import ast
import base64
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent
WORDS = ('split', 'revsi', 'vsibench', 'scannet', 'arkit', 'distill', 'qgen', 'sam', 'qwen',
         'h1', 'h10', 'head', 'routing', 'faithful', 'devs1', 'g3t', 'camera', 'displacement',
         'rotation', 'movement', 'distance', 'r0', 'direction', 'own', 'room', 'selector',
         'parity', 'benchmark', 'dataset', 'model', 'tower', 'coverage', 'orchard')


def scan(text):
    # Identify words, including snake-case components; do not mistake hex digests for names.
    tokens = re.findall(r'[A-Za-z][A-Za-z0-9]*', text)
    return sorted({t for t in tokens if any(w == t.lower() or (len(w)>3 and t.lower().startswith(w)) for w in WORDS)})


def main():
    build = json.loads((ROOT/'BUILD.json').read_text())
    scripts = ['o_place.sh', 'o_cpu.sh', 'o_check_sub.sh', 'o_fetch.sh', 'SUBMIT.cmd']
    files = build['bound_files']+scripts
    checked = []
    for name in files:
        assert not scan(name), (name, scan(name))
        raw = (ROOT/name).read_text()
        if name == '1.json':
            cfg = json.loads(raw)
            # This input JSON is the sole descriptive-data boundary. API symbols and
            # authenticated inherited dependency paths are data, never public argv/log text.
            assert all(re.fullmatch('x[0-9a-z]+', k) for k in cfg)
            for row in cfg['x3']:
                assert all(re.fullmatch('x[0-9a-z]+', k) for k in row)
                assert re.fullmatch('[0-9a-f]{16}', row['x0'])
            checked.append(dict(file=name, input_data=True, keys='opaque'))
            continue
        if name == 'o_place.sh':
            tree = ast.parse(raw.split("<<'PY'\n", 1)[1].rsplit('\nPY', 1)[0])
            assignment = next(n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(v, ast.Name) and v.id=='assets' for v in n.targets))
            assets = ast.literal_eval(assignment.value)
            assert set(assets) == set(build['bound_files'])
            for n, b in assets.items():
                assert base64.b64decode(b) == (ROOT/n).read_bytes()
            raw = raw[:raw.index('assets=')] + raw[raw.index('\ndata=', raw.index('assets=')):]
        assert not scan(raw), (name, scan(raw))
        if name.endswith(('.sh', '.cmd')):
            subprocess.run(['bash', '-n', str(ROOT/name)], check=True)
        elif name.endswith('.py'):
            compile(raw, name, 'exec')
        checked.append(dict(file=name, passed=True))
    assert re.fullmatch('/project/community/jjyeung/[a-f][0-9a-f]+', build['path'])
    assert build['placement_bytes']+build['return_reserve_bytes'] < 2_000_000
    result = dict(passed=True, files=checked, decoded_placement_checked=True,
        exceptions=['Only 1.json values contain capture identities, inherited dependency paths, and existing API symbols.',
                    'Reused payload files are authenticated existing dependencies; they are not newly shipped files.'],
        public_names_opaque=True, logs='stdout/stderr suppressed; only numeric E codes emitted on failure')
    (ROOT/'SCAN.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(passed=True, files=len(files))))


if __name__ == '__main__':
    main()
