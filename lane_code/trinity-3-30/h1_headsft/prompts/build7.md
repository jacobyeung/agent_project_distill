# Build H1-kit-7: run the H1-0 own-head read on b04's reviewed parity reader (CPU only here)

You are a Codex builder for lane h1_headsft on Trinity node trinity-3-30. Workspace `K=/scratch/jjyeung/orch_n30/h1_headsft/kit`
(write only inside K). Read `K/BUILD_REPORT.md` (sections "Build 3" H1-0 behavior, "Build 4", "Build 6") and
`K/h1eval/h10/RUN_H10.md` first; keep everything that passes. Work autonomously; where something is ambiguous, choose
the conservative option, record it in `K/BUILD_REPORT.md` under a new section "Build 7", and continue.

## Rules for the build (binding)
- Trinity rules: never run recursive grep/find/du/ls -R or any search over `/home` or `/data*`; read named files there
  only, in bounded parts. No Git. No ssh/scp/rsync/network. No GPU (`CUDA_VISIBLE_DEVICES=""`). No deletion or
  modification outside K; inputs (b04's code included) are read-only; never kill processes.
- Disk: this node is at its 200 GiB floor. Temporaries and pytest basetemps under ONE directory `K/tmp/b7/`; never copy
  the tree, a kit, b04's code or model files; add under 20 MB. Report the size you added.
- Python `/scratch/jjyeung/envs/p1cpu/bin/python -B` with `CUDA_VISIBLE_DEVICES= PYTHONPATH=K/tree:K`, at most 32 GB RAM,
  16 threads. Pytest: `-p no:cacheprovider -p tests.reader_plugin -p tests.build4_plugin --basetemp=K/tmp/b7/<name>`,
  with `LANE_TEST_OUTPUT=K/tmp/b7`.
- No answer post-processing: the model converts units and formats numbers itself; the launcher never rewrites text.

## Why
H1-0 reads the step-544 export with the OWN arm (own pose head, own gravity, own depth, SAM 3 + selector for ground) on
dev-S1 routed (636 items + 900 perturbed decodes) and, when frames exist, ReVSI official999, and pairs it with a tower arm
(registered design: `/data2/jjyeung/agent_project_data/distill_design/H1_GT_HEAD_ROUTING_SFT_20261116.md`, sections
Answer and Registration). The kit's launcher `K/h1eval/h10/{launch.py,perception_own.py,cpu_first_batch.py,run_card.sh,
card_entry.sh,merge.py}` was written against a draft of b04's reader (`e2e_reader.real:make_real(export, artifact, items,
*, perception_factory, device)`). b04's REVIEWED reader (Codex delta review GO) has a different interface and launch
pattern, and it already ran on GPU (smoke 5/5 types). H1-0 must land before ~13:00Z tomorrow, so the kit must run on it now.

## b04's reviewed reader (read these, bounded)
3-30 copy `B=/scratch/jjyeung/orch_n30/b04_e2ehook` (the run host 1-13 holds the same code at
`/dev/shm/jjyeung/b04/host2/b04_e2ehook`, run inside bwrap with `/dev/shm/jjyeung` bound at `/scratch/jjyeung/b04shm`):
`B/e2e_reader/parity.py` (`make_real(export_dir, artifact_manifest, items, *, perception_factory=None, device, settings)`,
`load_native`, `bind_item`, `score`, `key`), `B/e2e_reader/real.py` (`real_perception`, TowerG3T), `B/e2e_reader/core.py`
(E2EGenerator), `B/e2e_reader/stage1.py` (StageOne socket, OwnDepthScale), `B/parity_kit/README.md`, `B/parity_kit/run_parity.py`,
`B/parity_kit/cpu_first_batch.py`, `B/parity_kit/gpu_113.sh`, `B/parity_kit/settings_bw.json` (if absent on 3-30, use
`settings.json` and record the difference), `B/STATUS.md` (Done/Running sections). b04's message: perception_factory is
called as `perception_factory(artifact=, model=, processor=, device=, item=)` and returns a Perception.

## Deliver
1. Launcher on the reviewed interface: default entry `e2e_reader.parity:make_real`; pass `settings` (a JSON path option,
   default b04's settings file on the run host) with `arm` set as b04 requires; adapt the kit's own perception factory to
   b04's keyword signature (own pose9/gravity/depth from the model's heads as `K/h1eval/perception.py` does, ground/gap
   through b04's StageOne socket and selector head from the same artifact, the registered modes applied through
   `h1eval.perception.perturb` only on their target types). Keep read counts, resume, projection, refusal of busy cards,
   vnice and the M1-M4 records exactly as registered.
2. Items: map `K/items/devs1_routed.json` (636) onto b04's item keys/binding (`parity.key`, `bind_item`, frames JSON and
   dense manifest in settings); refuse any unmapped item; record the mapping and its sha256. 32-frame layout as b04 uses
   (`layout count=32`). ReVSI official999 (`K/items/revsi999.json`): implement the same path; if b04's settings carry no
   ReVSI frames, the ReVSI run refuses with a clear "frames not staged" error and the report states what must be staged.
3. Tower arm: the registered tower arm is b04's parity read of the same export (its `own_depth` arm: in-call G3T pose,
   own gravity, own-depth scale). `--tower-from DIR` must accept b04's GPU journal format
   (`<run>/gpu_results/own_depth_p*/items.jsonl` as written by `B/parity_kit/run_parity.py`; read its record schema from the
   code) and convert each complete record to the kit's tower baseline record, checking export, item, reader and artifact
   bindings as far as b04's records carry them (record what they carry and what cannot be checked). Several partition
   journals combine; duplicates or missing items refuse.
4. GPU entry for the run host: a wrapper modeled on `B/parity_kit/gpu_113.sh` (same bwrap binding, env, settings, caches
   under the run directory) plus the kit's `run_card.sh` guards (vnice `/data3/shared/scripts/vnice/vnice.sh`, refuse a card
   with > 1024 MiB used, nice 10), taking CARD, SET (devs1_routed|revsi999), ARMS (own), PARTITION i/n, OUT. Never kill.
5. CPU first batch on the reviewed reader: `h1eval/h10/cpu_first_batch.py` runs one dev-S1 item per routed call type
   (displacement, movement direction, rotation, absolute distance) through the own arm unperturbed plus one registered
   mode per item, on CPU, and writes a receipt (texts, calls served/unserved, timings, finite heads). Give the exact
   commands for 1-13 (inside bwrap, like gpu_113.sh) and for trinity-1-18 (b04's 1-18 host copy
   `/scratch/jjyeung/orch_n30/b04host/b04_e2ehook`, restore `.../parity_kit/host_restore`, env
   `/scratch/jjyeung/envs/vllm/bin/python` + scipy overlay `/scratch/jjyeung/orch_n30/h1_headsft_w/pyoverlay`).
6. Tests (tiny, CPU) for the adapter: signature binding against the real `parity.make_real` signature (inspect, do not
   load weights), own-perception factory with b04's keywords on a tiny Perception, item mapping on the real item files,
   tower-journal conversion on synthetic records in b04's schema, mode application per type, read counts unchanged.
   Rerun the full kit suite (Build 6: 101 passed; files in BUILD_REPORT "Build 6" validation command plus
   tests/test_build6.py); all must pass. Write "Build 7" in BUILD_REPORT.md with files, commands, results, size, and the
   exact run-host commands (CPU first batch, then GPU per partition), with a GUESS of seconds per decode (b04 measured
   ~25-100 s/item on an A6000-class card with SAM 3 in the call).
