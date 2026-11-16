import sys, base64, io, re, tarfile, importlib.util, json, traceback, tempfile, uuid
from pathlib import Path
sys.path.insert(0, '/scratch/jjyeung/orch_n30/review_d0r2/cur/tests')
kitroot = Path(sys.argv[1]); step = int(sys.argv[2])
sys.path.insert(0, str(kitroot/'kit/launcher'))
import orchard_launcher as L
root = Path(tempfile.mkdtemp(dir='/scratch/jjyeung/orch_n30/review_d0r2/tmp'))
config = L.prepare('a'+uuid.uuid4().hex[:12], root/'prepared', step)
import offline_guard  # deny subprocess/socket from here on
m = re.search(r"raw=base64.b64decode\('([^']+)'", (root/'prepared/BATCH.sh').read_text())
with tarfile.open(fileobj=io.BytesIO(base64.b64decode(m[1]))) as a:
    for it in a:
        t = root/it.name; t.parent.mkdir(exist_ok=True); t.write_bytes(a.extractfile(it).read())
spec = importlib.util.spec_from_file_location('packaged_job', root/'bootstrap/orchard_job.py')
job = importlib.util.module_from_spec(spec); spec.loader.exec_module(job)
reached = []
orig_run = job.run
def spy(r, c):
    reached.append(True); return orig_run(r, c)
job.run = spy
sys.argv = ['orchard_job.py', '--root', str(root), '--config', str(root/'bootstrap/CONFIG.json')]
try:
    job.main()
except SystemExit as e:
    print('SystemExit', e.code)
except BaseException as e:
    print('EXC', type(e).__name__, str(e)[:200])
print('reached_run', bool(reached), 'root', root)
