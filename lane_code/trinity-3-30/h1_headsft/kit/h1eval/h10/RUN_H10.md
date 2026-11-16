# H1-0 read on a compute node

Check the cluster dashboard, card occupancy, free disk and RAM before launch.
Keep the export, reader, media, environments, caches and outputs on local storage.
The step-544 export, heads, SAM 3, selector and exact 32-frame RGB binding must match
its artifact manifest. Their real sizes and compatibility remain unverified here.
The kit's own grounding adapter requires `model.h10_stage1_socket` or
`model.sam3_tower` plus `model.selector_head`; absent components refuse.

| Set | Own baseline | Own perturbed | Tower baseline | Own reads with tower reuse |
|---|---:|---:|---:|---:|
| dev-S1 routed | 636 | 900 | 636 | 1,536 |
| ReVSI official999 | 999 | 566 | 999 | 1,565 |

Every item has one own baseline. Translation scales 0.5/2 apply only to displacement;
180-degree translation rotation applies only to movement direction; turn negation
applies only to rotation; scene scales 0.5/2 apply only to object absolute distance.
Each tower item has one unperturbed decode. `--tower-from DIR` reuses complete tower
records from b04's parity read; it requires matching export, item-set, item-file,
reader and artifact hashes. DIR must contain `environment.json` with a `binding`
and `items.jsonl` with complete baseline records in the launcher's record format.
An absent binding, changed hash, missing item or perturbed tower record refuses.

```bash
export H10_EXPORT=/dev/shm/jjyeung/exports/m544
export H10_ARTIFACT_MANIFEST=/scratch/jjyeung/h10/E2E_MANIFEST.json
export H10_READER_ROOT=/scratch/jjyeung/b04_reader
export H10_ITEMS="$PWD/items/devs1_routed.json" H10_ARMS=own,tower
export H10_TOWER_FROM=/scratch/jjyeung/b04_parity
bash h1eval/h10/run_card.sh 0 0/1 "$PWD/out/h10"
bash cpu.sh -m h1eval.h10.merge out/h10 --out out/h10_merged
```
Run the card command in compute-node tmux. The wrapper uses nice 10/vnice and
refuses a failed card query or more than 1024 MiB of occupied card memory.
The launcher prints its read plan before decoding and measures its first ten reads.
`projection.json` and the log report card-hours = reads × measured seconds/read / 3600;
model loading is timed separately. No real timing forecast is available from this build.
Resume with identical bindings; completed records are skipped. A torn tail refuses.
For a CPU diagnostic, use `bash cpu.sh -m h1eval.h10.cpu_first_batch --help`.
The reader generates units and number formatting; the launcher never rewrites answers.
