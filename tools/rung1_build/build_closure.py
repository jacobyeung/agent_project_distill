"""Pack work/aws_closure into closure_<sha12>.tar with its JOBS.json manifest (trinity-0-13). Prints the closure sha."""
import hashlib, io, json, os, tarfile
C = "/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/rung1_build_20261027/work/aws_closure"
P = "/scratch/jjyeung/rung1_push/closure"
names = ["entry.sh", "prep_inner.sh", "prep_rung1.py", "mn_train_inner.sh", "efa_probe_inner.sh", "frames_install.py", "host_identity.py",
         "venv_build.sh", "pins_cu129.txt", "provenance_bin/git", "site_alias/sitecustomize.py"]
files = {n: hashlib.sha256(open(os.path.join(C, n), "rb").read()).hexdigest() for n in names}
jobs = (json.dumps({"files": files}, indent=1, sort_keys=True) + "\n").encode()
closure = hashlib.sha256(jobs).hexdigest()
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w", format=tarfile.USTAR_FORMAT) as t:
    for n in ["JOBS.json"] + names:
        data = jobs if n == "JOBS.json" else open(os.path.join(C, n), "rb").read()
        info = tarfile.TarInfo(n); info.size = len(data); info.mtime = 1793059200
        info.mode = 0o555 if n.endswith((".sh", "git")) else 0o444
        t.addfile(info, io.BytesIO(data))
os.makedirs(P, exist_ok=True)
path = os.path.join(P, "closure_%s.tar" % closure[:12])
open(path, "wb").write(buf.getvalue())
json.dump({"closure_sha256": closure, "tar": path, "files": files}, open(os.path.join(P, "CLOSURE.json"), "w"), indent=1)
print(closure)
