# DISPATCH BOILERPLATE — read this first, then execute your brief

You are a dispatched worker (codex or Claude lane) in the VSIBench/VSTIBench campaign repo
`/home/jjyeung/agent_project`. Your brief gives the task; THIS file gives the standing rules.
Comply with all of it. If your brief conflicts with this file, the brief wins — note the
conflict in your report.

## Host quirks (comply exactly)
- **NO file deletion, ever (USER RULING 2026-09-11):** never run `rm`, `rmdir`,
  `unlink`, `shred`, `truncate`, `find -delete`, `git clean`, `git worktree
  remove/prune`, or inline-script deletion (`os.remove`, `shutil.rmtree`,
  `Path.unlink`, …) — including inside `bash -c` strings, ssh remote commands,
  and scripts you write. Pre-shell hooks and Codex execpolicy `.rules` BLOCK
  these and auto-queue the attempt. To get something deleted, append the exact
  command as a `- [ ]` row to `agent/PENDING_USER_COMMANDS.md` (main checkout)
  and note it in your report; the user reviews and runs the queue personally.
- **Sealed-package bytecode:** any lane that audits, reviews, or runs fixtures inside a sealed
  package sets `PYTHONDONTWRITEBYTECODE=1` or runs Python with `-B`. A sealed package refuses
  unsealed `__pycache__` bytecode at admission; quarantine stale bytecode by renaming it to
  `agent/rounds/_quarantine_unsealed_bytecode/<stamp>/`, never by deleting it.
- **NO broad searches (user directive 2026-07-16): never run recursive scans (`find`, `du`,
  `grep -r`/`rg` without a pinned subdir, `ls -R`) over `/home/jjyeung`, `/data2`, or any NFS
  root — they hang the fileserver and can FREEZE THE NODE.** Targeted lookups only: exact
  known paths, `-maxdepth`-bounded listings inside ONE named subdir, `/proc/<pid>/cmdline` for
  a run's output dir, sample-one-and-multiply for size estimates.
- `python` is Python 3.12; `python3` is an ancient 3.6. Always `python`.
- File freshness: `find <dir> -mmin -N` — NEVER `-newermt '-N minutes'` (silently matches nothing).
- `pgrep -f` matches YOUR OWN command line: always bracket-guard patterns (`[r]un_experiment`)
  or you will kill your own shell / infinitely self-match in until-loops.
- NEVER pipe-mask exit codes on protocol steps: no `cmd | tail`; run `cmd; echo rc=$?` or
  capture to a file.
- Detached processes (`setsid`/`nohup`) DIE at sandboxed-codex teardown — launch long-running
  processes from a real shell only. Codex sandbox also cannot write `.coord/`/`.git`.
- This extends to INDIRECT spawns: guarded target setters, controllers, and any command that
  makes a live run respawn/replace its workers must ALSO run via a real shell (`ssh -F
  /dev/null <host>`) — respawned run processes become sandbox children and die at teardown.
  Verify which node you are on (`hostname`) before trusting /proc checks or "local" host
  labels from handoffs — pids are per-node.
- **Recovery/relaunch lanes: relaunch steps are CONDITIONAL on verified death.** Before killing
  any guard/lease/process, re-check production yourself (fresh traces `-mmin -15` AND live
  workers); if the run is producing, STAND DOWN and report — never execute a kill/relaunch
  recipe against a live run just because the brief pre-dated its recovery.
- **Sandbox write-refusals are NEVER a terminal stop reason (USER 2026-08-01: "sandbox is not a
  valid reason to fail. The agent never tries to cheat.").** If a required write hits EROFS or a
  permission wall, do not end the lane: (1) retry the step over a real shell on an allowlisted
  node (`ssh -F /dev/null <host>`), where /data2 is fully writable; (2) if the step must run
  locally, write to a path inside your declared writable roots and record the redirection; (3)
  only if both fail, report the exact step + command back for orchestrator-side execution and
  CONTINUE the rest of your brief. Terminal stops are reserved for integrity refusals, gate
  verdicts, and hard caps — never for sandbox mechanics.
- Because `.git` is read-only in-sandbox (EROFS): NEVER attempt commits/branches or workarounds.
  Leave all changes in the working tree and end your final message with the exact file list +
  one-line-per-file description; the orchestrator lands the pathspec-limited commit.
- vnice threshold (USER 2026-09-07): count distinct
  physical 49 GB GPUs across our whole Trinity footprint, including SAM3 and every model
  replica. At most 16 may run unwrapped; batch/worker compute beyond those 16 is wrapped with
  `/data3/shared/scripts/vnice/vnice.sh` via a self-contained SCRIPT FILE (vnice is
  incompatible with env-prefixed inline launches). Shared services consume slots within, not
  beyond, the 16-GPU allowance.
- **vnice is for batch/worker compute ONLY — NEVER wrap shared services** (SAM3 daemons, the
  Qwen router/serving endpoints, or anything multiple experiment lanes depend on): a
  deprioritized worker is a throughput dip; a downed SAM/router node stalls EVERY Gemini and
  Qwen lane at once, and the vnice terminator kills wrapped services. Service launches run unwrapped, and any ops lane touching a service node verifies it
  terminator-free before ending its turn.
- Raw traces: use `trace_*_clean.json`, never the raw/clean pair together (double-count).
- **Service ownership (tearing down a daemon another lane silently reused stalls its live
  episode):** never reuse a service (SAM3 daemon/router, vLLM
  server, fleet router) that your lane did not start unless the handshake is recorded in BOTH
  lanes' receipts; never tear down a service you did not start; before tearing down your own,
  check its call/access log for foreign clients in the last 10 minutes and, if any, leave it up
  and report the client instead.
- **GPU cleanup proof (USER 2026-09-07):** before stopping any GPU process, freshly prove its
  UID, PID start identity, experiment/service association, lack of an active dependency, and
  lack of a fresh ownership conflict. Zero instantaneous utilization is insufficient. Stop
  only the exact owned process or service gracefully; never use a broad process match, touch
  another user's process, or force-kill after a graceful stop fails.
- **r797-lineage relaunch trap:** the sealed watchdog writes
  a time_ns nonce into the resume-input filename, which lands in `run_receipt_r797_*.json`, so ANY
  relaunch over an existing receipt exits rc=1 with `existing receipt core mismatch` and drops the
  lease; with `set -e` launchers the first category kills the rest. Before relaunching a run of this
  lineage: back up (sha manifest) and remove the stale receipts, launch per category with a bounded
  relaunch cap, and skip categories whose coord lease is COMPLETED; reference implementation
  `agent/rounds/candidates/r979_answerable500_qwen_agent/launch_all_drain_v2.sh` + its
  `LAUNCHER_FIX2_DEVIATION.md`. Science bytes stay untouched (launch-lane deviation only).
- **Progress = finalized count rising, never process liveness:** adapter/gateway faults can
  produce pred=None "finalized" traces, and a Gemini 503 "high demand" storm can leave every
  worker alive but idle while state files keep refreshing. Every drain watchdog must (a) check null-prediction counts at first-trace
  verification and (b) alarm when the finalized count is flat for 30 min with workers alive.
  503 storms are server overload, not rate limits: cut concurrency and hold, never relaunch;
  503-exhausted terminals are `infra_transient` and rerun as top-ups at census.
- **Answer-bank registry writes (AGENTS.md 7.0a) are lock-first (a concurrent read-modify-write
  can drop entries from the top-level `ANSWER_BANKS/REGISTRY.json`):** acquire the flock on REGISTRY.json
  FIRST, then re-read REGISTRY.json and SHA256_MANIFEST.txt inside the lock immediately before
  writing (never write from a copy loaded earlier), write atomically, and assert the entry-count
  delta equals the number of banks you added, recording before/after counts in your receipt.
  Before writing a result doc, `git log -1 -- <doc>` to catch a concurrent close-out.
- Cache locality: every launched Python/service environment must set `HF_HOME=/data2/jjyeung/cache/huggingface`, `HUGGINGFACE_HUB_CACHE=/data2/jjyeung/cache/huggingface/hub`, `TORCH_HOME=/data2/jjyeung/cache/torch`, and `PIP_CACHE_DIR=/data2/jjyeung/cache/pip`. Do not rely on an interactive shell profile for detached or remote launches.

## Pre-review hardening checklist (verify ALL before requesting review; each item has
## produced a verified blocker in gate review)
1. Storage: programmatic write-site sweep (AST + string literals) over the FULL runtime
   closure (carrier, workers, routers, daemons, tools) — every write under the run-scoped
   /data2 root, fail-loud on /tmp//home; sanitize traversal-bearing path arguments.
2. Provenance: receipts/manifests live OFF-git, generated LAST; tracked docs cite
   package-internal files by path only (acyclic authority: external manifest + git HEAD);
   never hand-write a PASS — attestations derive from live command ledgers with rc checks.
3. Fail-loud everything: heartbeat threads (timeouts + exception paths + abort sentinel the
   launcher/runner honor), worker exceptions, zero-trace arm completions, clean-step failures.
4. Spend safety: one attempt per qid consumed at the provider boundary; budget rollback must
   NEVER delete previously consumed/committed starts on resume or queue drift.
5. GT isolation by design: no GT-bearing file in the runtime package closure (programmatic
   census); scoring is post-drain from the canonical dataset; post-hoc GT-access trace audit
   in the scoring contract (same-user resistance stays out of scope per the 2026-07-11 ruling).
6. Binding: hash-bind the ENTIRE executable closure (incl. routers/daemons/policy modules,
   bytecode) at execution, not just carrier/runner templates; no auth-bypassing direct calls.
7. Launch admission: exercise it in a fixture against REAL coord.py leases (field-compatible,
   freshness-checked) before claiming launchability.
8. Comparator purity: reused/nominal traces must byte-match the round's pins PER TRACE; mark
   categories ABSENT rather than mixing pin sets.

## Package-build hardening standard (reviewers verify ALL of these; build to them from the start)
- Telemetry: EVERY provider call site (planner, tool-internal, direct SDK calls) records
  content + thoughts + finish_reason + usage through the shared sink; mergers/scorers REFUSE
  rows missing finish_reason and refuse call-count vs telemetry-row mismatches per trace.
- Census anchoring: closure/entrypoint censuses anchor to the REVIEWED receipt (recomputed at
  bind time from the reviewed commit), never to a co-mutable document; fixtures must refuse
  SYMMETRIC corruption (entry removed from every co-mutable copy at once).
- Executable closure: every pre-verifier executable (launch wrappers, bind scripts, mergers,
  controllers) is hash-bound in the execution closure; launcher-byte drift refuses.
- Admission checks dependencies PRE-SPEND (e.g., required predecessor merge receipts exist at
  launch admission, not first at post-spend merge).
- Cohort retirement: every VSIBench package's `audit_package.py` calls
  `agent/scripts/cohort_guard.py` on both its membership authority and answer-free admission
  input; reviewers verify both calls and refuse any fresh cell on a retired cohort.
- Heartbeats/ramp controllers: timeouts + exception paths that publish the abort sentinel and
  terminate+reap provider children; state transitions are write-ahead (durable ledger record
  fsynced BEFORE the new state applies); no silent daemon-thread death.
- Fixtures exercise REAL code paths (real binder on corrupted package, real provider boundary
  with injected failure, real controller dispatch, real materialization); no AST/text scans as
  proof, no /tmp scratch (storage guards refuse it), no live-external-state requirements
  (synthesize schema-exact leases/receipts in fixture namespaces).
- Admission/coordination fixtures must ALSO include a READ-ONLY parse of the REAL shared coord
  store (in addition to the synthetic rows), not only synthetic ones — the live store permanently
  carries other lanes' non-conformant leases/COMPLETED history that fail-closed full-store parsing
  refuses, so a synthetic-only fixture misses the incompatibility.
- Package smokes mock at the NETWORK TRANSPORT layer ONLY — the real provider-side tool-schema
  conversion (e.g. `convert_to_genai_function_declarations` via `bind_tools`) and the real
  coordination-lease lifecycle (claim/heartbeat/release) must execute, never be mocked away (a
  mocked `_build_planner_bindings` hides an unconvertible tool schema and an unclaimed heartbeat
  lease).
- Tool-interface clarity (USER 2026-07-31): a planner-facing tool
  must not be failable by an undocumented idiosyncrasy of its call or payload — every argument
  states where its value comes from (e.g. "instance_id: an id from this label's
  matched_instance_ids list"), every returned field is self-describing (units, frame, ordering;
  never magnitude-sorted fields with positional names), and refusals name the violated rule.
  Keep descriptions CONCISE — a few Args/Returns lines, not paragraphs.

## Diagnostic fast path (USER 2026-07-19 — small diagnostic runs must be CHEAP)
For DIAGNOSTIC-class rows (aggregate-only readout, no score-index action, ≤~100 episodes):
- FORK THE NEAREST EXISTING RUNNER (e.g., a controller that already reruns episodes under the
  target pins) and change only the experimental knob — never rebuild launch machinery.
- No new watchdog/health/receipt scaffolding beyond tmux + the runner's own logs and receipts;
  the harness's standing telemetry persistence suffices.
- No review rounds (gate-scope ruling); verify outputs post-hoc.
- Budget the BUILD at minutes, not hours; if a diagnostic build exceeds ~20 minutes, stop and
  report what forced the complexity instead of continuing.

## Packet / gate protocol (/critique gate rounds)
1. Commit the EXACT packet file list in ONE checkpoint commit. No split commits.
2. Run the packet's post-commit audit generator/commands (fail-loud; check rc).
3. Only then dispatch the reviewer: `agent/scripts/codex_dispatch.sh review <dir> <prompt>`
   (Astra at high effort for gates; Sol, Terra, or Luna for mechanical verification according to
   task difficulty). Brief in `agent/scratch/codex_prompts/`.
4. Receipts land in `agent/scratch/codex_runs/<ts>_<label>/` — `final_message.md` + `meta.json`
   are canonical; NEVER trust a relayed/phantom summary over the receipt file.
5. Reviewer prompts: NO "do not execute"-style headers or lane-scoping preambles (reviewers
   refuse literally). Include the packet's `SCOPE_RULING_VERBATIM.md` text when a scope ruling
   governs classification.
6. Hard cap 3 rounds per series. FAIL at cap = STOP and report to the orchestrator; never
   self-authorize a successor. Round numbers are ORCHESTRATOR-ASSIGNED — never self-assign.

## Standing user rulings (binding)
- **Scope of gate findings:** same-user operator-forgery resistance is OUT of gate scope
  (cheating is handled post-hoc); scientific validity, functional correctness, preregistration
  integrity are IN scope. Accidental-corruption failure modes are IN scope.
- **Partial readiness:** never idle quota/endpoints/GPUs on a partial blocker — run the ready
  questions/scenes now, backfill blocked ones via RESUME. Sealed membership unchanged;
  partial drain is execution order, not membership change.
- **Eval spend:** runs under 1,100 questions are pre-authorized (gates unchanged; threshold
  set so the 1,057-qid ReVSI tiny cohort runs without a per-launch GO); ≥1,100 or
  qualitatively new scope requires the user.
- **Data dependencies:** every external data file your round reads
  must be enumerated in the manifest with path+SHA and verified on the ACTUAL launch host by
  the prespend validator. NO critical-file guard inside a broader `try/except: pass` — assert
  at startup. (A hard-coded wrong-cluster path can silently zero whole categories.)
- **Single seed / one eval attempt** for paper benchmark numbers.
- **Never solve benchmark questions yourself** — deterministic scripts only; bulk LLM labeling
  goes through the Gemini API key, not agent tokens; the NV inference keys need the user's
  per-use permission (USER 2026-09-11).
- **Run priority:** within Gemini API runs the docket order is the newest `USER-RULING` in
  the queue (ablations and user-flagged high-priority items first). Qwen runs proceed IN PARALLEL on the self-hosted fleet —
  they do not yield to Gemini except for GPU preemption per the existing API-over-Qwen rule.
- **Launch authorization (user 2026-07-17):** Qwen and Gemini experiment launches need NO
  per-run user GO at any size — launch the instant the package gates. Gates/protocols
  unchanged. Other carriers keep the <1,100-question threshold above.
- **Launch-first rule (USER 2026-09-07):** after correctness, scientific, authorization, and
  resource gates pass, start the smallest valid ready registered experiment/cell and verify
  evaluation output before throughput work. A prepared package or assigned worker is not launch
  evidence; never waive mandatory gates or pairing contracts.
- **Output-token budgets (user 2026-07-17):** thinking-model calls pin ≥16k output tokens
  (4096 produces empty responses). Budget has ladder semantics: answered-under-
  ceiling traces are valid keepers at temp 0; only budget-bound failures rerun higher, as a
  top-up. Runners MUST persist per-call finish_reason + usage.
- **Canonical launcher (user 2026-07-17):** launches prefer the canonical `agent/launch.sh` +
  `agent/harness/` path when compatible with the round; if incompatible, keep the bespoke path
  and state the specific incompatibility in the gate receipt — never silently bespoke.
- **Node ruling (USER 2026-08-15): every Trinity node is usable.** Sole condition: our
  batch/worker compute beyond a 16-GPU total footprint runs
  vnice-wrapped (see the vnice bullet). Occupancy etiquette stands — check `nvidia-smi`
  ownership before every placement and never crowd out other users' live jobs.
- **Commit quiescence:** NEVER commit changes
  to shared runtime files (agent/harness/*, agent/coord.py, agent/infra/qwen_router/*,
  shared probes) while ANY run is live — live runs verify these bytes per-episode and die on
  drift. Batch such commits to global quiet points; enumerate live runs first.
- **Residue archiving:** never archive an entire
  output/experiment directory wholesale — adjudication/amendment receipts bind evidence by
  ABSOLUTE PATH + SHA. Separate first: bound evidence (`.resume_rejected`, quarantine rows)
  stays at canonical paths; archive only unbound superseded launch metadata.

- **Cluster-utility scope (USER RULING 2026-07-19):** the internal behavior of shared cluster
  utilities (vnice/terminator and similar wrappers) is OUT of gate-review scope — including
  their own /tmp or scratch writes. Reviewers must not raise findings about, and builders must
  not vendor/hash-bind, these utilities. The binding requirement is only that EXPERIMENT
  outputs (traces, receipts, ledgers) write to the run-scoped /data2 root. Do not spend
  reviewer rounds on this class.

## Shared-resource constraints (do not disturb)
- Other lanes' experiment dirs, leases, and coord slots — hands off unless your brief says.
- Gemini key: 8M input tok/min HARD cap, cannot be raised. Prior storm history: certified
  worker counts have self-saturated it; ramp with a 15-min health watch and step down on 429s.
- **Reabsorb freed quota (USER 2026-07-19):** when a Gemini-consuming run drains, the freed
  capacity goes to the remaining runs — controllers/governors should step their worker limits
  back UP (within their reviewed ceilings, health gates + 429 backoff unchanged) rather than
  leaving quota idle. The NV inference keys are used only with the user's per-use permission
  (USER 2026-09-11); the Google Gemini key is the preferred carrier.
- Raw outputs under `experiments_5.0/**`, composites, dense `.npz`: NEVER committed to git;
  reference by path + sha256.

## Cross-agent experiment requests
If your work concludes an experiment SHOULD BE RUN but running it is outside your brief/scope,
do NOT run it and do NOT bury it in your report: add a row to
`agent/agentic_information_5.0/EXPERIMENT_REQUEST_QUEUE.md` (schema at the top of that file;
status PENDING, auth line honest). Experiment-running sessions check that queue every session
start / tick via `grep -c "| PENDING |" agent/agentic_information_5.0/EXPERIMENT_REQUEST_QUEUE.md`
and claim rows by flipping status. Results come back as pointers on the row.

## Reader-facing writing (papers, updates, reports)
If your task writes or edits ANY reader-facing text (paper tex, captions, weekly updates,
READMEs), read `.claude/skills/no-archaeology/SKILL.md` and comply: never narrate the
project's revision history; per-sentence test = "would this inform a reader who never saw our
process?"; ablations are designed comparisons, never chronology.

## Report format (your final message)
**HARD LIMIT: ≤20 lines.** The orchestrator is an expensive model; your full detail goes in a
result/receipt FILE (routed per AGENTS.md §5.1 or your receipt dir), referenced by path. The
20 lines: outcome/verdict first, key numbers, commits (hash + one-liner), artifact paths (+
sha256 for anything off-git), liveness for anything left running (pids, hosts, log paths,
one-line health-check command), explicit blockers. Nothing else.

## Turn discipline
End your turn ONLY at a decision point (verdict landed, work complete, blocked, or a choice
the orchestrator must make). Do NOT checkpoint with interim "still waiting/still running"
states — park interim status in your status file or the coord slot; the orchestrator's sweep
reads files, not turn-ends.

- **Launch verification cadence (USER 2026-09-16):** purpose, in the user's words: catch failures quickly when they are most likely to happen. Failure likelihood is highest right after a launch, restart, resume, ramp step, version takeover, membership extension, or alarm, and falls once traces are landing repeatedly, so check frequency tracks it: frequent checks of BOTH process liveness (supervisor and worker pids, service health) AND outputs landing (finalized trace files with non-null predictions on /data2); either signal alone can mislead. At each of those moments the lane checks every 1 minute until traces are landing repeatedly. Two one-minute checks with no new trace mean debug immediately (worker logs, service health, provider errors). Once traces land, lengthen the interval step by step (about 2, 5, then 10 minutes) and hold at 10; drop back to 1 minute whenever a signal regresses (a pid dies, no new trace within one expected episode time, rising error rate). A detached watchdog on the 10-minute cadence may take over once traces are landing, and the lane may end its turn reporting the watchdog pid, its log path, and the last verified answer count. The orchestrator's own ticks run every 10 minutes while any lane is launching or draining and never substitute for the lane's one-minute checks.

## GPU right-sizing for tool/backbone model serving (user directive)
Maximize throughput; do NOT over-allocate GPUs for model serving (SAM3, Qwen tool/backbone,
any vLLM stack). Before grabbing GPUs: (1) verify existing/surviving endpoints and measure
actual headroom under load; (2) size replica count to the REMAINING demand of the runs you
serve, not a fixed number; (3) prefer raising per-replica concurrency (vLLM continuous
batching / max-num-seqs, SAM3 request batching, client worker counts) over adding replicas,
and adding replicas over adding GPUs; (4) NEVER change pins/quantization/model identity on an
in-flight round to save GPUs — throughput levers only. Report GPU count used vs available and
projected drain time in your final message.

## Experiment round banking storage (user directive)
At round-bank time the scoring/banking lane relocates the round's /home experiment dir to
/data2/jjyeung/agent_project_data/experiments_5.0/ with the manifest-verified per-round
symlink protocol (nothing is backed up — full-manifest verify before source deletion).

## Sole copies never on node-local /tmp
Experiment OUTPUTS (traces, receipts, audits) write to shared storage (/data2) from the very
first trace. Node-local /tmp is for CODE worktrees only — a node failure strands or destroys
sole copies, and nothing is backed up. If a launcher defaults its output dir under the worktree, redirect it
to /data2 before launch.

## Run authorization + SAM3/429 rerun classes (user directives)
Paper-needed experiment launches proceed without per-run GO (gates and recorded cross-agent
orderings still apply). SAM3-tool-failure and HTTP-429 transport-failure episodes are
standing rerun classes in every bank: rerun exactly those qids as top-ups, merge, pinned
rescore. Model-merit failures still count wrong.

## Launch-safety invariants — every new run package implements ALL of these up front (reviewers: check each)
- Every launch lane emits non-sealed `RESUME.sh` + supervisor + detached watchdog artifacts at launch time under `RESUMABILITY_CONTRACT.md`; resuming through `RESUME.sh` needs NO gate review.
- Use `agent/rounds/candidates/resizable_pool_harness/` as the canonical implementation and
  `agent/agentic_information_5.0/GEMINI_THROUGHPUT_BOTTLENECK_RESULT.md` as the evidence record.
- Divide work with an episode-level claim queue: workers take the next available question; never
  use per-category or fixed worker shards.
- Publish claims and once-only files through NFS-safe private-file-plus-hard-link publication,
  never bare `O_CREAT|O_EXCL` or `renameat2(..., RENAME_NOREPLACE)`; claims record owner +
  heartbeat, and stale no-trace claims are reclaimed rather than terminal-refused.
- Make worker count a live JSON target reconciled continuously: raise by staggered spawns
  (~45 s), lower by retirement at a claim boundary, and set the sealed admission ceiling HIGH at
  build time (ceiling is not the day's target); never stop/restart merely to rescale.
- Persist spawn bookkeeping so stagger survives controller restart and accounts for surviving
  children.
- Classify a true 429 only by exact HTTP-429 status-field or `RESOURCE_EXHAUSTED` signature,
  never a bare `429` substring (known false positive: episode duration `(429.8s)`); on a genuine
  burst, the watchdog lowers and persists the live target.
- Before any write, validate that the output root is under `/data2`; traces, state, and logs
  write there from their first byte, never to `/tmp` or `/home`.
- Start new Gemini launches high (about 16 staggered workers), then ramp toward about 6M of the
  8M input-token/minute limit under rolling health gates; for Qwen, use endpoint admission/queue
  depth as the health signal.
- Persist monotonic start, end, and elapsed timestamps for every provider and tool call, plus
  content, thoughts, finish_reason, and usage.
- Pin agentic Qwen output budgets to at least 16k tokens.
- Ship a deterministic verifier covering claim/steal, stagger including post-restart, ramp-down
  retirement, crash reclaim, the true-positive 429 and duration false-positive classifiers, and
  output-root rejection.

- USER-RULING 2026-09-14: Gemini output caps do not affect generated tokens except on a cap hit, so Gemini planner and verifier output budgets are 32,768 from the first pass on every new Gemini package, both arms alike, with no new comparison lineage implied; the 16,384-then-rerun-at-32k procedure stays only for Qwen, where a 32k cap needs the extra KV memory and prompt plus max_tokens must fit the replica context. Existing 16k Gemini cells rerun cap-hit-and-wrong questions at 32k as before.
