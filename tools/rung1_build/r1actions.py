"""Write action files for tools/r1aws.py (rung1_build lane). Runs on trinity-0-13 with python3.12.

  r1actions.py upload FILE [TAG]            -> upload FILE to ap/59845bf9/x/<sha256><ext>        (prints the remote path)
  r1actions.py closure CLOSURE_TAR CLOSURE_SHA -> upload + install the job closure at ap/59845bf9/j/<sha[:12]>
  r1actions.py spec SPEC_JSON               -> upload the spec to ap/59845bf9/s/<sha256>.json    (prints the sha)
  r1actions.py sbatch CLOSURE_SHA SPEC_SHA CPUS MEM TIME [DEPENDENCY] -> one CPU job, name a15_cot_ap<spec sha[:8]>
  r1actions.py sbatchpre CLOSURE_SHA SPEC_SHA CPUS MEM TIME -> one CPU startup pre-stage job (spec phase "prestage")
  r1actions.py sbatchmn CLOSURE_SHA SPEC_SHA NODES TIME [DEPENDENCY|-]   -> one multi-node GPU job; DEPENDENCY
                                            "afterok-name:a15_cot_ap<8hex>" chains it (afterok) on a job queued by name
                                            (r1aws resolves the id when it submits; GPUs are requested only after it succeeds)
  r1actions.py sh NAME SCRIPT_FILE          -> a plain bash action
Action files go to actions/pending/ with names that keep upload -> install -> spec -> sbatch order within one poll.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

HOME = Path("/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/rung1_build_20261027")
PENDING = HOME / "actions/pending"
BASE = "/lustre/fsw/portfolios/av/users/jyeung/ap/59845bf9"
ACCOUNT = ["--account=av_alpamayo_aml", "--qos=av_alpamayo_aml_low"]


def sha(path):
    """Paced at 0.5 MB/s, so hashing a large local file never bursts (the IO meter counts local reads too)."""
    value, done, start = hashlib.sha256(), 0, time.time()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            value.update(block)
            done += len(block)
            ahead = done / 500_000 - (time.time() - start)
            if ahead > 0:
                time.sleep(ahead)
    return value.hexdigest()


def write(order, tag, action):
    name = "%s_%s_%s.json" % (order, time.strftime("%Y%m%dT%H%M%S"), tag)
    (PENDING / name).write_text(json.dumps(action, indent=1) + "\n")
    return name


def upload(path, tag="up", order="b", digest=None):
    digest = digest or sha(path)  # pass a known digest (PACKED.json, ARCHIVES.json) to skip re-reading the file
    suffix = "".join(Path(path).suffixes[-2:]) if path.endswith(".tar.gz") else Path(path).suffix
    dest = "%s/x/%s%s" % (BASE, digest, suffix)
    write(order, tag + "_" + digest[:8], {"kind": "upload", "src": str(Path(path).resolve()), "dest": dest, "sha256": digest})
    return dest


def refuse_per_row_copy(closure):
    """A GPU run may use only a closure whose finalize archives the run output: an older closure copies the staged
    frames to Lustre one file per row (about 290k files for a full arm) and exhausts the shared code-aws file quota."""
    import tarfile
    path = Path("/scratch/jjyeung/rung1_push/closure") / ("closure_%s.tar" % closure[:12])
    if not path.exists():
        raise SystemExit("REFUSED: no local closure tar to check for %s" % closure[:12])
    with tarfile.open(path) as tar:
        script = tar.extractfile("mn_train_inner.sh").read().decode()
    if 'cp -a "$RUN_OUTPUT"' in script or "train.tar" not in script:
        raise SystemExit("REFUSED: closure %s copies the run output file by file" % closure[:12])


def main(argv):
    kind = argv[0]
    if kind == "upload":
        print(upload(argv[1], argv[2] if len(argv) > 2 else "up", "z", argv[3] if len(argv) > 3 else None))
    elif kind == "closure":
        tar, closure = argv[1], argv[2]
        dest = upload(tar, "closure", "c")
        target = "%s/j/%s" % (BASE, closure[:12])
        script = (f"set -e\nT={target}\nif [ -e $T/JOBS.json ]; then echo CLOSURE_PRESENT; else\n"
                  f"mkdir -p $T.part && tar -C $T.part -xf {dest}\n"
                  f"test \"$(sha256sum < $T.part/JOBS.json | cut -d' ' -f1)\" = {closure}\n"
                  "cd $T.part && python3 -c 'import json,hashlib; m=json.load(open(\"JOBS.json\"))[\"files\"]; "
                  "bad=[f for f,h in m.items() if hashlib.sha256(open(f,\"rb\").read()).hexdigest()!=h]; assert not bad, bad'\n"
                  "chmod 0555 entry.sh prep_inner.sh mn_train_inner.sh venv_build.sh provenance_bin/git\n"
                  f"cd .. && mv -n $T.part $T && echo CLOSURE_INSTALLED {closure}; fi\nls -la $T")
        write("d", "install_" + closure[:8], {"kind": "sh", "script": script})
    elif kind == "spec":
        digest = sha(argv[1])
        write("e", "spec_" + digest[:8], {"kind": "upload", "src": str(Path(argv[1]).resolve()),
                                          "dest": "%s/s/%s.json" % (BASE, digest), "sha256": digest})
        print(digest)
    elif kind in ("sbatch", "sbatchpre"):
        closure, spec, cpus, mem, limit = argv[1:6]
        name = "a15_cot_ap" + spec[:8]
        entry = "%s/j/%s/entry.sh" % (BASE, closure[:12])
        args = ["sbatch", "--parsable", *ACCOUNT, "--partition=cpu,cpu-big", "--nodes=1", "--ntasks=1",
                "--cpus-per-task=%s" % cpus, "--mem=%s" % mem, "--time=%s" % limit, "--no-requeue", "--export=ALL",
                "--chdir=%s/l" % BASE, "--job-name=" + name, "--output=%s/l/%s_%%j.log" % (BASE, name)]
        if len(argv) > 6:
            args.append("--dependency=" + argv[6])
        args += [entry, closure, spec]
        pre = (f"test \"$(sha256sum < {BASE}/j/{closure[:12]}/JOBS.json | cut -d' ' -f1)\" = {closure} && "
               f"test \"$(sha256sum < {BASE}/s/{spec}.json | cut -d' ' -f1)\" = {spec}")
        phase, purpose = (("prestage", "CPU startup pre-stage (verify, frames, rows) before a chained GPU job")
                          if kind == "sbatchpre" else ("prep", "CPU preparation of rung-1 frozen sets"))
        write("f", "sbatch_" + spec[:8], {"kind": "sbatch", "name": name, "gpus": 0, "argv": args,
                                          "chdir": "%s/l" % BASE, "pre": pre,
                                          "run_spec": {"lane": "rung1_build_20261027", "phase": phase,
                                                       "closure": closure, "spec_sha256": spec,
                                                       "purpose": purpose}})
        print(name)
    elif kind == "sbatchmn":
        # Multi-node GPU job on pool0: one batch task per node; entry.sh launches one srun task per node with 8 GPUs.
        closure, spec, nodes, limit = argv[1:5]
        refuse_per_row_copy(closure)
        GPN = int(os.environ.get("R1_GPN", "8"))  # GPUs per node; a probe may ask for fewer
        name = "a15_cot_ap" + spec[:8]
        entry = "%s/j/%s/entry.sh" % (BASE, closure[:12])
        args = ["sbatch", "--parsable", *ACCOUNT, "--partition=pool0", "--nodes=%s" % nodes, "--ntasks=%s" % nodes,
                "--gres=gpu:%d" % GPN, "--cpus-per-task=%s" % os.environ.get("R1_CPUS", "64"),
                "--mem=%s" % os.environ.get("R1_MEM", "900G"), "--time=%s" % limit, "--no-requeue",
                "--export=ALL", "--chdir=%s/l" % BASE, "--job-name=" + name, "--output=%s/l/%s_%%j.log" % (BASE, name)]
        after = None
        if len(argv) > 5 and argv[5].startswith("afterok-name:"):
            after = argv[5].partition(":")[2]
            if not re.fullmatch(r"a15_cot_ap[0-9a-f]{8}", after):
                raise SystemExit("REFUSED: afterok-name needs an a15_cot_ap<8 hex> job name")
            # r1aws.py replaces the placeholder with the queued job's id. afterok: GPUs are requested only once the
            # cache is ready; a failed pre-stage cancels this job instead of letting it idle through a slow startup.
            args += ["--dependency=afterok:@JOBID@", "--kill-on-invalid-dep=yes"]
        elif len(argv) > 5 and argv[5] != "-":
            args.append("--dependency=" + argv[5])
        for flag, variable in (("--deadline", "R1_DEADLINE"), ("--time-min", "R1_TIME_MIN")):
            if os.environ.get(variable):  # a chained arm that cannot finish by the deadline is removed, never truncated
                args.append(f"{flag}={os.environ[variable]}")
        args += [entry, closure, spec]
        pre = (f"test \"$(sha256sum < {BASE}/j/{closure[:12]}/JOBS.json | cut -d' ' -f1)\" = {closure} && "
               f"test \"$(sha256sum < {BASE}/s/{spec}.json | cut -d' ' -f1)\" = {spec}")
        action = {"kind": "sbatch", "name": name, "gpus": GPN * int(nodes), "argv": args,
                  "chdir": "%s/l" % BASE, "pre": pre,
                  "run_spec": {"lane": "rung1_build_20261027", "phase": "mntrain",
                               "closure": closure, "spec_sha256": spec, "nodes": int(nodes),
                               "purpose": "multi-node startup and s/step test"}}
        if after:
            action["after_name"] = after
            action["run_spec"]["after"] = after
        write("g", "sbatchmn_" + spec[:8], action)
        print(name)
    elif kind == "sh":
        write("a", argv[1], {"kind": "sh", "script": Path(argv[2]).read_text()})
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
