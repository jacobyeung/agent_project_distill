The Orchard packet is an unlaunched candidate. Its family retains the C8r base/runtime/trainer/export provenance and return locations, replaces the evaluation assets, and omits the old mask/geometry/cohort contract. The packet is not certified launch-ready; see `out/FAMILY.json` and `out/UNEXECUTED.md`.

Build a local packet after preparing the new assets:

```bash
cd /scratch/jjyeung/orch_n30/native_r4/builds/01_vsti
./work/py code/venue.py packet --family out/FAMILY.json --assets out/ASSETS.json --out work/operator_packet --token 3917ab0dd64f429ac1e708fb
```

The batch file is submitted only from the authorized Orchard environment after local assets have been staged there. The asset manifest must contain Orchard-local source paths; use `venue.py stage` there to extract the same pinned archives. The large assets and export must already be present. This build performs no network operation and has not produced a generation-pinned cloud upload manifest.

```bash
export READ_CODE=/tmp/r01/code
export READ_CONFIG=/tmp/r01/packet/CONFIG.json
export READ_ASSETS=/tmp/r01/stage/ASSETS.json
export READ_ROOT=/tmp/r01/job
sbatch --account=mt01 --partition=general --gres=gpu:1 --time=07:00:00 /tmp/r01/packet/BATCH.sh
```

These exact paths describe the required staged layout; they do not assert that those files already exist. The worker runs the same `entry.py job` path and uses the inherited return publisher. The bound full allowance is stored in `out/FAMILY.json`. The return pool is `/project/community/jjyeung/okh7/n2r/<token>` and the GCS prefix is `gs://cmu-gpucloud-jjyeung/q8/n2r/<token>/`.

For a canary-only run or multiple cards, invoke the commands in `out/RUN_TRINITY.md` through `entry.py` in the staged namespace. Use one shared geometry manifest, a passed canary receipt, and separate shard output folders. Merge and report with those same bound inputs and geometry pins. The selected historical proof keys are `out/PROOF_KEYS.json`; its runner remains separate from this corpus.

Not completed: generation-pinned cloud asset publication, Orchard namespace rehearsal, remote return tests, and GPU parity. The packet refuses missing local assets; it is not a drop-in replacement accepted by the unmodified C8r launcher validator.
