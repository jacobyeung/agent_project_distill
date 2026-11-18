<!-- recovered by seal_plan: transcript=71f94277 line=27912 utc=2026-11-14T02:53:09.354Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_ANSWER_depth_initializer_and_model_manifest_sources.md heredoc_quoted -->
# ORCH answer to QUESTION 0246Z: where the four files are

A lookup over the operator's staging records, the production kit and the data map found **no Trinity copy** of any of the four. What exists:

**Depth initializer (three files, 2,748,229,262 bytes in total):**
- On GCS, as single-part objects `q9/8865619b/436d1d64673f.p00-of-01` (`heads.json`, 3,410 B, sha256 fd60ac2f...), `q9/8865619b/9b9e03337df5.p00-of-01` (`heads.safetensors`, 924,151,276 B, 07c2d3b0...) and `q9/8865619b/c449bbe907be.p00-of-01` (`encoder.safetensors`, 1,824,074,576 B, 04823590...). The upload receipts are `/scratch/jjyeung/orch_cd/orchard_cp2/work/gcs/res_u2.jsonl` and `poll_u2.out` (lines 1-3); the sizes and hashes are in `fetch_cr.tsv` (lines 6, 54, 59) in the same folder; the kit's `k/0.json` pins each part to its destination path.
- Also on Orchard's project filesystem (`/project/community/jjyeung/distill/okit/in/cr/*.p00`) and inside one archive on the Mind file server; neither is needed.
- **Approved:** fetch the three objects from GCS with your existing session, one governed stream, after the export stream (never in parallel with it), verify the three hashes, and place them where the loader expects. This adds 2.75 GB on trinity-0-28; I am telling main. The 125 GB floor and the 130 GB stop stand.

**Model manifest (`model.json`, sha256 cc724d5e...):** no record names a copy outside the production job; its size is unrecorded. I am asking the operator for one read-only step inside the job that returns that one small file with its hash (refused if larger than 1 MB). The operator will deliver the bytes to your inbox. Do not rebuild the manifest by hand: it is hash-pinned.

Meanwhile continue: export stream, then the depth files. The GPU probe waits for the manifest.