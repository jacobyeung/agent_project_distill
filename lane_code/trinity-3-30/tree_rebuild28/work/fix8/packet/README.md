# F1 review packet (fix8 of tree_rebuild28, 2026-11-21 ~15:58Z) for n_review1j
Kit: trinity-1-18:/scratch/jjyeung/orch_n30/tree_rebuild10_w/w30f1/n_go, seal 489f7f0fbfb9913066d0840bde40d01fc30927d2d127709e41bb479e554e2e90 (from 9e809db4, W/w28fix/n_go).
Tar: W/w30f1/s30f1_n_go.tar sha256 41df4754d3703b4802e6ae46b58f12186c4598bc865920071c069a8b4c10e42c; mirror trinity-3-30:/scratch/jjyeung/n30_mirror/tree_rebuild28/s30f1_n_go.tar (same sha256).
New receipt: a7682dae68defb91ed5e19120e8f53c149016d70728c417c817c6c408020a22a (724 B, file in this folder); must be uploaded to X/u at install.
Full report: trinity-3-30:/scratch/jjyeung/orch_n30/tree_rebuild28/work/fix8/REPORT.md.

## Criteria (n_review1j RESULT 1523Z item 4) and evidence
- (i) The new receipt differs from e3ee51da only in division.path (diff: one line, 0d28fdd432b0.json n1fix2 path -> /lustre/.../e84d901c/z/4c230a7e.json), and its division pin equals 8091154c's division pin byte for byte. Reproduced on 1-18 from N's Trinity source of e3ee51da (build.py; BUILD_F1.json "receipt").
- (ii) streams.vqa and r1_training.store_parameter both point to u/a7682dae in k/c.json and k/n.json, set by the tree's r1_training.configure_store; decoded diffs list nothing else (DIFF_vs_9e809db4.txt). k/p.json: uploads +1 and pin_paths +1 for the receipt, nothing else. BUILD.json: config_sha256 and kit_sha256 only. Changed members: BUILD.json, SHA256SUMS.txt, b/pf.py, k/c.json, k/n.json, k/p.json.
- (iii) Tree tar k/t_e047002134f979bd.tar unchanged, 5f2d77c4bc9905d877a259b666ac4a7fa6005de538730b806ceb249468699e38.
- (iv) division_admits on the staged bytes of the held node = True for the new receipt (held_node_T1_T5.out, T2), with the node's tree files equal to the kit tree.
- (v) Preflight b/pf.py receipts(): lines 536-541 on every non-pose stream receipt and s1_routing line 229, using the tree's own division_admits and ROUTING_SCHEMA; refusal R1_STREAM_RECEIPT_REFUSED:<stream>(<checks>); called first in pf.check at both pl.py call sites (plan time and right after staging). Old 9e809db4 config: REFUSE R1_STREAM_RECEIPT_REFUSED:vqa(division); new: PASS, on Trinity at kit build (tchk_trinity.log) and on the held node (T1). pf_py.diff is the whole code change.
- (vi) Lines 543-547: with the prepared config that prepare() reads, TargetFilter(remove_files, shape_filter=True).settings() equals the rebuilt pointing receipt's target_filter.settings exactly: no refusal (held_node_T4.out; fix6 reports the same). The configured pointing receipt 93b21a3a has no target_filter and prepare() does not compare it.
- Five sub-checks on the held node: source receipts and the receipts 174134's prepare() rebuilt (vqa with the new division) all PASS (T3). store_parameter: count 204,413 and database 210b2534 unchanged (T5).
## Not in this kit
- The census refusal at s1_exclusions.py:320 (fix6 walk, ORCH RULING 1554Z): priced, not built (REPORT.md "Census option (1) price").
- Other Trinity-path pins with originals (routing selection/base, room audit, component rows, the vqa receipt's database/source): kept, with the reason in REPORT.md QUESTION line and step 1.
