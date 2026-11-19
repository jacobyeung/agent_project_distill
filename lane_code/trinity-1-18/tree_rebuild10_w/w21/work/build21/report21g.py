from pathlib import Path
import datetime,json
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21g'
def read(p):return json.loads(p.read_text())
print(datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
d=read(D/'DELIVERY.json');tests=read(D/'TESTS.json');scan=read(D/'SCAN.json');cov=read(D/'COVERAGE.json')
upload=read(D/'UPLOAD_DIFF.json');mount=read(D/'MOUNTS.json');look=read(D/'LOOKAHEAD.json')
summary='; '.join(f'{x["name"]}: {x["tests"]}' for x in tests)
report=f'''NO-GO: the kit mount fix and CPU checks pass; production GPU/model/store proof remains unrun. GO=false.

The kit gives `/tmp` a private writable parent, restores Q_ROOT at its original path, then applies the remaining binds.
Only `kit.py` and generated `kits/q/k/j.json` change runtime behavior. P's wrapper, joblib and the sealed tree are unchanged (`INTEGRITY.json`).
The scanner accepts the whole unmodified `os.environ` spread/copy and checks added keys/values; computed keys refuse.
The five runtime Python path names are Q_ROOT, Q_KIT, Q_NS, TK_KIT_HOME and TK_JOBDIR (`environment21f.py`).
Complex shell requires exact reviewed source bytes plus explicit literal-name runtime allowlists (`environment_shell21g.json`); edits invalidate that proof.
The fixed literal withheld-module import is recognized; dynamic imports remain refused. Provenance exceptions are unchanged.
Paths below are relative to `work/build21g/` unless stated otherwise.

Destinations and ordered availability (`MOUNTS.json`; source: P tk_bwrap and the decoded q shell):
N=`${{SLURM_TMPDIR:-/tmp}}/q_22c714e1_${{SLURM_JOB_ID}}`; AS=`/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung`.
AL is AS with `/scratch` replaced by `/lustre`; X=`AS/ap/8865619b`; P=`/project/community/jjyeung/c7d31ddd`.

| Destination | Mode-q value / source | Availability before mount |
|---|---|---|
| Every host top-level entry except home/dev/proc | Same host path or symlink target; exact Trinity list in MOUNTS.json | Exists by P's glob guard; initially read-only |
| /tmp overlay | `/tmp`, private tmpfs | Existing top-level target; now writable |
| Q_ROOT | N, bound from N | Host created during bootstrap; restored before child binds |
| /dev, /proc | `/dev` dev-bind; `/proc` procfs | Creatable under namespace root |
| /home | `/home`, tmpfs, finally remounted read-only | Creatable under namespace root |
| home user | `/home/jjyeung`, --dir | Creatable under /home tmpfs |
| AS, AL | AS and AL, both from `N/s/aws/u` | Read-only host ancestors; production targets already existed, inferred from job 173051 reaching the last bind |
| X | X, from `N/x` | Earlier AS is read-only; tk_stage creates source `U/ap/8865619b` before the view |
| runs | `X/runs`, from `N/rp` | Earlier X is writable; tk_nx also creates it |
| u | `X/u`, from `N/s/aws/u/ap/8865619b/u` | Earlier X is writable; source and target staged |
| data root | `X/data2root`, from `N/s/c7d31ddd/data2root` | Earlier X is writable; source and target staged |
| models | `X/models`, from `N/s/c7d31ddd/runs/aws128p_20261025/models` | Earlier X is writable; source and target staged |
| P | P, from `N/s/c7d31ddd` | Read-only host ancestor; production target already existed by the same ordered-failure inference |
| EPOCHS | `/home/jjyeung/6d00e578`, from `N/s/epochs` | Creatable under /home tmpfs before remount-ro |
| TK_JOBDIR | `N/j`, from `N/j` | Host created by staging; restored Q_ROOT is writable |
| Q_NS | `/tmp/q_22c714e1`, from N | Missing under read-only /tmp fails; private tmpfs makes it creatable |

No pool mount point is created. No Orchard host was inspected; AS/AL/P existence is inferred from the supplied launch failure.
The full-view fixture prefixes only AS/AL/P destinations under L; /tmp, /home, UID/GID and ordered mount operations stay faithful (`VIEW.json`).
Both the reduced command and generated tk_bwrap reproduce `Can't mkdir /tmp/q_22c714e1: Read-only file system`; fixed views run `true` successfully (`MOUNT_REDUCTION.json`, `VIEW.json`).
Marker checks also pass with default `/tmp` job-directory destinations (`TMP_VIEW.json`).

Look-ahead: every production stage below remains unproved after the Orchard launch failure (`LOOKAHEAD.json`).

| Stage | What CPU checks establish / remaining limit |
|---|---|
| bwrap binds | Exact generated view passes with local stand-ins; production host/GPU paths remain unchecked |
| GPU guard | Real b/g.py refuses E42 on CPU; no CUDA/80-GiB claim |
| q entry and extraction | Real b/a.py verifies kit and extracts sealed source; production venv compatibility remains unchecked |
| Staging/config/card/room audit | Pinned synthetic fixture passes these checks, then the unchanged Trinity frame-host guard refuses |
| Persisted receipt/component evidence | Focused/resolver readers retain identity and default-deny checks; DEFERRED evidence remains required |
| Opener witness/target binding | Focused tests retain step-544 and keep/reset contracts; production witness remains unrun |
| Native build/compose/prepare | CPU fixture tests cover producer/reader contracts; production RGB, labels and joins remain unchecked |
| Population binding/production audit | Focused tests cover fixture invariants; no production capacity/population claim |
| Final handover/admission | CPU readers check manifests and proof-only export restrictions; production prepared-store binding remains unrun |
| Staged base model and export load | Kit/resolver tests check archive/layout authentication; no 9B weights, production tokenizer or memory-fit check |
| Every rank's first batch | Fixture contracts only; production rank/stream forwards, finite losses and GPU memory remain unchecked |
| Room count | Exact b/d.py counts two synthetic rows with real room authority; no production census claim |
| Result archive | Naming controls retain opaque outputs and GO=false; no pool write/upload |

The production sequence reaches the GPU guard. The additional CPU q diagnostic reaches `R1_PROOF_FRAME_HOST_REQUIRED` after room certification (`NATIVE_VIEW.json`).
The empty-request diagnostic refuses `R1_PROOF_STAGED_PINS_REQUIRED`; the separate room entry passes (`VIEW.json`, `ROOM_VIEW.json`).
These are expected boundary refusals. No additional kit defect or required tree change was found.

Tests: {sum(x['tests'] for x in tests)} methods, zero failures/errors (`TESTS.json`): {summary}.
All six 21f mutations, including the reviewer tuple, refuse; the added non-literal key after a spread also refuses (`regression21f/MUTATIONS.json`, `INHERITANCE_CONTROLS.json`).
The controlled old scanner accepts those mutations; the final scanner refuses them. Added inheritance/alias/scope/shell-integrity controls also pass.
Decoded scan: {scan['status']}, {scan['checked_strings']} checked strings (`SCAN.json`).
Changed-statement coverage: {cov['environment21f.py']['changed_covered']}/{cov['environment21f.py']['changed_statements']} in environment21f.py (`COVERAGE.json`); missing statements are listed.
The exact generator insertion is traced against baseline bytes and emits the tested shell byte-for-byte (`TRACE_generator.json`).

Tree seal: `{d['tree_seal']}`; {d['tree_files']} sealed files remain unchanged (`INTEGRITY.json`).
Kit q: `{d['kit_seal_before']}` -> `{d['kit_seal_after']}` (`DELIVERY.json`).
Changed uploads versus build21e UPLOADS.json: {', '.join(x['name'] for x in upload['changed'])}; all others match (`UPLOAD_DIFF.json`).
Upload total: {d['upload_bytes']} bytes / {d['upload_files']} files; previous total {upload['before_bytes']} bytes (`UPLOAD_DIFF.json`).
Package: `{d['package']}`, {d['bytes']} bytes; {d['members']} members stream-verified (`DELIVERY.json`).
Package seal: `{d['package_seal']}`; SHA-256: `{d['sha256']}` (`DELIVERY.json`).
Every earlier package is unchanged. Package completed at {d['timestamp']}; workspace growth {d['workspace_growth_bytes']} bytes (`DELIVERY.json`).
No scheduler, network, GPU, Git, other agent, production store traversal or production weight load was used. Nothing was submitted.
'''
assert len(report.splitlines())<90,len(report.splitlines())
(L/'out/BUILD21G_REPORT.md').write_text(report)
print('out/BUILD21G_REPORT.md',len(report.splitlines()),'lines')
