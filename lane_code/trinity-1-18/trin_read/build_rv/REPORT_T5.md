# Trinity paired direct-read build

The runner supports parent CP1 m200 and f17 weights on the 636 selected dev-S1 keys. Both use the e193 step-544 duplicate cell, 32 anchors, true timing, greedy ON16k, B2048 decision arm, B4096, and the unchanged answer-cap policy. All 161 CPU tests pass (`TESTS_T5_FINAL.log`), including the existing 134 cases. Two existing assertions now account for the fourth family and expanded runner bundle; no existing test was removed.

## Model and packet contract

`read --model-slot cp1m200|f17` reads the SHA-pinned staged camera `models.json`. The parent uses the unchanged c1 export checker at step 200. f17 uses its full-file archive SHA256 and the unchanged kit `stage.prepare()`. The logical paths map to `root/fsw/ap/f2ad01ad/runs/49becb79/m200/artifact.json` and `root/m/ap/bdad3598/k/f17.tar`. Both use base manifest SHA256 `ae9247f7c316e7661bfbe4301c28d75b6871db7427d675b8e1cc4c0c41b4b252`.

The request's `cp1m200` name is the protocol slot. `SPEC.json.model_identity` identifies the actual weights; `cell_used` records the cell used. f17's spread cell is never selected. The bridge rejects any change to the e193 cell, timing/payload pins, engine settings, or copied kit source digest. The packet retains the accepted per-family directory structure. Each 636-item read comprises a 186-item main packet and a 450-item camera packet.

The runner bundle uses `root/trinity_runner_t5/`. No bundle was installed during this session. The fixture mode writes only in build_t5 and cannot launch a model. Production remains gated by the orchestrator's GO and staging/frame/proof prerequisites.

## Keys and frames

`KEYS636_main.ids` comes from e193 `direct/main/results/0/budget_2048.jsonl`: exactly 150 `object_abs_distance` and 36 `room_size_estimation` IDs. `KEYS636_camera.ids` contains exactly 450 camera IDs, 150 per task. Tests compare both lists to e193 and validate camera TASKS SHA256 `f59090ffc8fd0f4d80a2b049e2624660c0f46dbc1d26016145f4747850a432ac` through the pinned adapter.

| Selection | Items | Unique frames | RGB estimate, bytes |
|---|---:|---:|---:|
| Main subset | 186 | 2,304 | 2,123,366,400 |
| Camera | 450 | 1,664 | 1,533,542,400 |
| Union | 636 | 2,688 | 2,477,260,800 |

The lists were generated with `need --fixture`, which calls the actual bind, task-selection, and payload functions with tensor/processor dependency fixtures. Camera contributes 384 frames beyond the selected main subset. It contributes **zero extra frames beyond `work/NEED_X27.txt`**. The estimate sums uncompressed RGB dimensions; actual PNG/tar transfer sizes were not measured. `NEED636.txt`, the per-family lists, and `NEED636.json` contain the results.

## CPU binding comparisons

No file named `camera_leg.py` was found in build, root, dl, kit_src, or evalx27 by the local filename search; there was no candidate to match SHA256 `487570aea8c47ba65faf380b7e5e215707ff6091e8afe39c9f500f68a76edd7f`. Large runtime/model archives were not scanned for embedded source. The reconstruction uses the available pinned camera package and the camera argv, code pins, request, and bind/layout logs in e193. It does not claim byte identity with the lost wrapper.

All six family/model combinations pass. `BIND_PARITY_T5.json` records the comparisons, and `tests/t5_final/e193_binds0/` retains their packets and reconstructed comparison files. The same-family cp1m200 and f17 requests differ from the step-544 fixture only in model identity fields and the resulting binding, after normalizing the fixture output directory. Their prompt files and normalized frame indexes are byte-identical.

The dry step-544 request becomes byte-identical to e193 after these explicitly checked substitutions:

| Field | Reason |
|---|---|
| `binding` | Digest changes with paths, dry state, and wrapper provenance. |
| `build_only` | A dry bind must remain non-executable. |
| `datasets[0].rows.path`, `devs1.payload` | Read-only local fixture paths; content pins stay identical. |
| `devs1.frames_root`, `roots.video_root`, `output` | Local frame destination, identity-only video root, and output directory. |
| `legs1.export_bytes_verified`, `legs1.export_verification` | Dry binding does not hash model weights. |
| `camera_leg.wrapper_sha256` | Identifies the reconstructed wrapper, only for camera. |
| `trinity_binding` | Adds the actual wrapper and accepted-contract SHA256 pins. |

Model substitutions additionally change `models.cp1m200.{kind,path,sha256}`, `legs1.artifact.{path,sha256}`, and `legs1.{step,name}`. The production worker also records `trinity_selection`, sets main `smoke_items` to 186, marks the request executable after verification, and recomputes its binding. These production transitions are not represented as an exact e193 request match.

`PROMPT_PINS.json` matches e193 byte-for-byte for each complete family, including the full main prompt inventory emitted by the unchanged binder. The main execution selection remains 186 items.

The comparison reconstructs receipt JSON from the real task/capture metadata and inserts e193's recorded pixel digest from each B2048 result row. Every reconstructed receipt hash matches the accepted frame-index entry. Camera `comparison/frames/0.json` matches all e193 bytes. Main matches after retaining only the 186 selected item entries and updating `decodes` to their distinct receipts. The comparison uses the accepted video identity root and binding; production relocation changes those identities and receipt paths/hashes. **Pixel hashes were reused as reference evidence, not measured from Trinity PNGs.** Comparison indexes stay outside executable `direct/<family>/frames/` directories.

## Disk reserve

The authenticated base manifest totals 19,329,302,904 bytes. Model estimates use the requested ~21.6 GB parent export and ~20.2 GB f17 tar/extracted tree. Actual model sizes are unavailable because these inputs are not staged.

| Per-family packet | Additional reserve, decimal GB |
|---|---:|
| Parent main | 47.324 |
| Parent camera | 46.144 |
| f17 main | 66.146 |
| f17 camera | 64.967 |

Each reserve includes a base copy, model storage, twice the RGB estimate for pulled tar plus PNG tree, and 2 GiB of working space. The archive reserve includes both the retained extraction and copied weights, plus a conservative base-metadata allowance. The already-staged input tar consumes a separate ~20.2 GB; current free space already reflects it. All four retained packets require an estimated 224.581 GB additional space, so the initial free space must be about 439.329 GB to retain the 200 GiB floor, excluding other concurrent growth.

At production admission, c1 sizes come from authenticated manifests. Archive sizes come from uncompressed tar member headers after the full SHA check; unsafe members are refused. `DISK_T5.json` contains the arithmetic. Tests exercise both reserve paths and confirm that the unchanged archive preparer retains the extraction and copied weights.

## Unverified work and open risks

- `runtime_0` and its uv interpreter are absent; STAGING also lists runtime_2 and base as missing. No real namespace `need` or `selfcheck` ran. Fixture imports are not a substitute for a real staged CPU bind.
- Parent CP1 m200 and f17 model paths are absent. Full model-byte checks, base compatibility on real weights, and actual reserve sizes remain unverified.
- No PNG ingestion, real frame cache, GPU execution, or token parity ran. The inherited step-544 20-item proof remains pending. Model outputs must not be treated as paired production results before these checks and the orchestrator's GO.
- The camera wrapper is reconstructed. Its CPU contract/receipt checks pass; execution through the real staged runtime is still required.
- Production uses the imported llguidance stub and private namespace from the existing runner. The inherited runtime compatibility and GPU-proof limits still apply.

Only build_t5 was edited. No GPU, SSH, network, Git, download, deletion, heavy-I/O command, or production stage/frames/proof/read ran. `INPUT_PINS_T5.json` identifies the read-only evidence used.
