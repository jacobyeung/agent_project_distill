#!/usr/bin/env python3
"""rung1_build batched code-aws driver (copy of awstrain_20261027 awstrain.py): ONE ssh call per poll (>= 150 s apart), stream throttled to 0.5 MB/s.

Each poll sends one stream to `bash -s` on the code-aws login node: a status block, then every queued action in
actions/pending (sorted by name), in order. Action kinds (JSON files):
  {"kind": "sh", "script": "..."}                                   plain bash, run with set +e, rc printed
  {"kind": "upload", "src": LOCAL, "dest": REMOTE, "sha256": HEX}   raw bytes appended to the stream (dd fullblock),
                                                                     sha-verified, published with mv -n (no clobber)
  {"kind": "sbatch", "name": "a15_cot_ap<8hex>", "gpus": N, "argv": [...], "pre": "bash checks", "run_spec": {...}}
       GPU requests are admitted only if, from a fresh squeue in the same call: no new URGENT heading in the peer inbox,
       project GPUs (a15_cot_c1022_* and a15_cot_<alnum>, running+pending) + N <= CODE_AWS_GPU_CAP, and this lane's
       GPUs + N <= min(DISTILL_GUARANTEE_GPUS, DISTILL_SHARE_GPUS). A ledger intent line precedes the call; the
       submitted / not_submitted / uncertain line follows it.
usage: awsl2.py run   |   awsl2.py status
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

LANES = Path("/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes")
HOME = LANES / "rung1_build_20261027"
PENDING, SENT, POLLS = HOME / "actions/pending", HOME / "actions/sent", HOME / "polls"
STAMP, STATE = HOME / "polls/LAST_POLL", HOME / "polls/STATE.json"
JOB_LEDGER = LANES / "aws_reserve/AWS_JOB_LEDGER.jsonl"
SUBMIT_LOCK = LANES / "aws_reserve/submit_r2.lock"  # shared with aws_lane2 so submissions serialize
# 2026-10-27: the main orchestrator relays distillation's share directly (cap scheduler v4 is down), so both the
# project-level and the lane-level checks read lane files this lane maintains from the relayed share.
CAP_FILE, GUARANTEE, SHARE = HOME / "SCHEDULE.json", HOME / "SCHEDULE.json", HOME / "SCHEDULE.json"  # GPU windows: SCHEDULE.json
LANE = "rung1_build_20261027"
# 2026-10-27: code-aws is reached through the reverse tunnel on trinity-0-13 (127.0.0.1:42224, ~/.ssh/config host
# code-aws, whose ControlMaster is reused). No hop through the Trinity head node. Run this driver only on trinity-0-13.
# The 900 s timeout is enforced in-process (paced_ssh kills the ssh), so a poll is this interpreter plus one ssh.
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=30", "code-aws", "bash -s"]
SSH_TIMEOUT = 900
ACK = POLLS / "URGENT_ACK"
MIN_INTERVAL = 150
BANNED = re.compile("sp" "lit", re.I)
# Every AWS-visible string of a job (sbatch argv, paths, log path, and the spec file the job reads its arguments from)
# must be opaque: none of these words, case-insensitive; the job's own name is the only place "cot_ap" may appear.
FORBIDDEN = re.compile("sp" "lit|distill|qgen|revsi|vsi|qwen|gemini|t3b|dc6dm|selfv|prmrl|smoke|cot_ap", re.I)
SPEC_DIRS = (HOME / "specs",)
# Spec files (read by the job, never by Slurm) must carry no "sp" "lit" (coordinator ruling 2026-10-27 01:40 PT);
# Slurm-visible text (name, argv, workdir, log path) must pass the full FORBIDDEN list.
SPEC_FORBIDDEN = BANNED


def sent_uploads():
    """sha256 -> local source of every upload this lane already delivered (archived in actions/sent)."""
    found = {}
    for path in sorted((HOME / "actions/sent").glob("*.json")):
        try:
            act = json.loads(path.read_text())
        except ValueError:
            continue
        if act.get("kind") == "upload" and Path(act.get("src", "")).is_file():
            found[act["sha256"]] = act["src"]
    return found


def opaque_violations(name, argv, uploads):
    """Forbidden words in the job's argv (its own name removed) or in any spec file the argv names by SHA-256.
    `uploads` maps sha256 -> local source of upload actions queued earlier; a named spec that cannot be read locally
    is itself a violation (fail closed)."""
    text = " ".join(argv).replace(name, "")
    hits = sorted({m.group(0).lower() for m in FORBIDDEN.finditer(text)})
    for digest in sorted(set(re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", " ".join(argv)))):
        if not any(digest + ".json" in arg for arg in argv) and not any(arg == digest for arg in argv):
            continue
        source = uploads.get(digest) or sent_uploads().get(digest)
        if source is None:
            source = next((d / (digest + ".json") for d in SPEC_DIRS if (d / (digest + ".json")).is_file()), None)
        if source is None:
            # A bare 64-hex argument may be a script or closure digest rather than a spec; only spec paths must resolve.
            if any(arg.endswith("/" + digest + ".json") for arg in argv):
                hits.append("unreadable_spec:" + digest[:12])
            continue
        content = Path(source).read_bytes()
        if hashlib.sha256(content).hexdigest() != digest:
            hits.append("spec_digest_mismatch:" + digest[:12])
            continue
        # A launcher may check its own job name; that pattern (and an exact a15_cot_ap<8 hex> name) is the job name.
        scanned = re.sub(r"a15_cot_ap(?:\[0-9a-f\]\{8\}|\$\{[^}]*\}|[0-9a-f]{8})", "", content.decode("utf-8", "replace"))
        hits.extend(sorted({"spec:" + m.group(0).lower() for m in SPEC_FORBIDDEN.finditer(scanned)}))
    return hits
SLURM = "/cm/shared/apps/slurm/current/bin"
CLEAN_ENV = ("env -i HOME=/home/jyeung USER=jyeung LOGNAME=jyeung TZ=America/Los_Angeles "
             f"SLURM_CONF=/cm/shared/apps/slurm/var/etc/aws-iad-cs-002/slurm.conf PATH={SLURM}:/usr/local/bin:/usr/bin:/bin")
INBOX = "/home/jyeung/peer_inbox/TO_AGENT_PROJECT.md"


def schedule():
    """(distillation total, this lane's share) in GPUs, running+pending, from the relayed windows (PT):
    SCHEDULE.json = [{"from": "2026-10-27T01:30", "total": 86, "lane": 8}, ...]; the last entry whose start has passed wins."""
    now = datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%dT%H:%M")
    rows = [r for r in json.loads((HOME / "SCHEDULE.json").read_text()) if r["from"] <= now]
    row = rows[-1] if rows else {"total": 0, "lane": 0}
    return int(row["total"]), int(row["lane"])


def first_int(path):
    return int(re.match(r"\s*([0-9]+)", Path(path).read_text()).group(1))


def now_pt():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ledger_append(value):
    with JOB_LEDGER.open("a") as stream:
        stream.write(json.dumps({"at_pt": now_pt(), "lane": LANE, **value}, sort_keys=True) + "\n")


def my_jobs():
    """name -> latest slurm id (or None) for every job this lane recorded."""
    jobs = {}
    for line in JOB_LEDGER.read_text().splitlines():
        if line.strip():
            entry = json.loads(line)
            if entry.get("lane") == LANE:
                jobs.setdefault(entry["opaque_name"], None)
                if entry.get("slurm_job_id"):
                    jobs[entry["opaque_name"]] = str(entry["slurm_job_id"])
    return jobs


def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"urgent_seen": [], "uncertain": [], "watch": []}


def status_block(state, jobs):
    ids = sorted({j for j in jobs.values() if j})
    watch = " ".join(shlex.quote(w) for w in state.get("watch", []))
    names = " ".join(sorted(jobs))
    return f"""export TZ=America/Los_Angeles PATH={SLURM}:$PATH
echo "=== STATUS BEGIN $(date '+%F %T %Z')"
urgent_latched=0
{remote_python(URGENT_CODE, [INBOX, json.dumps(ACK.read_text().splitlines() if ACK.exists() else []), json.dumps(state.get('urgent_seen', [])), "guard"])}urgent_status=$?
if [ "$urgent_status" != 0 ]; then urgent_latched=1; fi
echo "=== INBOX_HEADS"; grep -n '^## ' {INBOX} | tail -n 4
echo "=== SQUEUE"; squeue -h -r -u jyeung --states=R,PD,CF,CG,S,RS -o '%i|%j|%T|%b|%D|%P|%M|%L|%R' 2>&1
echo "=== SACCT"; {f"sacct -n -X -P -j {','.join(ids)} -o JobID,JobName,State,Elapsed,ExitCode,Start,End 2>&1" if ids else "true"}
echo "=== LOGS"; for n in {names or 'none'}; do for f in $(ls -t /lustre/fsw/portfolios/av/users/jyeung/ap/*/l/${{n}}_*.log 2>/dev/null | head -n 1); do echo "--- $f"; tail -n 6 "$f" | cut -c1-300; done; done
echo "=== WATCH"; for w in {watch or 'none'}; do bash -c "$w" 2>&1 | tail -n 40 | cut -c1-400; done
echo "=== STATUS END"
"""


# These programs run on the login node inside the single poll stream.
URGENT_CODE = r"""
import json, re, sys
from pathlib import Path
inbox, acknowledged, seen, mode = sys.argv[1:]
try:
    heads = [line for line in Path(inbox).read_text().splitlines()
             if re.match(r'^#{1,6}\s', line) and 'URGENT' in line]
except OSError:
    print('URGENT_UNREADABLE')
    sys.exit(1)
for heading in heads:
    print('URGENT_HEADING ' + json.dumps(heading))
blocked = (set(heads) | set(json.loads(seen))) - set(json.loads(acknowledged))
for heading in sorted(blocked):
    print('URGENT_UNACKNOWLEDGED ' + json.dumps(heading))
if mode != 'status' and blocked:
    sys.exit(1)
"""

CAPACITY_CODE = r"""
import json, re, subprocess, sys
name, need, cap, share, names = sys.argv[1:]
need, cap, share, names = int(need), int(cap), int(share), set(json.loads(names))

def command(argv):
    return subprocess.run(argv, text=True, capture_output=True, check=True).stdout

def tres_total(tres):
    entries = [item.split('=', 1) for item in tres.split(',') if 'gpu' in item.lower()]
    if any(len(item) != 2 or not item[1].isdigit() for item in entries):
        raise ValueError('unreadable TRES')
    if len({item[0] for item in entries}) != len(entries):
        raise ValueError('duplicate GPU TRES')
    total = [int(v) for k, v in entries if k == 'gres/gpu']
    typed = [int(v) for k, v in entries if k.startswith('gres/gpu:')]
    if any(k != 'gres/gpu' and not k.startswith('gres/gpu:') for k, v in entries):
        raise ValueError('ambiguous GPU TRES')
    if not total or total[0] <= 0:
        raise ValueError('missing positive GPU TRES total')
    if typed and total[0] != sum(typed):
        raise ValueError('GPU TRES disagree')
    return total[0]

def requested(id):
    # Exact task ID is essential: an array parent can have different requests.
    output = command(['scontrol', 'show', 'job', '-o', id])
    lines = [line for line in output.splitlines() if line.strip()]
    if len(lines) != 1:
        raise ValueError('missing or ambiguous job')
    fields = dict(token.split('=', 1) for token in lines[0].split() if '=' in token)
    if fields.get('JobId') != id and (fields.get('ArrayJobId', '') + '_' + fields.get('ArrayTaskId', '')) != id:
        raise ValueError('job ID differs')
    tres = fields.get('ReqTRES', fields.get('TRES', ''))
    return tres_total(tres)

project = lane = 0
try:
    snapshot = command(['squeue', '-h', '-r', '-u', 'jyeung', '--states=R,PD,CF,CG,S,RS',
                        '--Format=JobID:40,Name:128,State:20,tres-per-node:256,NumNodes:20,Partition:128,tres-alloc:256'])
    ids = set()
    for line in snapshot.splitlines():
        if not line.strip():
            continue
        id, job, state, gres, nodes, partition, tres = line.split()
        if not re.fullmatch(r'[0-9]+(?:_[0-9]+)?(?:[+][0-9]+)?', id) or id in ids:
            raise ValueError('ambiguous queue ID')
        ids.add(id)
        gpu_partition = bool(re.search('pool0|backfill|batch|gpu', partition, re.I))
        gpu_evidence = gpu_partition or 'gpu' in (gres + tres).lower()
        # Parenthesized topology may contain commas; remove it before parsing entries.
        entries = re.sub(r'\([^)]*\)', '', gres).split(',')
        gpu_entries = [entry for entry in entries if 'gpu' in entry.lower()]
        matches = [re.fullmatch(r'gpu(?::[A-Za-z0-9_-]+)?:([0-9]+)', entry) for entry in gpu_entries]
        readable = (gpu_entries and all(matches) and nodes.isdigit() and int(nodes) > 0)
        g = sum(int(match[1]) for match in matches) * int(nodes) if readable else 0
        if gpu_evidence:
            if state in ('PENDING', 'PD') or not readable:
                g = max(g, requested(id))
            if 'gpu' in tres.lower():
                g = max(g, tres_total(tres))
        if re.fullmatch(r'a15_cot_ap[0-9a-f]{8}', job):
            project += g  # every distillation job (all lanes): checked against the relayed distillation total
        if job in names:
            lane += g
except (OSError, ValueError, subprocess.SubprocessError) as error:
    print(f'NOT_SUBMITTED {name} capacity_lookup_failed {error}')
    sys.exit(1)
print(f'CAPACITY {name} project={project} lane={lane} need={need} cap={cap} share={share} bad=0')
if project + need > cap or lane + need > share:
    print(f'NOT_SUBMITTED {name} capacity')
    sys.exit(1)
"""

RECONCILE_CODE = r"""
import re, subprocess, sys
name, uncertain = sys.argv[1:]
try:
    queue = subprocess.run(['squeue', '-h', '-r', '-u', 'jyeung', '-n', name, '-o', '%i|%j'],
                           capture_output=True, text=True, check=True).stdout
    rows = [line.strip().split('|') for line in queue.splitlines() if line.strip()]
    if uncertain == '1':
        account = subprocess.run(['sacct', '-n', '-X', '-P', '-u', 'jyeung', '--name', name,
                                  '-S', '2026-10-25', '-o', 'JobIDRaw,JobName%100'],
                                 capture_output=True, text=True, check=True).stdout
        rows += [line.strip().split('|')[:2] for line in account.splitlines() if line.strip()]
    if any(len(row) != 2 or row[1] != name or not re.fullmatch(r'[0-9]+(?:_[0-9]+)?', row[0]) for row in rows):
        raise ValueError('ambiguous reconciliation')
    ids = {row[0] for row in rows}
    if len(ids) > 1:
        raise ValueError('multiple matching jobs')
    if ids:
        print('RECONCILED ' + name + ' ' + next(iter(ids)))
        sys.exit(10)
    if uncertain == '1':
        raise ValueError('uncertain submission absent from queue and accounting; retain for reconciliation')
except (OSError, ValueError, subprocess.SubprocessError) as error:
    print('RECONCILE_BLOCKED ' + name + ' ' + str(error))
    sys.exit(1)
"""


def remote_python(code, args):
    return "python3 - " + shlex.join(args) + " <<'AWSL2_PY'\n" + code + "\nAWSL2_PY\n"


def capacity_guard(name, gpus, mine, state=None):
    state = state or {}
    acknowledged = ACK.read_text().splitlines() if ACK.exists() else []
    urgent = remote_python(URGENT_CODE, [INBOX, json.dumps(acknowledged),
                                        json.dumps(state.get('urgent_seen', [])), 'guard'])
    total, share = schedule()
    capacity = remote_python(CAPACITY_CODE, [name, str(gpus), str(total), str(share),
                            json.dumps(sorted(set(mine) | {name}))])
    return (f'guard_ok=0\nif {urgent}then\nif [ "${{urgent_latched:-0}}" = 0 ]; then\n'
            f'if {capacity}then guard_ok=1; fi\n'
            f'else echo "NOT_SUBMITTED {name} urgent_unacknowledged"; fi\n'
            f'else urgent_latched=1; echo "NOT_SUBMITTED {name} urgent_unacknowledged"; fi\n')


def argv_gpus(argv):
    """Require each GPU request form to describe the same positive total."""
    values = {}
    aliases = {'-N': '--nodes', '-n': '--ntasks'}
    supported = {'--gres', '--gpus', '--gpus-per-node', '--gpus-per-task', '--nodes', '--ntasks'}
    args = iter(argv[1:])
    for arg in args:
        flag, sep, value = arg.partition('=')
        if arg[:2] in aliases:
            flag, value = aliases[arg[:2]], arg[2:]
            sep = bool(value)
        if flag in supported:
            if not sep:
                value = next(args, '')
            if flag in values:
                raise ValueError('duplicate resource flag ' + flag)
            values[flag] = value
        elif flag.startswith(('--gpu', '--gre', '--tres', '--node', '--ntask', '-G')):
            raise ValueError('unsupported resource flag ' + flag)

    def positive(value):
        if not re.fullmatch(r'[0-9]+', value) or int(value) <= 0:
            raise ValueError('resource counts must be exact positive integers')
        return int(value)

    nodes = positive(values.get('--nodes', '1'))
    tasks = positive(values.get('--ntasks', str(nodes)))
    totals = []
    if '--gres' in values and 'gpu' in values['--gres'].lower():
        entries = [entry for entry in values['--gres'].split(',') if 'gpu' in entry.lower()]
        matches = [re.fullmatch(r'gpu(?::[A-Za-z0-9_-]+)?:([0-9]+)', entry) for entry in entries]
        if not all(matches):
            raise ValueError('unsupported GPU GRES')
        totals.append(sum(positive(match[1]) for match in matches) * nodes)
    for flag, multiplier in (('--gpus', 1), ('--gpus-per-node', nodes), ('--gpus-per-task', tasks)):
        if flag in values:
            totals.append(positive(values[flag]) * multiplier)
    if len(set(totals)) > 1:
        raise ValueError('GPU request flags disagree')
    return totals[0] if totals else 0


def build(actions, state, jobs):
    """Returns (stream bytes, plan list)."""
    parts, plan = [status_block(state, jobs).encode()], []
    planned_names = set(jobs)
    uploads = {}
    for path in actions:
        act = json.loads(path.read_text())
        aid = path.stem
        kind = act["kind"]
        if kind == "sh":
            text = act["script"]
            if BANNED.search(text) and not act.get("allow_glob_note"):
                raise SystemExit(f"REFUSED: action {aid} carries the banned word")
            parts.append(f"echo '=== ACTION {aid} BEGIN'\n( set +e\n{text}\n)\necho \"=== ACTION {aid} END rc=$?\"\n".encode())
        elif kind == "upload":
            src, dest, want = Path(act["src"]), act["dest"], act["sha256"]
            assert not BANNED.search(dest), dest
            data_len = src.stat().st_size
            data = FileRef(src, data_len)  # streamed in paced chunks; the remote side verifies the sha256
            uploads[want] = src
            parts.append((f"echo '=== ACTION {aid} BEGIN'\nmkdir -p {shlex.quote(os.path.dirname(dest))}\n"
                          f"dd of={shlex.quote(dest)}.part.$$ bs={max(1, data_len)} count={int(bool(data_len))} iflag=fullblock status=none || exit 97\n").encode())
            parts.append(data)
            parts.append((f"got=$(sha256sum < {shlex.quote(dest)}.part.$$ | cut -d' ' -f1)\n"
                          f"if [ \"$got\" = {want} ]; then mv -n {shlex.quote(dest)}.part.$$ {shlex.quote(dest)}; fi\n"
                          f"fin=$(sha256sum < {shlex.quote(dest)} 2>/dev/null | cut -d' ' -f1)\n"
                          f"if [ \"$got\" = {want} ] && [ \"$fin\" = {want} ]; then echo \"UPLOADED {aid} $fin\"; rc=0; "
                          f"else echo \"UPLOAD_FAILED {aid} got=$got dest=$fin\"; rc=1; fi\n"
                          f"echo \"=== ACTION {aid} END rc=$rc\"\n").encode())
        elif kind == "sbatch":
            name, gpus = act["name"], int(act["gpus"])
            assert re.fullmatch(r"a15_cot_ap[0-9a-f]{8}", name), name
            argv = act["argv"]
            try:
                if gpus < 0 or argv_gpus(argv) != gpus:
                    raise ValueError('argv GPU request differs from declared gpus')
            except ValueError as error:
                raise SystemExit(f"REFUSED: {name}: {error}") from error
            hits = opaque_violations(name, argv, uploads)
            if hits:
                raise SystemExit(f"REFUSED: AWS-visible text of {name} is not opaque: {', '.join(hits)}")
            pre = act.get("pre", "true")
            planned_names.add(name)
            guard = capacity_guard(name, gpus, planned_names, state) if gpus else "guard_ok=1\n"
            reconcile = remote_python(RECONCILE_CODE, [name, str(int(name in state.get('uncertain', []) or bool(jobs.get(name))))])
            parts.append((f"echo '=== ACTION {aid} BEGIN'\nrc=1\n{reconcile}reconciled=$?\n"
                          f"if [ \"$reconciled\" = 10 ]; then rc=0;\n"
                          f"elif [ \"$reconciled\" = 0 ]; then\n{guard}"
                          f"if [ \"$guard_ok\" = 1 ]; then\n"
                          f"  if ! ( {pre} ); then echo 'NOT_SUBMITTED {name} precheck_failed';\n"
                          f"  else r=$(cd {shlex.quote(act['chdir'])} && {CLEAN_ENV} {shlex.join(argv)} 2>&1); sr=$?; "
                          f"echo \"SBATCH_REPLY {name} $r\"; "
                          f"if [ \"$sr\" = 0 ] && [[ \"$r\" =~ ^[0-9]+(\\;[^[:space:]]+)?$ ]]; then rc=0; fi; fi\n"
                          f"fi\nfi\necho \"=== ACTION {aid} END rc=$rc\"\n").encode())
            act["_aid"] = aid
            plan.append(act)
        else:
            raise SystemExit(f"unknown action kind {kind}")
    parts.append(b"echo '=== POLL END'\n")
    return parts, plan


RATE = 500_000  # bytes per second through the tunnel


class FileRef:
    def __init__(self, path, size):
        self.path, self.size = Path(path), size


GOVERNOR = Path("/data3/jjyeung/orch_n13_20261026/io_governor/streams")
REGISTER = "/scratch/jjyeung/io_governor_n13/register.py"


ADMISSION_WAIT = 2400  # seconds a registered payload poll waits for the governor before giving up (nothing sent)
STREAM_TIMEOUT = 5400  # seconds for an admitted payload poll, governor pauses included


def governed_ssh(parts, stamp, payload):
    import threading
    work = Path("/scratch/jjyeung/rung1_push/stream") / stamp
    work.mkdir(parents=True, exist_ok=True)
    files = []
    for number, part in enumerate(parts):
        if isinstance(part, FileRef):
            files.append(str(part.path))
        else:
            path = work / f"part_{number:04d}.txt"
            path.write_bytes(part)
            files.append(str(path))
    manifest = work / "MANIFEST.json"
    manifest.write_text(json.dumps(files))
    total = sum(Path(f).stat().st_size for f in files)
    reader = subprocess.Popen([sys.executable, "-B", str(Path(__file__).with_name("r1stream.py")), str(manifest),
                               str(work / "reader.pid")], stdout=subprocess.PIPE)
    pv = subprocess.Popen(["pv", "-q", "-L", "500k", "-B", "65536"], stdin=reader.stdout, stdout=subprocess.PIPE)
    reader.stdout.close()
    proc = subprocess.Popen(SSH, stdin=pv.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pv.stdout.close()
    chunks = {"out": [], "err": []}

    def drain(stream, key):
        for block in iter(lambda: stream.read(65536), b""):
            chunks[key].append(block)

    threads = [threading.Thread(target=drain, args=(proc.stdout, "out"), daemon=True),
               threading.Thread(target=drain, args=(proc.stderr, "err"), daemon=True)]
    for thread in threads:
        thread.start()
    for _ in range(120):
        if (work / "reader.pid").exists() and "T" in Path(f"/proc/{reader.pid}/stat").read_text().rsplit(")", 1)[1].split()[0]:
            break
        time.sleep(0.5)
    record = GOVERNOR / (LANE + ".json")
    if record.exists():
        record.rename(record.with_name(f"{LANE}.done.{int(time.time())}"))
    subprocess.run(["/usr/bin/python3", REGISTER, "--lane", LANE, "--pid", str(reader.pid), "--member-pid", str(pv.pid),
                    "--pv-pid", str(pv.pid), "--expected-bytes", str(total), "--tier", "1", "--kind", "push",
                    "--nominal-mbps", "1.0", "--tunnel-mbps", "0.5", "--io-weight", "1", "--tunnel-weight", "1",
                    "--allow-resume"], check=True)
    # Rung-1 copies are on the critical path: admission priority 10 within the tier (coordinator). The helper has no
    # flag for it, so the field is added to the published record by an atomic same-directory rewrite.
    value = json.loads(record.read_text())
    value["priority"] = 10
    staged = record.with_name(f".{record.name}.{os.getpid()}.tmp")
    staged.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(staged, record)
    start = time.time()
    admitted = False
    while time.time() - start < ADMISSION_WAIT:
        state = Path(f"/proc/{reader.pid}/stat").read_text().rsplit(")", 1)[1].split()[0] if reader.poll() is None else "X"
        if state not in ("T", "t"):
            admitted = True
            break
        time.sleep(5)
    if not admitted:
        print(f"NOT_ADMITTED after {ADMISSION_WAIT} s; nothing was sent; actions stay pending")
        for p in (proc, pv, reader):
            p.kill()
        reader.wait(); pv.wait(); proc.wait()
        governor_complete()
        return subprocess.CompletedProcess(SSH, 99, b"", b"governor did not admit the payload poll")
    killer = threading.Timer(STREAM_TIMEOUT, lambda: [p.kill() for p in (proc, pv, reader)])
    killer.daemon = True
    killer.start()
    reader.wait()
    pv.wait()
    code = proc.wait()
    killer.cancel()
    for thread in threads:
        thread.join(timeout=30)
    governor_complete()
    return subprocess.CompletedProcess(SSH, code, b"".join(chunks["out"]), b"".join(chunks["err"]))


def governor_register():
    """Stop this process, have a helper register it with the central IO governor (tier 1 push), then resume."""
    import signal
    record = GOVERNOR / (LANE + ".json")
    if record.exists():
        record.rename(record.with_name(f"{LANE}.done.{int(time.time())}"))
    pid = os.getpid()
    helper = subprocess.Popen(["/bin/bash", "-c",
        f"for i in $(seq 1 120); do grep -q '^State:.*T' /proc/{pid}/status && break; sleep 0.5; done; "
        f"/usr/bin/python3 {REGISTER} --lane {LANE} --pid {pid} --tier 1 --kind push --nominal-mbps 1.0 "
        f"--tunnel-mbps 0.5 --allow-resume; kill -CONT {pid}"])
    os.kill(pid, signal.SIGSTOP)
    helper.wait()
    assert record.exists(), "governor registration missing"


def governor_complete():
    record = GOVERNOR / (LANE + ".json")
    if record.exists():
        record.rename(record.with_name(f"{LANE}.done.{int(time.time())}"))


def paced_ssh(parts, rate):
    import threading
    proc = subprocess.Popen(SSH, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    chunks = {"out": [], "err": []}

    def drain(stream, key):
        for block in iter(lambda: stream.read(65536), b""):
            chunks[key].append(block)

    threads = [threading.Thread(target=drain, args=(proc.stdout, "out"), daemon=True),
               threading.Thread(target=drain, args=(proc.stderr, "err"), daemon=True)]
    for thread in threads:
        thread.start()
    killer = threading.Timer(SSH_TIMEOUT, proc.kill)
    killer.daemon = True
    killer.start()
    start, sent = time.time(), 0
    def blocks():
        for part in parts:
            if isinstance(part, FileRef):
                with part.path.open("rb") as source:
                    yield from iter(lambda: source.read(65536), b"")
            else:
                yield part

    try:
        for block in blocks():
            proc.stdin.write(block)
            sent += len(block)
            ahead = sent / rate - (time.time() - start)
            if ahead > 0:
                time.sleep(ahead)
        proc.stdin.close()
    except BrokenPipeError:
        pass
    code = proc.wait()
    killer.cancel()
    for thread in threads:
        thread.join(timeout=30)
    return subprocess.CompletedProcess(SSH, code, b"".join(chunks["out"]), b"".join(chunks["err"]))


def failed_sbatch_reply(out, name):
    reply = re.search(rf'^SBATCH_REPLY {re.escape(name)} (.*?)(?=^=== |^SBATCH_REPLY |^RECONCILED |\Z)',
                      out, re.M | re.S)
    if not reply:
        return None
    text = reply[1].strip()
    if re.search(r'^(?:[0-9]+(?:;\S+)?|Submitted batch job [0-9]+)\s*$', text, re.M):
        return None
    return text if re.search(r'\bsbatch:\s*error:', text, re.I) else None


def archive_successes(actions, out, stamp):
    for path in actions:
        act = json.loads(path.read_text())
        if act['kind'] == 'sbatch' and failed_sbatch_reply(out, act['name']):
            SENT.mkdir(parents=True, exist_ok=True)
            path.rename(SENT / f"{stamp}_failed_{path.name}")
            continue
        aid = re.escape(path.stem)
        block = re.search(rf"^=== ACTION {aid} BEGIN\n(.*?)^=== ACTION {aid} END rc=0$", out, re.M | re.S)
        if not block or re.search(r'^=== ACTION .* END', block[1], re.M):
            continue
        if act['kind'] == 'upload' and not re.search(rf'^UPLOADED {aid} {act["sha256"]}$', block[1], re.M):
            continue
        SENT.mkdir(parents=True, exist_ok=True)
        path.rename(SENT / f"{stamp}_{path.name}")


def save_state(state):
    temp = STATE.with_suffix('.tmp')
    temp.write_text(json.dumps(state, indent=1) + "\n")
    temp.replace(STATE)


def update_urgent(state, out):
    seen = set(state.get('urgent_seen', []))
    for heading in re.findall(r'^URGENT_HEADING (.+)$', out, re.M):
        seen.add(json.loads(heading))
    state['urgent_seen'] = sorted(seen)
    acknowledged = set(ACK.read_text().splitlines()) if ACK.exists() else set()
    state['urgent_unacknowledged'] = sorted(seen - acknowledged)
    for heading in state['urgent_unacknowledged']:
        print('!!! UNACKNOWLEDGED URGENT: ' + heading)


def run():
    POLLS.mkdir(parents=True, exist_ok=True)
    with open(HOME / "polls/poll.lock", "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        last = float(STAMP.read_text()) if STAMP.exists() else 0
        if time.time() - last < MIN_INTERVAL:
            print(f"WAIT {int(MIN_INTERVAL - (time.time() - last))} s until the next poll")
            return 3
        state, jobs = load_state(), my_jobs()
        # Name order is execution order; bulk uploads are queued with a z_ prefix so they run last.
        actions = sorted(PENDING.glob("*.json"))
        with open(SUBMIT_LOCK, "r+") as slock:
            fcntl.flock(slock, fcntl.LOCK_EX)
            stream, plan = build(actions, state, jobs)
            # Persist intent before the call so a process crash cannot permit blind retry.
            state['uncertain'] = sorted(set(state.get('uncertain', [])) | {act['name'] for act in plan})
            save_state(state)
            for act in plan:
                ledger_append({"event": "intent", "opaque_name": act["name"], "gpus": int(act["gpus"]),
                               "run_spec": act.get("run_spec"), "slurm_job_id": None})
            STAMP.write_text(str(time.time()))
            stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
            t0 = time.time()
            try:
                payload = sum(part.size for part in stream if isinstance(part, FileRef))
                if payload > 1_000_000:
                    # Payload polls: gated reader | pv | ssh, registered with the IO governor, which admits and paces it.
                    result = governed_ssh(stream, stamp, payload)
                else:
                    # Control-only polls (status, sh, sbatch; a few kB) are not data streams.
                    result = paced_ssh(stream, RATE)
            except (OSError, subprocess.TimeoutExpired) as error:
                result = subprocess.CompletedProcess(SSH, 98, getattr(error, 'stdout', None) or b'',
                                                     str(error).encode())
            out = result.stdout.decode(errors="replace")
            (POLLS / f"poll_{stamp}.txt").write_text(out + "\n=== STDERR\n" + result.stderr.decode(errors="replace")
                                                    + f"\n=== RC {result.returncode} seconds {time.time() - t0:.1f}\n")
            for act in plan:
                name = act["name"]
                m = re.search(rf"^(?:SBATCH_REPLY|RECONCILED) {name} ([0-9]+)(?:;\S+)?\s*$", out, re.M)
                n = re.search(rf"^NOT_SUBMITTED {name} (.*)$", out, re.M)
                failure = failed_sbatch_reply(out, name) if not m else None
                if m:
                    ledger_append({"event": "submitted", "opaque_name": name, "gpus": int(act["gpus"]),
                                   "run_spec": act.get("run_spec"), "slurm_job_id": m.group(1)})
                elif n or failure:
                    state['uncertain'] = [job for job in state['uncertain'] if job != name]
                    ledger_append({"event": "not_submitted", "opaque_name": name,
                                   "reason": failure or n.group(1), "slurm_job_id": None})
                elif f"=== ACTION {act['_aid']} BEGIN" not in out:
                    # The remote shell never reached this action, so its sbatch cannot have run.
                    state['uncertain'] = [job for job in state['uncertain'] if job != name]
                    ledger_append({"event": "not_submitted", "opaque_name": name, "slurm_job_id": None,
                                   "reason": f"not reached before the poll ended (rc={result.returncode}); retried next poll"})
                else:
                    ledger_append({"event": "uncertain", "opaque_name": name, "slurm_job_id": None,
                                   "reason": f"rc={result.returncode}; check squeue by name in the next poll"})
        complete = "=== POLL END" in out
        update_urgent(state, out)
        archive_successes(actions, out, stamp)
        # Retain names with known IDs too: any leftover action must reconcile before retry.
        pending_names = {json.loads(path.read_text()).get('name') for path in PENDING.glob('*.json')}
        state['uncertain'] = [name for name in state['uncertain'] if name in pending_names]
        save_state(state)
        print(f"poll {stamp} rc={result.returncode} complete={complete} seconds={time.time() - t0:.1f} "
              f"actions={len(actions)} -> {POLLS / f'poll_{stamp}.txt'}")
        return 0 if complete else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        if len(sys.argv) != 2:
            raise SystemExit("usage: awsl2.py run (no options)")
        sys.exit(run())
    print(__doc__)
