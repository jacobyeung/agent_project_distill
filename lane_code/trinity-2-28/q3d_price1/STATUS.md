# q3d_price1 status
Updated UTC: 2026-11-20T02:56:03Z
Status: BLOCKED; kit is not ready; no experiment exists.
Code: W/src, commit bf91573212c3538fc314d2add05519d7e9fd6b7e; one shallow clone completed.
Stock Qwen-3D + required backbone + local G3T: 21030841260 bytes, exceeding decimal 20 GB before environment/data.
Evidence: W/evidence/INPUT_BUDGET.json and the three public model file listings, including advertised LFS hashes.
Protocol issue: default decoder consumes ScanNet mesh points/superpoints; depth/pose-only replacement leaves sensor geometry in B.
Environment, adapter, manifests, tests, CPU dry run, bootstrap and run_read.sh: not built; W/kit is empty.
No large downloads or governor registration attempted; no governor refusal claimed; existing node agent is present.
No GPU, jobs, SSH, deletion or stops of other agents. /scratch has 2.9 TB free.
Record: /data2/jjyeung/agent_project_data/distill_design/QWEN3D_PREDICTED_GEOMETRY_PRICING_20261120.md; registered rules preserved, no second INDEX line.
Resume: establish storage-compliant loading and exact-frame inputs, then build RGB-only decoder support with scoring geometry isolated. GPU read still needs review and GO.
W = /scratch/jjyeung/orch_n30/q3d_price1
