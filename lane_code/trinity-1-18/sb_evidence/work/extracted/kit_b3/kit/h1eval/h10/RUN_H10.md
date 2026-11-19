# H1-0 on trinity-1-13

Run only after the cluster dashboard and local card checks permit it.
Stage once; keep data, environments, caches and outputs on local storage.

| Input | Location / size |
|---|---|
| Step-544 export | Already `/dev/shm/jjyeung/exports/m544`; bytes unverified here; 9B BF16 parameters alone are about 18 GB |
| `heads.pt` | Step-544 stop export; bytes and SHA256 must come from its pinned manifest |
| SAM 3 | Frozen checkpoint, source and receipt; bytes unverified; use artifact-listed sizes |
| Selector `run_raw` | Selector weights/config; bytes unverified; use artifact-listed sizes |
| RGB frames | Exact 32-frame/media binding for the selected set; bytes unverified; use artifact-listed sizes |
| Kit code/data | About 21.7 MB excluding tests, logs, tmp and checksum index; copy auth, tree, rows, configs, items, items_sources, h1eval and cpu.sh |
| b04 reader | Published `e2e_reader.real:make_real`; size unverified; stage its required dependencies |

First check export/head/manifest hashes, step 544, frame layout, R0 pins, free disk and RAM.
The artifact must bind heads, media, SAM and selector; make_real owns loading and decoding.
Own grounding needs `model.h10_stage1_socket` or `model.sam3_tower` plus `model.selector_head`.
This binding is unverified with b04; absent bindings refuse instead of substituting geometry.
Run `bash cpu.sh -m h1eval.h10.cpu_first_batch --export "$H10_EXPORT" --heads "$HEADS" --artifact-manifest "$H10_ARTIFACT_MANIFEST" --reader-root "$H10_READER_ROOT"` only where the real weights fit the 32 GiB cap.
Check its move, turn, ground/gap records, finish reasons, times and unchanged model responses.

```bash
export H10_EXPORT=/dev/shm/jjyeung/exports/m544
export H10_ARTIFACT_MANIFEST=/scratch/jjyeung/h10/E2E_MANIFEST.json
export H10_READER_ROOT=/scratch/jjyeung/b04_reader
export H10_ITEMS="$PWD/items/devs1_routed.json"
export H10_ARMS=own,tower H10_MODES=scale_translation:2,rotate_translation:90,negate_turn,scale_scene:2
bash h1eval/h10/run_card.sh 0 0/4 "$PWD/out/h10/card0"
bash h1eval/h10/run_card.sh 1 1/4 "$PWD/out/h10/card1"
bash h1eval/h10/run_card.sh 2 2/4 "$PWD/out/h10/card2"
bash h1eval/h10/run_card.sh 3 3/4 "$PWD/out/h10/card3"
bash cpu.sh -m h1eval.h10.merge out/h10/card{0,1,2,3} --out out/h10/merged
```
Run each card command in its own compute-node tmux session; vnice stays in the foreground.
The script checks >1024 MiB busy memory, applies nice 10/vnice and writes `<out>/log`.
Defaults yield 6,360 reads: expected card-hours = 1.767 × measured seconds/read, plus loading.
At an assumed 60 s/read: 106 card-hours, roughly 26.5 hours on four cards; this is not a measured forecast.
Resume with the identical command; changed bindings refuse. A torn JSONL tail requires a fresh output directory.
Tower remains unperturbed for every mode. Donor/GT require explicit Python factory_options; the CLI refuses unbound inputs.
