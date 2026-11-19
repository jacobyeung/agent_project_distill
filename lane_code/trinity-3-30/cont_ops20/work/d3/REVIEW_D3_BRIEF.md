# Review (read-only): three-segment merge scorer for the D distance read at step 544

Workspace: /scratch/jjyeung/orch_n30/cont_ops20/work/d3. Write only REVIEW_D3.md there. No ssh, network, Git, or code edits. Search only inside this directory, /scratch/jjyeung/orch_n30/cont_ops18/dresume (the reviewed two-segment scorer score_d.py and its helpers return_tools.py, score_base.py, fetch_validation.py, dbuild/make_items_d.py, RESUME_D.md), /scratch/jjyeung/orch_n30/cont_ops19/work/drem2/make_rem2.py (how remainder 2 was selected), /scratch/jjyeung/orch_n30/cont_ops18/d544ret (parent package pkg/ and return f/), /dev/shm/c19r and /dev/shm/c20t1 (remainder-1 package and unpacked returns).

The D read of 580 items ran in three allocations: the parent (478 done), remainder 1 (3 of 102 done), remainder 2 (the other 99, not yet run). score_d3.py merges them. TEST_D3.txt records checks on the two existing segments and why the scorer drops artifact_manifest_sha256 from the cross-segment binding equality and checks code bytes instead.

Check only, and report verified problems with file:line evidence:
1. Every authentication score_d.py's merge applies to a pair is applied to all three segments (unpack receipts, manifest/package identity, provenance chain parent -> rem1 -> rem2, export binding, fresh tokens/plans, evaluator files, settings, disjointness).
2. Is replacing the artifact_manifest_sha256 equality by the code_py byte-equality check sound (does the artifact manifest bind anything else that could differ silently: weights, components, paths)? Use the package source under d544ret/pkg/src.
3. Metrics, paired reworded-minus-twin and the optional compare group are computed as in score_d.py; missing items never score zero.
4. Python 3.6 compatibility of the code paths (it runs with /scratch/jjyeung/envs/p1cpu/bin/python here).
Verdict line at the top: GO, GO AFTER FIXES (list), or NO-GO (list). Do not design fixes beyond naming the defect.
