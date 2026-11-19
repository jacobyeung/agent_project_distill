from pathlib import Path
K=Path('/scratch/jjyeung/orch_n30/so_reads228/work/round4/kit')
p=K/'COORDINATOR.md';s=p.read_text().replace('/reads228/kit','/reads228/kit2').replace('`kit/reference`','`kit2/reference`').replace('`kit/ingest/','`kit2/ingest/')
s=s.replace('All 21 archive parts are staged and match their pins according to the coordinator\'s 18:37Z check.', 'All 21 archive parts are staged. The kit checks their pins itself.')
s=s.replace('The stage-only sequence never queries a card or creates a run directory.', 'The stage-only sequence never queries a card or creates a run directory. It reads all three runtime archives before creating any runtime member, then extracts every registered group under `reads228/private_rt/`. The `x/` helpers stay there as records and have no namespace bind or execution path.')
s=s.replace('`--run-only` rechecks staging and operator imports before the card gate,', '`--run-only` rehashes staged data and checks operator imports before the card gate; allow minutes of local scratch IO before the first idle reading. It')
s+='''
The coordinator-authorized second `--stage-only`, from `kit2` after the reported refusal, starts with an absent `private_rt/`. It verifies the same 13 runtime part pins, completes pass 1 across r0/r1/r2, creates the private runtime in pass 2, extracts inputs into the private logical root, installs sealed code, probes the namespace, prepares once, verifies staging and probes operator imports. It never reads or removes the 443 entries left in shared `orch_cd/` by the refused delivery. The old `kit/` stays in place.

A subsequent authorized stage check on a successfully staged kit compares every existing runtime file and symlink in pass 1, preserves matching files and their metadata in pass 2, skips matching input members, verifies installed code, and reuses READY.json instead of launching preparation again. A conflict refuses before runtime writes. There is no retry loop; an interrupted extraction or failed preparation requires coordinator review before another invocation.
'''
p.write_text(s)
p=K/'README.md';s=p.read_text().replace('/reads228/kit','/reads228/kit2').replace('`kit/ingest/','`kit2/ingest/')
s=s.replace('This exact path is required because STAGE_PLAN pins the package\'s `a/6` there;', 'This delivery selects kit2 in STAGE_PLAN for the package\'s `a/6`;')
s=s.replace('**Staging uses a private logical root.**', '**Staging uses private runtime and logical roots.** Every runtime member stages under `reads228/private_rt/` with its archive-relative `sj/`, `m/` or `x/` layout. Pass 1 authenticates all parts and headers across all three archives, hashes file bodies, compares existing members, and rejects unknown namespaces, unsafe paths/links, unsupported types and topology conflicts before any runtime member is created. Pass 2 extracts only after the full preflight succeeds. Matching existing members retain their bytes, inodes, modes and modification times. The two `x/` helpers are recorded in STAGE_CHECK.json and never bound or executed.')
s=s.replace('The package\'s own `orchard_job.namespace` supplies its sj/fsw/m-ap/uv binds;', 'The package\'s own `orchard_job.namespace` receives `private_rt` and supplies its sj/fsw/m-ap/uv binds;')
s=s.replace('and adds the private logical-root bind.', 'and adds the private logical-root bind plus narrow kit/control/output binds. It never binds the private runtime root or its `x/` helpers into the namespace.')
s=s.replace('Runtime extraction records every member\'s name, type and size.', 'Runtime extraction records every member\'s name, type, size and link. [RUNTIME_LISTS.json](RUNTIME_LISTS.json) summarizes the three supplied lists: 115,837 headers and 10,371,055,588 file-content bytes. The registry in STAGE_PLAN links each namespace to package receipts and its in-namespace path. Exact header digests also pin membership to the coordinator lists.')
s=s.replace('Native CPython performs stdlib stage, gate and comparison work.', 'Native CPython at `private_rt/sj/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12` performs stdlib stage, gate and comparison work.')
s+='''
The coordinator-authorized stage-only invocation from kit2 starts with no private runtime after the reported refusal. It stages the complete private copy and ignores the 443 shared entries left by that refusal. No removal or shared-file reuse occurs. A successful later stage-only invocation verifies and preserves the existing private files, reuses READY.json, and repeats the namespace/import checks. It does not rerun preparation. See [COORDINATOR.md](COORDINATOR.md) for the stage-first sequence and the single card-gated run. There is no automatic retry after failure or termination.

The operator installs the sealed `install_process_guard(out)` before loading the operator or spawning children. The test harness runs bootstrap tests with actual `/usr/bin/python3` 3.6.8 when available and runs both control-boundary suites without site-packages. Full target runtime imports, preparation and Ada/H100 parity remain deployment checks.
'''
p.write_text(s)
p=K/'ENVIRONMENT.md';s=p.read_text().replace('`kit/A10b/', '`kit2/A10b/')
a=s.index('The physical runtime mapping is:');b=s.index('The adapter calls',a)
s=s[:a]+'''The physical runtime root is `/scratch/jjyeung/orch_n30/reads228/private_rt`. The package receives that root directly; `sj` is a real private directory.

| Archive group | Host path below private_rt | In-namespace path | Package evidence |
|---|---|---|---|
| devs1_direct, rv_merge_fix, legs1_reads | `sj/orch_cd/<group>` | `/scratch/jjyeung/orch_cd/<group>` | `orchard_job.py:128–129`; `trace_runtime.py:22–25`, `export_stage.py:19` identify the latter two. devs1_direct membership comes from the coordinator list. |
| p1cpu | `sj/envs/p1cpu` | `/scratch/jjyeung/envs/p1cpu` | `orchard_job.py:128`; `orchard_stage.py:19–24` pins its absolute Python link. |
| Native CPython | `sj/uv-python/cpython-3.12.13-linux-x86_64-gnu` | Same suffix below `/scratch/jjyeung`, and `/home/jyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu` | `orchard_job.py:128,131`; `orchard_stage.py:19–24`. |
| Base manifest | `m/ap/90da7ac2` | `/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/90da7ac2` | `orchard_job.py:130`; `ORCHARD_ASSETS.json:7–10`. |
| Base environment | `m/ap/19252904` | `/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/19252904` | `orchard_job.py:130`; `q/env.json:1`, `orchard_stage.py:22–23`. |
| Empty package fsw bind | `fsw` | `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung` | `orchard_job.py:129`; zero archive members. |
| Staging records | `x/pull.py`, `x/need_frames.txt` | None; never bound or executed | Coordinator r0 list; fix4 decision. |
| Private logical root | Outside private_rt: `reads228/private/b01ec87a6f29b` | `/scratch/jjyeung/b01ec87a6f29b` | `namespace228.namespace_command` appends this bind after the package SJ bind. |

Package evidence above is under `A10b/src/orchard_h10/vendor/`; the delivered q receipt is `evidence/q/env.json`. STAGE_PLAN contains receipt sizes/hashes, header digests, member counts and all physical/namespace destinations. RUNTIME_LISTS.json contains source-list hashes and measured listing totals.

The adapter adds narrow binds for the kit, `prepare`, `operator_probe` and `namespace_probe`; an executing operator also gets its own output directory. It changes the namespace working directory to the kit. Neither the stage root nor private_rt is bound wholesale, so the record-only x helpers remain invisible. This allows the private runtime, private logical root and operator control paths to work together while shared environments and orch_cd stay hidden.

'''+s[b:]
s=s.replace('appends one bind from the private logical root to the pinned logical path.', 'appends the private logical-root bind and the narrow control binds described above.')
s=s.replace('staged native `uv-python/.../bin/python3.12`', 'private native `private_rt/sj/uv-python/.../bin/python3.12`')
s=s.replace('Runtime members are unavailable in this build workspace.', 'Complete runtime member lists are supplied in `evidence/runtime/`; archive bodies are unavailable in this build workspace. Header-only, zero-body tar fixtures exercise all 115,837 real entries, and a fixture with one additional namespace refuses before any runtime write.')
s=s.replace('Extraction on 2-28 authenticates ordered parts,', 'Pass 1 on 2-28 authenticates all ordered parts and file bodies across all three archives before pass 2 writes any member. It')
p.write_text(s)
print('Updated README, ENVIRONMENT and coordinator sequence for kit2 and private runtime.')
