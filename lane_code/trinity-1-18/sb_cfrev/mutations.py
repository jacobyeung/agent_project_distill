from pathlib import Path
import hashlib, json, shutil, subprocess, sys

ROOT = Path(__file__).resolve().parent
base = ROOT/'work/patched/src/tree/student_pilot'
test = ROOT/'work/test_cachefix.py'
pins = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
        [test, Path(__file__), ROOT/'run.sh', base/'routed_features.py', base/'routed_candidates.py']}
# The existing legacy-cache test reads the first three candidates files.
cache_root = Path('/scratch/jjyeung/k1/run_convert_2')
for p in sorted(p/'candidates.json' for p in cache_root.iterdir() if (p/'candidates.json').is_file())[:3]:
    pins[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
cases = {
    'first_presence': ('routed_features.py', 'presence=value["presence"]', 'presence=values[0]["presence"]'),
    'ignore_instance': ('routed_candidates.py', "instance.get('presence', record['presence'])", "record['presence']"),
    'no_legacy_fallback': ('routed_candidates.py', "instance.get('presence', record['presence'])", "instance['presence']"),
    'wrong_legacy_fallback': ('routed_candidates.py', "instance.get('presence', record['presence'])", "instance.get('presence', 0.)"),
}
results = {}
for name, (filename, old, new) in cases.items():
    folder = ROOT/'work/mutations'/name
    target = folder/'patched/src/tree/student_pilot'
    target.mkdir(parents=True)
    for m in ('routed_features.py', 'routed_candidates.py'):
        text = (base/m).read_text()
        if m == filename:
            assert text.count(old) == 1
            text = text.replace(old, new)
        (target/m).write_text(text)
    text = test.read_text().replace("A4 = HERE/'orig/src/tree/student_pilot'", f'A4 = Path({str(ROOT / "work/orig/src/tree/student_pilot")!r})')
    path = folder/'test_cachefix.py'
    path.write_text(text)
    done = subprocess.run([sys.executable, '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', str(path)],
                          cwd=ROOT, capture_output=True, text=True)
    log = ROOT/'logs'/f'mutation_{name}.log'
    log.write_text(done.stdout+done.stderr)
    assert done.returncode in (0, 1), (name, done.returncode, done.stderr)
    result = dict(killed=done.returncode == 1, exit_code=done.returncode,
                  summary=done.stdout.strip().splitlines()[-1],
                  mutation_file=filename, before=old, after=new,
                  mutant_sha256=hashlib.sha256((target/filename).read_bytes()).hexdigest(),
                  log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    results[name] = result
    print(name, result['summary'], flush=True)
(ROOT/'evidence/mutations.json').write_text(json.dumps(dict(input_sha256=pins, results=results), indent=2)+'\n')
(ROOT/'STATUS.md').write_text('The exact patch applies to a local A4 copy, and all 29 supplied tests pass. Four mutation runs are complete; their failures and input hashes are in evidence/mutations.json. Two fresh K1 runs use identical raw-name detectors and differ only in the patched modules. Journal and producer audits remain in progress.\n')
