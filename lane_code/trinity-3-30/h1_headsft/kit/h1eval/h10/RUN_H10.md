# H1-0 on the reviewed parity reader

The launcher defaults to `e2e_reader.parity:make_real`. `--settings` defaults to
`/scratch/jjyeung/b04shm/b04/host2/b04_e2ehook/parity_kit/settings_bw.json`.
Settings must name the restored export, artifact binding, sealed tree, frame root,
SAM 3 and selector head. The launcher sets `arm=own_depth` and adds the active `H10_OVERLAY` to the
recorded `env_roots`, so audited scipy/library imports use that local overlay. The own factory uses
own pose/gravity/depth at scale one; the tower factory is b04's unmodified
`own_depth` path. The model writes every answer, conversion and numeric format.

| Set | Own baseline | Own perturbed | Tower baseline | Own decodes with tower reuse |
|---|---:|---:|---:|---:|
| devs1_routed | 636 | 900 | 636 | 1,536 |
| revsi999 | 999 | 566 | 999 | 1,565 |

Modes remain type-specific: translation scales 0.5/2 for displacement, 180-degree
translation rotation for movement direction, turn negation for rotation, scene
scales 0.5/2 for absolute distance. Direct types receive baseline reads only.
Each process loads the carrier once per decoded arm and shares SAM/selector
weights across items. Every item receives a new perception/session.

`item_mapping.json` binds each canonical ID to `parity.key`, the native task digest,
anchors, dense metadata digest and count. `sha256` hashes the canonical mapping
list. The carrier layout has count 32. Dev-S1 keeps b04's 567 items with 64 dense
frames and 69 with 32; both have exactly 32 pinned anchors. Generation checks and
loads RGB through `bind_item`; metadata validation does not read images.

ReVSI requires `item_sets.revsi999` overrides in the settings JSON for `tasks`
(a list of JSONL files), `frames_json`, `dense_manifest` and `frames_root`.
Native tasks must retain official IDs, question, question_type, options, dataset,
scene and answer, and add `native` and `room`. Captures must contain the same
32-anchor records, source indices, hashes, timestamps, fps and total-frame count
that b04's `bind_item` requires. Dense captures add `anchor_slots` and indexed,
hashed frames. RGB files must exist at those relative paths under `frames_root`.
Without these inputs the run refuses with `frames not staged`; dev-S1 clips are
never substituted. The generic staged-ReVSI test uses a synthetic binding and
establishes no official ReVSI RGB coverage.

`--tower-from DIR` accepts a b04 run root containing
`gpu_results/own_depth_p*/{items.jsonl,LOAD_RECEIPT.json}`, the `gpu_results`
directory itself, or one complete partition directory. All partition receipts
must agree except selection keys and frame counts. Every selected partition and
the complete registered item set must be covered; duplicates, torn lines, missing
items and changed bindings refuse. The converter verifies row provenance,
restore pins, artifact binding, native task/metadata pins, perception settings,
reader/runner code and decode-policy pins. It preserves the model's text and
calls in the kit's tower baseline records. b04 does not carry the kit's item-set
hash; native task pins and keys provide that binding. Conversion checks recorded
model identity and does not rehash weight payloads. Tower runtimes must agree
with one another; they need not equal the own runtime. The legacy kit journal
format with `environment.json` is also accepted under its existing hash checks.

Run these commands from an existing compute-node session. The complete kit and
b04 inputs must already be staged at the stated paths. This build stages nothing
on another host. Check allocation, occupancy and local RAM before launch. Use
compute-node tmux for real reads. The GPU wrapper performs one occupancy query,
refuses more than 1024 MiB, and runs under vnice plus nice 10. It never retries or
kills. Caches and temporary files stay under OUT. CPU diagnostics hide CUDA and
use 16 threads. The GPU wrapper does not impose a virtual-address cap because
CUDA reserves large address ranges; CPU build tests use the 32 GiB cap in cpu.sh.

On trinity-1-13, the wrapper enters the same bwrap view as b04:

```bash
K=/scratch/jjyeung/orch_n30/h1_headsft/kit
bash "$K/h1eval/h10/gpu_113.sh" cpu devs1_routed own 0/1 "$K/tmp/b7/cpu113"
```

This is equivalent to invoking the CPU first batch inside:

```bash
bwrap --dev-bind / / --bind /dev/shm/jjyeung /scratch/jjyeung/b04shm \
  bash "$K/h1eval/h10/host_run.sh" cpu devs1_routed own 0/1 "$K/tmp/b7/cpu113"
```

The wrapper uses `/scratch/jjyeung/envs/vllm/bin/python -B`, overlay
`/scratch/jjyeung/b04shm/b04/pyoverlay`, b04 host2 `settings_bw.json`, and its
`restore_bw` export. It does not run b04's restore or manifest builder.
`FIRST_BATCH.json` contains eight decodes: baseline and one registered mode for
each routed type, with exact texts, served/unserved calls, load/decode timings,
interventions and finite pose/gravity/depth checks. A failed read retains the
partial receipt and error. It is a diagnostic, not a resumable benchmark shard.

After the CPU receipt passes, use an assigned card. These are separate commands,
not an automatic chain; do not restart a killed job without the user's answer.
For paired records, set `H10_TOWER_FROM` before the first GPU launch to b04's
complete run root, for example the path below. Omit it for an own-only journal.
The binding cannot change during resume.

```bash
export H10_TOWER_FROM=/scratch/jjyeung/b04shm/b04/host2/b04_e2ehook/parity_kit
CARD=${ORCH_CARD:?Set the assigned card index}
bash "$K/h1eval/h10/gpu_113.sh" "$CARD" devs1_routed own 0/3 "$K/tmp/b7/devs1_p0"
bash "$K/h1eval/h10/gpu_113.sh" "$CARD" devs1_routed own 1/3 "$K/tmp/b7/devs1_p1"
bash "$K/h1eval/h10/gpu_113.sh" "$CARD" devs1_routed own 2/3 "$K/tmp/b7/devs1_p2"
```

The complete tower journals must exist before these paired commands. `ARMS=own`
controls new decodes; `H10_TOWER_FROM` adds reused tower records. For ReVSI, use
`SET=revsi999` and separate outputs after its frames and native tasks are staged;
a paired run also needs complete ReVSI tower journals. The 636 dev-S1 journals
cannot serve as the ReVSI baseline.

On trinity-1-18, use the local b04 copy and scipy overlay:

```bash
K=/scratch/jjyeung/orch_n30/h1_headsft/kit
export H10_READER_ROOT=/scratch/jjyeung/orch_n30/b04host/b04_e2ehook
export H10_SETTINGS=$H10_READER_ROOT/parity_kit/settings.json
export H10_EXPORT=$H10_READER_ROOT/parity_kit/host_restore
export H10_PY=/scratch/jjyeung/envs/vllm/bin/python
export H10_OVERLAY=/scratch/jjyeung/orch_n30/h1_headsft_w/pyoverlay
bash "$K/h1eval/h10/host_run.sh" cpu devs1_routed own 0/1 "$K/tmp/b7/cpu118"
CARD=${ORCH_CARD:?Set the assigned card index}
bash "$K/h1eval/h10/host_run.sh" "$CARD" devs1_routed own 0/3 "$K/tmp/b7/devs1_118_p0"
bash "$K/h1eval/h10/host_run.sh" "$CARD" devs1_routed own 1/3 "$K/tmp/b7/devs1_118_p1"
bash "$K/h1eval/h10/host_run.sh" "$CARD" devs1_routed own 2/3 "$K/tmp/b7/devs1_118_p2"
```

b04's status describes the 1-18 settings with `sam3: null`. Such settings refuse
before model loading. Stage SAM 3 source/checkpoint/receipt and the selector,
include their code/data pins in the artifact, and supply a settings JSON with
those local paths via `H10_SETTINGS`. The 1-13 bwrap paths cannot substitute for
missing 1-18 files. No real-host settings were available for inspection here.

Resume a benchmark with the identical command and bindings. The launcher skips
completed tuples and preserves a torn tail by refusing. After ten decodes it
writes `projection.json` with measured seconds/read and projected card-hours,
excluding model load. Merge complete disjoint partitions with the existing
M1–M4 evaluator:

```bash
cd "$K"
LANE_TEST_OUTPUT="$K/tmp/b7" bash cpu.sh -m h1eval.h10.merge \
  "$K/tmp/b7/devs1_p0" "$K/tmp/b7/devs1_p1" "$K/tmp/b7/devs1_p2" \
  --out "$K/tmp/b7/devs1_merged"
```

**GUESS:** 25–100 seconds/decode on an A6000-class card with SAM 3. That is
10.7–42.7 card-hours for 1,536 dev-S1 own decodes and 10.9–43.5 for 1,565 ReVSI
own decodes, before loading. b04's status also records call-heavy items taking
up to 430 seconds. Use the measured projection rather than treating this range
as a deadline guarantee. No real-weight timing was measured by this build.


## H1-1 mid-leg development reads

At both m100 and m200, read dev-S1 under its registered plan and read the pinned
`items/r0dev.json` (`r0dev_f32`) as a separate own-arm baseline. Use all nine R0
types and `--modes none`; do not supply `--types`. Keep separate journals and
curves. R0-dev is development only and remains excluded from every training
stream; never append it to ReVSI or another official set.

The CLI accepts `h1eval.cli items build --sets r0dev` (or `r0dev_f32`) and
`h1eval.cli run --items items/r0dev.json --arms own --modes none` with the usual
export/output arguments. The reviewed H1-0 launcher accepts the same item file,
`--arms own --modes none`, and its usual export, artifact, reader and settings
arguments. Its settings must provide `item_sets.r0dev_f32.frames_root` with the
verified f32 frames. The Orchard package dispatches it through an opaque entry;
do not expose these descriptive CLI arguments on Orchard.

Every R0 report prints per-type accuracy/MRA beside the pinned b10 f32
no-information value and separate unserved/error call rates. The package's
optional last phase requires the missing frames archive and the time guard;
see `orchard_h10/OPERATIONS.md`. This build executes no milestone read.
