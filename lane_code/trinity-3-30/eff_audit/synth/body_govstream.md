# Build brief 7 of 8: govstream (lane `eff_govstream`, branch `eff/govstream`, Claude Opus, effort high, size S: 2 to 3 agent-hours)

Build the one launcher for a governed stream and the one command that mirrors sealed work to a second node, so that no lane writes its own.

## Why

- 29 files in lane folders call the governor's `register.py`, about 25 of them distinct; `bundle_up_launch.py` and `bundle_up_p10_launch.py` differ only in the lane name and `'--priority', '30'` against `'10'` (`AUD/kits/INVENTORY.md` section 3; `AUD/kits/govstream_launchers.txt`).
- One of them carried a bug that the governor punishes: "launch_pull.py starts the root as `bash -c 'kill -STOP $$; exec timeout ...'`; after the first SIGCONT the exec turns the registered PID's comm from bash into timeout, so any stream paused once fails the identity check at its next admission" (`B/events/trin_read/20261116T0623Z_BLOCKER_rt0_refused.md`). The fix landed in that lane only.
- Sealed work existed on one node: the K1 raster builder, the refit inputs and every trainer build were lost with trinity-2-18 (`AUD/incidents/INCIDENTS.md` rows 1 and 2). The lane rule already demands a mirror on a second node; nothing makes it one command.
- Input uploads waited behind review although review cannot change input bytes: the VSTI inputs were admitted at 10:47Z and 10:55Z, after the code was confirmed at 10:29Z (`AUD/process/NOTES.md`, "IO governor").

{{COMMON}}

## Scope

**`tools/orchkit/govstream.py`.** Generalize the 42-line `REF/trinity-1-3/native_r4/work/streams/launch_gated.py` (read it and its siblings `launch_push.py`, `launch_push_file.py`, `launch_tar.py`, and `REF/trinity-1-3/trin_read/work/launch_pull2.py`).
- `govstream.py run --lane L --bytes N --sha256 HEX|- --priority P --kind pull|push|tar-read|tar-write [--writes-nfs] [--io-weight W] (--out FILE | --in FILE) -- CMD...`
- The registered root process is a `bash -c` that stops itself and then runs CMD as a child and waits for it. It never calls `exec`, so its command name stays `bash` across every pause.
- The data path runs through the governor's `ratelimit.py`; registration goes through its `register.py` with tier 3 and `--allow-resume`, and with the flags the governor's README prescribes for the kind (`--writes-nfs` for a stream that writes NFS, `--io-weight 1` for a pure internet or head-node transfer). Read `/data3/jjyeung/orch_n13_20261026/io_governor/README.md` once, in bounded parts, and match its current interface exactly; the helper directory and the streams directory come from `ORCHKIT_GOV_HELPERS` and `ORCHKIT_GOV_STREAMS`.
- After the stream ends it verifies the byte count and the sha256, writes `<target>.RECEIPT.json`, renames the governor record to `.done.<epoch>`, and only then renames `<target>.part` to the target. On any failure it exits non-zero, keeps the `.part` file and the record for inspection, and retries nothing.
- `govstream.py batch SPEC.json` starts every stream of a step stopped and registers them all at once, each with its own record and priority, because a stream registered late waits behind every earlier one.
- It refuses a stream of a directory tree to or from `/home` or `/data*` (archives only), and a destination under `/home`.

**`tools/orchkit/mirror.py`.** `mirror.py --src PATH --dest-node trinity-X-Y --lane L` sends one tar stream of a sealed kit, packet or tool folder from this node's `/scratch` to `/scratch/jjyeung/n30_mirror/<lane>/` on a second node over InfiniBand (`tar cf - X | ssh -o ConnectTimeout=20 <node>.ib 'cd ... && tar xf -'`), compares the sha256 of the stream on both ends in the same ssh call, and prints the two paths and the digest as the line the lane puts in STATUS.md. It refuses a destination host without `.ib`, a path under `/home` or `/data*` on either side, trinity-2-18 and trinity-2-28, the head node, and a source above 5 GB unless `--approved-by` names the order. It opens one ssh session per mirror and never loops.

**`docs/STREAM_PRIORITIES.md`.** A proposal of at most 30 lines for the orchestrator: the priority bands distillation lanes use among themselves (inputs of a job that holds a GO; kit code and bundles under 100 MB; the mover; bulk), the rule that a data input is registered when it is built and not after its kit's review, and the statement that no band outranks the main project's streams. The orchestrators agree the numbers; you propose bands, not numbers.

## Files you own

`tools/orchkit/govstream.py`, `mirror.py`, `tests/test_govstream.py`, `tests/test_mirror.py`, `tests/fixtures/govstream/`, `docs/STREAM_PRIORITIES.md`.

## Tests (folder `tools/orchkit/tests/`; a stub helper directory stands in for the governor)

The stub holds a `register.py` that records its arguments and writes a record file, a `ratelimit.py` that copies its input, and whatever identity helper the real launchers import; a fake `ssh` runs its command locally.
1. Pull and push round trips: bytes and sha256 verified, receipt written, record renamed to `.done.*`, `.part` renamed last.
2. Pause and resume: the test stops and continues the registered root, and its command name is `bash` before and after. The same test run against a launcher line that uses `exec` must fail; keep that line as a fixture, so the rt0 defect cannot return.
3. A sha256 mismatch and a short stream each exit non-zero, keep `.part` and the record, and start nothing again.
4. `batch`: three streams are all registered before the first byte moves; the stub's log shows three registrations, then data.
5. Refusals: a directory tree to `/data3`, a destination under `/home`, a mirror to a plain host name, to trinity-2-18, to the head node, and of 6 GB without approval.
6. `mirror.py` with the fake ssh: equal digests print the STATUS line; a corrupted far end exits non-zero.
7. The suite passes on `/usr/bin/python3` and under the bwrap run of rule 8.

## Deliverables

Branch `eff/govstream`; `W/REPORT.md` naming every README flag you mapped and the one live proof still owed (a single small governed pull, run by an operator lane on an ORCH GO, never by you); the RESULT event; the result block in RECORD.

## Out of scope

The governor, its ordering, its rates and its node agents; any registration with the real governor; any real ssh or copy; replacing the launchers of streams that run now.

## Review

None required: the launcher admits nothing, and the governor still admits every stream. The live proof on a GO is its acceptance check.
