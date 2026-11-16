<!-- recovered by seal_plan: transcript=71f94277 line=22718 utc=2026-11-13T16:46:09.606Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/20261113T1652Z_ORCH_LEAD_persister_mirror_may_be_the_writer.md  -->
# ORCH lead (2026-11-13T16:52Z): check the kit's own periodic mirror first

Free space was 559.8 GB at 16:44:58Z (another 18.4 GB in five minutes).

A lead from the sealed kit, not yet a finding: `b/r.sh:69` runs `tk_persist_small` every 600 seconds from the launch at 15:41:38Z, and `b/c.sh:398-402` copies three things from the node to the project side: `o/`, `arm/`, and **every `*.json` and `*.jsonl` under the node-local runs root** (only `checkpoint_*`, `full_weights/` and `*.pt` are excluded). If full-population admission writes large JSON or JSONL files under the run folder, each cycle copies them to `$HM/runs/` on the project filesystem. The cycle times (16:21, 16:31, 16:41Z) fit the steps in your series.

In your next routine call:
1. Bytes, file count and the ten largest files of the resolved `x_07ca49df/runs/469ddece`, `x_07ca49df/o` and `x_07ca49df/arm` on the project side, with their modification times.
2. If that mirror is the writer: its size now, its growth per cycle, and from the node-local side (only if your bounded reader can see it without entering the job) the total of JSON and JSONL under the run folder, which bounds how far it can grow.
3. Post the RESULT at once either way. Do not stop the persister, the job or anything else; if it is ours, the decision on what to do is mine.
