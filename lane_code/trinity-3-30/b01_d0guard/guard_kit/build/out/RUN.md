# Operator run sheet

**NOT READY.** `packet.py packet` intentionally refuses to emit a batch while integration is incomplete. The commands below define the intended operator interface. They do not authorize upload or submission. Read `RELEASE_BLOCKERS.json` first.

The candidate metadata manifest must contain pinned config, data_receipt, preparation, source_seal and inventory files. The candidate closure is absent from the supplied inputs. Never substitute the accepted training metadata.

Local validation:
```sh
cd /scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/build
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B out/tests/test_g1.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B out/tests/test_stage.py
```

New-object upload commands, held until release blockers and independent review are resolved:
```sh
gcloud storage cp /scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/build/out/code_g1.tar gs://cmu-gpucloud-jjyeung/q8/8c9d2e74/c_dab2e6fb06fa7685.tar
gcloud storage objects describe gs://cmu-gpucloud-jjyeung/q8/8c9d2e74/c_dab2e6fb06fa7685.tar --format=json
gcloud storage cp /scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/build/out/inputs_g1.tar gs://cmu-gpucloud-jjyeung/q8/8c9d2e74/i_880b6ac41bdeddea.tar
gcloud storage objects describe gs://cmu-gpucloud-jjyeung/q8/8c9d2e74/i_880b6ac41bdeddea.tar --format=json
```

Cloud generations remain `PENDING_UPLOAD` in `FAMILY.json`. Record actual generation, size and digest, reseal the family and obtain review on that family. Do not replace a placeholder without checking uploaded bytes.

Orchard neutral-copy commands are copied verbatim below from `NAMING.md`:

```sh
mkdir -p /project/community/jjyeung/okh7/8c9d2e74
cp -- /project/community/jjyeung/cp4tk_rt/kit/model_qwen35_9b_c2022362.tar /project/community/jjyeung/okh7/8c9d2e74/ab626354ad7ea9b9
sha256sum -- /project/community/jjyeung/cp4tk_rt/kit/model_qwen35_9b_c2022362.tar /project/community/jjyeung/okh7/8c9d2e74/ab626354ad7ea9b9
# Required SHA256: 20a2ab6c54e22baba2c6b9065a7c0df24a9fe60a867fb078a017859dac2fdaca
cp -- /project/community/jjyeung/distill/okit/in/c_fa8681cba4c0.tar /project/community/jjyeung/okh7/8c9d2e74/3f4e9154ba1f2066
sha256sum -- /project/community/jjyeung/distill/okit/in/c_fa8681cba4c0.tar /project/community/jjyeung/okh7/8c9d2e74/3f4e9154ba1f2066
# Required SHA256: fa8681cba4c02d789bc60c09fac7a05936c5b1fde81d53f77830294ea7e7895c
cp -- /project/community/jjyeung/distill/okit/in/cr/436d1d64673f.p00 /project/community/jjyeung/okh7/8c9d2e74/8f38e81ca7758e70
sha256sum -- /project/community/jjyeung/distill/okit/in/cr/436d1d64673f.p00 /project/community/jjyeung/okh7/8c9d2e74/8f38e81ca7758e70
# Required SHA256: fd60ac2f525727836258ae7ea0705ff3a49163ae74320f7bf8a17b66cd69f0c7
cp -- /project/community/jjyeung/distill/okit/in/cr/9b9e03337df5.p00 /project/community/jjyeung/okh7/8c9d2e74/9bda75a7077ab157
sha256sum -- /project/community/jjyeung/distill/okit/in/cr/9b9e03337df5.p00 /project/community/jjyeung/okh7/8c9d2e74/9bda75a7077ab157
# Required SHA256: 07c2d3b0358fd6f16e014f4a155bee6de921e6723a5b9633d08d0fb71e8fad39
cp -- /project/community/jjyeung/distill/okit/in/cr/c449bbe907be.p00 /project/community/jjyeung/okh7/8c9d2e74/2206733a423ef6ba
sha256sum -- /project/community/jjyeung/distill/okit/in/cr/c449bbe907be.p00 /project/community/jjyeung/okh7/8c9d2e74/2206733a423ef6ba
# Required SHA256: 0482359088665775014cb46c10f6d87a6f99c4203a978b6b6d1a74a50155438d
cp -- /project/community/jjyeung/distill/okit/in/d00 /project/community/jjyeung/okh7/8c9d2e74/cb81e2210d956d4a
sha256sum -- /project/community/jjyeung/distill/okit/in/d00 /project/community/jjyeung/okh7/8c9d2e74/cb81e2210d956d4a
```


Milestone commands on Orchard after the missing metadata is staged under the neutral pool. Every token below is distinct (`OPERATOR_TOKENS.json`). Each destination must be fresh. These draft prepare/packet calls cannot produce a runnable batch in the current release.
```sh
cd /project/community/jjyeung/okh7/8c9d2e74/g1
# Candidate m200; commands remain blocked by this family.
/usr/bin/python3 -I -s -B guard_kit/packet.py prepare --family FAMILY.json --done /project/community/jjyeung/okh7/x_f5c353f7/o/gcs_359fcc3c_m200.done --step 200 --metadata /project/community/jjyeung/okh7/8c9d2e74/m200_meta.json --token 099e158c500659d9 --out plans/099e158c500659d9
/usr/bin/python3 -I -s -B guard_kit/packet.py packet --config plans/099e158c500659d9/CONFIG.json --review REVIEW.json --order ORDER.md --out packets/099e158c500659d9
# After a completed, reviewed packet builder exists:
# sbatch --partition=general --gres=gpu:1 --ntasks=1 --nodes=1 --cpus-per-task=16 --mem=200G --time=05:00:00 --job-name=a15_cot_ap099e158c500659d9 packets/099e158c500659d9/BATCH.sh
# Candidate m400; commands remain blocked by this family.
/usr/bin/python3 -I -s -B guard_kit/packet.py prepare --family FAMILY.json --done /project/community/jjyeung/okh7/x_f5c353f7/o/gcs_359fcc3c_m400.done --step 400 --metadata /project/community/jjyeung/okh7/8c9d2e74/m400_meta.json --token d53b20095bf873de --out plans/d53b20095bf873de
/usr/bin/python3 -I -s -B guard_kit/packet.py packet --config plans/d53b20095bf873de/CONFIG.json --review REVIEW.json --order ORDER.md --out packets/d53b20095bf873de
# After a completed, reviewed packet builder exists:
# sbatch --partition=general --gres=gpu:1 --ntasks=1 --nodes=1 --cpus-per-task=16 --mem=200G --time=05:00:00 --job-name=a15_cot_apd53b20095bf873de packets/d53b20095bf873de/BATCH.sh
# Candidate m600; commands remain blocked by this family.
/usr/bin/python3 -I -s -B guard_kit/packet.py prepare --family FAMILY.json --done /project/community/jjyeung/okh7/x_f5c353f7/o/gcs_359fcc3c_m600.done --step 600 --metadata /project/community/jjyeung/okh7/8c9d2e74/m600_meta.json --token 7a1829105e08b53b --out plans/7a1829105e08b53b
/usr/bin/python3 -I -s -B guard_kit/packet.py packet --config plans/7a1829105e08b53b/CONFIG.json --review REVIEW.json --order ORDER.md --out packets/7a1829105e08b53b
# After a completed, reviewed packet builder exists:
# sbatch --partition=general --gres=gpu:1 --ntasks=1 --nodes=1 --cpus-per-task=16 --mem=200G --time=05:00:00 --job-name=a15_cot_ap7a1829105e08b53b packets/7a1829105e08b53b/BATCH.sh
# Candidate m800; commands remain blocked by this family.
/usr/bin/python3 -I -s -B guard_kit/packet.py prepare --family FAMILY.json --done /project/community/jjyeung/okh7/x_f5c353f7/o/gcs_359fcc3c_m800.done --step 800 --metadata /project/community/jjyeung/okh7/8c9d2e74/m800_meta.json --token 3297624c6ddfd509 --out plans/3297624c6ddfd509
/usr/bin/python3 -I -s -B guard_kit/packet.py packet --config plans/3297624c6ddfd509/CONFIG.json --review REVIEW.json --order ORDER.md --out packets/3297624c6ddfd509
# After a completed, reviewed packet builder exists:
# sbatch --partition=general --gres=gpu:1 --ntasks=1 --nodes=1 --cpus-per-task=16 --mem=200G --time=05:00:00 --job-name=a15_cot_ap3297624c6ddfd509 packets/3297624c6ddfd509/BATCH.sh
# Candidate m1000; commands remain blocked by this family.
/usr/bin/python3 -I -s -B guard_kit/packet.py prepare --family FAMILY.json --done /project/community/jjyeung/okh7/x_f5c353f7/o/gcs_359fcc3c_m1000.done --step 1000 --metadata /project/community/jjyeung/okh7/8c9d2e74/m1000_meta.json --token cf1dc1c8193461eb --out plans/cf1dc1c8193461eb
/usr/bin/python3 -I -s -B guard_kit/packet.py packet --config plans/cf1dc1c8193461eb/CONFIG.json --review REVIEW.json --order ORDER.md --out packets/cf1dc1c8193461eb
# After a completed, reviewed packet builder exists:
# sbatch --partition=general --gres=gpu:1 --ntasks=1 --nodes=1 --cpus-per-task=16 --mem=200G --time=05:00:00 --job-name=a15_cot_apcf1dc1c8193461eb packets/cf1dc1c8193461eb/BATCH.sh
```

No batch file exists and no sbatch command is currently runnable. Resources belong on the command line. Input tars must have no hard-link members; the new archives pass this check (`CODE_MANIFEST.json`, `INPUT_MANIFEST.json`). Existing large Orchard archives were unavailable for inspection.

Governed fetch, held for the operator:
```sh
# Run on Trinity; registration must succeed before opening any stream.
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /data3/jjyeung/orch_n13_20261026/io_governor/register.py --tier 3 --allow-resume
# Then use the governor-issued stream command for the published return object.
# Intended source: gs://cmu-gpucloud-jjyeung/q8/8c9d2e74/<token>/result.tar.gz
# Intended destination: /scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/build/out/fetched/<token>/result.tar.gz
```

The named governor script is absent on this node. Its remaining CLI arguments and the new return publisher are not validated, so this sheet does not invent a runnable governed stream. Fetch only after registration and verify the return receipt size and SHA256. No fetch ran here.

Ledger line format for `work/ORCHARD_LEDGER.jsonl` (append only after actual submission; never record a draft as submitted):
```json
{"utc":"<UTC>","job":"<actual Orchard job>","token":"<fresh hex>","step":"<candidate step>","run":"359fcc3c","done_object":"<exact object>","done_bytes":"<whole tar bytes>","done_sha256":"<whole tar SHA256>","family_sha256":"<reviewed family SHA256>","plan_sha256":"<sealed plan SHA256>","status":"SUBMITTED","order_sha256":"<exact ORCH order SHA256>"}
```
