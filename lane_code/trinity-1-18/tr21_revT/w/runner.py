import json, os, resource, shutil, sys, tempfile, time, unittest
from pathlib import Path

tree, test_file = Path(sys.argv[1]).resolve(), sys.argv[2]
out_json, tmp = Path(sys.argv[3]).resolve(), Path(sys.argv[4]).resolve()
tmp.mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(tmp)
for key in ('TMPDIR', 'XDG_CACHE_HOME', 'HF_HOME', 'TORCH_HOME', 'TORCHINDUCTOR_CACHE_DIR', 'TRITON_CACHE_DIR', 'MPLCONFIGDIR'):
    os.environ[key] = str(tmp / key.lower())
    Path(os.environ[key]).mkdir(exist_ok=True)
resource.setrlimit(resource.RLIMIT_AS, (14 * 1024**3, 14 * 1024**3))
skipped = []
def keep(*args, **kwargs):
    skipped.append(str(args[0]) if args else '')
os.remove = os.unlink = os.rmdir = keep
shutil.rmtree = keep
for p in (str(tree / 'tests'), str(tree)):
    if p not in sys.path:
        sys.path.insert(0, p)

if __name__ == '__main__':
    os.chdir(tree)
    start = time.time()
    suite = unittest.defaultTestLoader.loadTestsFromName(Path(test_file).stem)
    result = unittest.TextTestRunner(verbosity=1, stream=sys.stderr).run(suite)
    out_json.write_text(json.dumps(dict(
        file=test_file, run=result.testsRun, failures=[t.id() for t, _ in result.failures],
        errors=[t.id() for t, _ in result.errors], skipped=len(result.skipped),
        failure_text={t.id(): tb[-800:] for t, tb in result.failures + result.errors},
        seconds=round(time.time() - start, 1), deletions_skipped=len(skipped)), indent=1))
