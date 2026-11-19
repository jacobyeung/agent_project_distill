This kit is unsubmitted and GO=false. The capacity fixture and full frozen suite did not complete. The local shell test captures bwrap arguments after staging; it does not qualify a real allocation. Review the build report before using these commands.

Run these commands on the Orchard login host from the extracted delivery root. They write only to N's own pool folder. P's kit and run remain read-only.

```bash
python3 -I -s -B work/build20/upload.py "$PWD" /project/community/jjyeung/okh7/x_90a20c41
mkdir -p /project/community/jjyeung/okh7/x_90a20c41/o
```

After P's export lands, supply `/project/community/jjyeung/okh7/x_90a20c41/g.json`. This is the normalized, offline listing of the four cached GCS parts. Each `objects` entry contains `name`, absolute `pool_path`, integer `bytes`, and `sha256`. Names must occur in order from `q8/8865619b/6ed2c7aa_m400.tar.part00-of-04` through `part03-of-04`. The listed files must already exist within the pool. This build does not download them. The resolver hashes each file and the concatenated stream, then checks P's done marker. No guessed size or hash is accepted.

Supply `metadata` entries with `pool_path`, `bytes`, and `sha256` for each model/tokenizer/config text file absent from P's small archive. The model manifest supplies their expected hashes. The resolver refuses missing metadata. It reads P's `h_6ed2c7aa/m400/{DONE.json,e.json,r.json,s.tar}` and `x_ee227714/o/gcs_6ed2c7aa_m400.done`; it inventories `h.json` and `RP.json` when present. The export-only proof uses `e.json` and `r.json`.

```bash
python3 -I -s -B /project/community/jjyeung/okh7/x_90a20c41/q/b/resolve.py --pool /project/community/jjyeung/okh7 --listing /project/community/jjyeung/okh7/x_90a20c41/g.json --output /project/community/jjyeung/okh7/x_90a20c41/r.json
sbatch --chdir=/project/community/jjyeung/okh7/x_90a20c41/q --output=/project/community/jjyeung/okh7/x_90a20c41/o/%j.log --error=/project/community/jjyeung/okh7/x_90a20c41/o/%j.err /project/community/jjyeung/okh7/x_90a20c41/q/job.sh /project/community/jjyeung/okh7/x_90a20c41/r.json
```

Resource settings come from `kits/q/job.sh` and `kits/q/b/g.py`: general partition, one GPU, eight CPUs, 192 GiB requested memory, twelve hours. Memory and time sizing are GUESS. The GPU guard requires at least 80 GiB reported by CUDA; a nominal 80 GB device can fail that exact check. No real allocation or model fit was tested.

The job validates its seal, stages P's pinned venv/closure/inputs through P's staging functions, stages N's uploads and the export locally, and constructs P's original bwrap path mappings. Its caches and temporary files stay on the allocated node. It runs `b/a.py q`, then runs the room report independently of the proof result.

Read `x_90a20c41/o/JOB/RESULT.json` for `proof_rc` and `rooms_rc`. This wrapper deliberately retains GO=false. The accompanying `o.tar` contains the native `p/q/RESULT.json`, forward receipt when produced, logs, and room report when produced. Only the native admission result establishes ADMIT; shell success or room counts do not. Room cells retain counts and up to twenty example keys under the pinned K1, R0, and withheld-room rules (`proofs/operator/ROOMS.json` records the fixture result).

Seal, path, size, SHA-256, receipt schema, milestone, model metadata, and export-stream mismatches refuse with E-prefixed errors. Native admission keeps its own typed refusals, including capacity and component-evidence gates. `proofs/operator/RESULT.json` lists static pins unavailable here. P's staged pool inputs must resolve those pins, including any runtime-prepared stores; that complete real-input closure has not been verified on this node. A resolver success alone does not certify it.
