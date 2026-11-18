<!-- recovered by seal_plan: transcript=71f94277 line=29536 utc=2026-11-14T07:30:10.394Z kind=written original_path=/scratch/jjyeung/orch_cd/if_p0/inbox/$(date_ORCH_ANSWER_persist_record_yourself.md heredoc_quoted -->
# ORCH answer to QUESTION 0729Z: yes; persist it yourself, three writes

You may write under `/data2/jjyeung/agent_project_data/distill_design/` exactly these and nothing else:
1. `IF_P0_ORCHARD_RUNTIME_20261114.json`: your record `out/IF_P0_ORCHARD_RUNTIME_RECORD.json`, byte for byte.
2. `if_p0_20261114/kit_ifp0_orchard_job_0fa68201bddadd5b.tar.gz`: the sealed kit archive (1.28 MB), copied with the IO governor's archive copier (`io_governor/copy_archive.py --job ...`, as the rules for writes to `/data*` require), then hash-checked at the destination.
3. One line appended to `INDEX.md` with `>>`, naming both, in the style of the existing lines: what the record answers (how to run a sealed one-GPU probe job on Orchard: job-private staging from project archives, inventories from real header listings, the namespace, partition and time limits, cross-seal admission) and its status.

The existing design record `INFUSION_VISION_CAPACITY_20261113.md` stays as it is; when P0's real result exists, append its status section there (result, headroom gate, next arm) with one more approved write, which this note already covers. Post no event for this unless a write fails; put the three hashes in `STATUS.md`.