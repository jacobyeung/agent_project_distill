# Codex build 2: finish the Orchard package for K1 phase `own` on the orchestrator's rulings (prepare only; submit nothing)

Model gpt-6-astra, effort high. The rules of BRIEF.md in this workspace still hold: write only here, no Git, ssh, network, GPU, kill or deletion, bounded reads, nice and one thread. Read BRIEF.md, your REPORT.txt and STATUS.json first; this build continues them in the same workspace /scratch/jjyeung/orch_n30/k1_ops3/work/partb/build/. The orchestrator's rulings are in /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/k1_ops3/20261116T0534Z_ORCH_RULING_part_b_four_points.md; read it whole. It decides.

## Rulings to implement
(a) Manifest v2 (amendment 2). Write make_manifest_v2.py:
   - Input: manifest 91a2dbf9 (path in BRIEF.md). Fill ONLY gpu.config and gpu.data_receipt with {path, sha256} pins. The paths are the fixed in-namespace paths where the job stages the two files.
   - Assert that every other key is equal to v1 under canonical JSON: all 300 capture entries, gpu.artifact, every other gpu key, and every top-level key.
   - Print the diff of the two values and v2's sha256. Write v2 under manifest_v2/ here.
   - The orchestrator records v2's sha in the amendment. Do not write outside the workspace.
(b) Pins: the prepared config and data receipt that the accepted native read used (C8r FAMILY.json worker_contract):
   - config: .../runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/config.json, sha 78341acb36ffd03b9cec6de65effc9fafcbe8bccdc1dfb43e9da7bd88af47560.
   - data receipt: .../runs/469ddece/inputs/data_receipt.json, sha ebc2983ef7ba33e2e77f4435fff7a031b633a449ef9311622ecab653ea759f40.
   Both are members of the metadata tar gs://cmu-gpucloud-jjyeung/q8/8865619b/evalx_native/metadata_e10fbb95487f3baf.tar (sha e10fbb95487f3bafc379f99ac42668f94ac4c479129d8631d63750112cab3266; FAMILY.json assets.small_objects[1]). Stage it in-job as C8r does.
   A local copy is arriving at /scratch/jjyeung/orch_n30/k1_ops3/work/partb/meta/e10fbb95.tar through a governed stream. If it is absent or the wrong size, poll every 2 minutes for up to 30 minutes; then continue with everything else and report the gap. Verify its sha before use.
   The job must run read_runtime.prepared on these pins and stop unless config identity 84ea03af... matches artifact 1d6eeb28..., exactly as the native read does. Rehearse that check on CPU with the real files and the real artifact JSON (/scratch/jjyeung/orch_cd/evalx/inbox/20261114T141906Z_cp2_m544_artifact.json).
(c) Names: immutable internal paths inside the job's namespace are exempt (for example /scratch/jjyeung/k1_frames/..., own.npz, the kit's absolute source paths). Everything Slurm, the filesystem outside the namespace, the pool, GCS and the logs can show stays opaque. List every exempt path pattern in REPORT.txt, and grep your own job script, arguments, environment, pool and GCS names and log names for forbidden words; report the result.
(d) Namespace rehearsal on trinity-1-3. You cannot ssh; I run it. Produce:
   - rh/RH_1_3.tar: everything the rehearsal needs, laid out to extract under /scratch/jjyeung/orch_n30/k1_partb_rh/ on trinity-1-3. That means the source bundle, the fixture, stand-ins for GCS and the pool, and the CPU interpreter. 1-3 has no copy of our envs, so include /scratch/jjyeung/envs/p1cpu and the uv-python base it links to, /scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu, bound at their logical paths by bwrap. Keep the tar under 3 GB.
   - rh/run_rh.sh: it runs there with `cd /scratch/jjyeung/orch_n30/k1_partb_rh && bash run_rh.sh`, writes only under that folder, and ends by writing out/RH_RESULT.tar (results, coverage, logs), which I copy back.
   - The same run_rh.sh must also run here up to the bwrap step, as far as bwrap allows; show that.
## Also finish
1. The batch entrypoint and job script, in the native kit's form. In order it does:
   - pool write test and free-space print;
   - staging of the export parts, anchor tar, metadata tar, base snapshot and the code bundle;
   - namespace setup;
   - verify_sources, the prepared check, check_manifest(v2,'own'), and the BINDING comparison with tower_sam's;
   - root restore (resume snapshot) and the computed --max-seconds;
   - run_k1-equivalent invocation of k1_pipeline.py cache --phase own;
   - canary: after three captures, write their seconds and generated-token counts into the return (pool and GCS) BEFORE the job continues; on a canary failure, STOP;
   - snapshot and return at the end.
   For the token counts, use the least invasive read-only way (for example, the journal, or an observer that returns the decode result unchanged). Changing no kit file and no source_identity member, explain it for the reviewer.
   The code bundle goes up to GCS under an opaque object name that you choose (I upload it as a governed stream); print the upload size and sha.
2. A full CPU rehearsal here of every line the job runs except the GPU decode (fixture boundary for own), using the real metadata files for the prepared check. Give coverage per file and the list of lines no rehearsal executes (here or on 1-3).
3. REPORT.txt rewritten for this state (no-archaeology): the v2 script and its output diff; the diff against C8r's wrapper files; the exempt paths; the rehearsal output; the unexecuted lines; the exact submit command (do not run it); the fetch command for the return; the uploads I must make (objects, sizes, shas); and the job-count table using native_r3's measured rate:
   - about 0.046 s per sampled token (20.6-22.5 tok/s with light tools; 5.6 tok/s ground-heavy);
   - prompt about 4,700 tokens;
   - full 16,384 tokens is about 780 s per capture, about 65 GPU-h;
   - the native read's items stayed at or under 2,175 generated tokens.
