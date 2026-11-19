"""Verbatim archive and batch helpers from build_r10.py."""
import ast,gzip,hashlib,io,json,tarfile
HEAD_OLD = "#!/bin/bash\nset -euo pipefail\nexec /usr/bin/python3 -I -s -B - <<'A'\n"
def read_tar(raw):
    t = tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz')
    out = [(m, t.extractfile(m).read()) for m in t.getmembers()]
    assert all(m.isfile() for m, _ in out)
    return out



def write_tar(items):
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode='wb', compresslevel=9, mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode='w', format=tarfile.GNU_FORMAT) as t:
            for m, data in items:
                info = tarfile.TarInfo(m.name)
                info.size = len(data); info.mode = m.mode; info.mtime = m.mtime
                info.uid = m.uid; info.gid = m.gid; info.uname = m.uname; info.gname = m.gname
                t.addfile(info, io.BytesIO(data))
    return buf.getvalue()



def replace_once(data, old, new, what):
    assert data.count(old) == 1, (what, data.count(old))
    return data.replace(old, new)



def bundle_of(batch):
    lines = [l for l in batch.decode().splitlines() if l.startswith('b=bytes.fromhex(')]
    assert len(lines) == 1
    return lines[0], bytes.fromhex(ast.literal_eval(ast.parse(lines[0]).body[0].value.args[0]))



def wrap_batch(text, tok):
    # ORCH ANSWER 0318Z item 2: node-local log, EXIT trap copies node line + exit code + last 60 lines to the package's a/x<job>;
    # USR1 (stop margin) is forwarded to the reader; a failed copy never changes the exit code. #SBATCH exclude: item 3.
    t = text.decode(); assert t.startswith(HEAD_OLD) and t.endswith('\nA\n') and t.count('\nA\n') == 1
    head = ("#!/bin/bash\n#SBATCH --exclude=orchard-community-2\nset -uo pipefail\n"
            "P=/project/community/jjyeung/okh7/a15_cot_ap" + tok + "\nL=/tmp/a${SLURM_JOB_ID:-0}.l\nR=$P/a/x${SLURM_JOB_ID:-0}\n"
            "fin(){ rc=$?; { head -n 1 \"$L\"; echo \"exit $rc\"; tail -n 60 \"$L\"; } > \"$R\" 2>/dev/null || true; exit $rc; }\n"
            "trap fin EXIT\n"
            "echo \"node $(hostname -s) tmp_free_kb $(df -Pk /tmp | awk 'NR==2{print $4}') gpus $(nvidia-smi -L 2>/dev/null | wc -l) cvd ${CUDA_VISIBLE_DEVICES:-none}\" > \"$L\" 2>/dev/null\n"
            "/usr/bin/python3 -I -s -B - >>\"$L\" 2>&1 <<'A' &\n")
    tail = "\nA\nPID=$!\ntrap 'kill -USR1 $PID 2>/dev/null' USR1\nwhile true; do wait $PID; rc=$?; kill -0 $PID 2>/dev/null || break; done\nexit $rc\n"
    return (head + t[len(HEAD_OLD):-len('\nA\n')] + tail).encode()



