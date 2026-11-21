# Review: rank 5 extension of the rank 1 paired relift (r1x/r1/relift.py)

Reviewer: read-only static review on trinity-2-28, 2026-11-21. No cell or score was computed.

**Verdict: GO.** No fix is required.

`diff r1p/r1/relift.py r1x/r1/relift.py` is byte-identical to relift_x.diff, so the extension changes only four things: the docstring, the NOGT constants, the GT count (38 to 59), the NOGT branch of the funnel-binding check, and the default --gt-dirs.

1. PASS. The two gt21 directories hold 15 T1 NPZs (7 ScanNet, 8 ScanNet++) and 6 ARKit NPZs, 21 in total. Each one is sha256-identical to its member in arch5/nogt_gt15 or arch6/nogt_arkit7. None of them overlaps the 38. The dump lever1_c/r1/returned/0.gz has 60 rows and 60 unique metadata.capture values, which equal the items544 capture set; that set contains all 21 NOGT and all 38 existing captures. The only dump capture without GT is arkitscenes/41254810.
2. PASS. FUNNEL_T1 objects.t1 has 144 objects on NOGT captures. Every one has binding null. 142 have gt_available false, and 2 (vsi590k_045785:window and :table, the item-level join) lack the key, which the code treats as false. With a null binding, the original equality could never pass, so skipping it loses no check. The new branch still raises if a funnel binding ever appears. The 152 objects on the 38 captures all have a non-null binding with gt_available true, and their check is the original expression.
3. PASS. The diff touches no other check. frame_indices == source_indices holds for all 21 captures (one source_indices per capture), and valid.all() is true for every one. Rasters are (32,240,320), except ARKit 42899829 and 47331002, which are (32,320,240). The unchanged shape rule censors those two as portrait, the same way it treats the 38. The unbound-operand exclusion, the item set (items544, 150 items: 76 on old captures, 72 on NOGT captures, 2 on 41254810), stats and the bootstrap all run unchanged over the shared loop.
4. PASS. The capture set comes from a glob plus an assert (21 captures, 41254810 absent). No code selects by score or result. Rank 5's record and NOGT_REPORT.md record 41254810 as passing geometry but failing binding (both same-frame IoU medians are 0) before this review. Its 2 items fall to the existing 'GT capture missing' exclusion.
5. PASS. The docstring matches the code. Its "gt_available false" also covers the 2 objects whose key is absent.

Non-blocking notes:
- counts.portrait_bound_objects still reports the funnel census of 20. It does not count the objects censored on the two portrait NOGT ARKit captures; those appear only as exclusions.
- The 41254810 exclusion reason reads 'GT capture missing'. A reader would need rank 5's record to learn the real cause, a binding failure.
- --depth defaults to HERE/returned/0.gz, which is absent in r1x/r1, as it is in r1p. Pass --depth and --receipt explicitly.
