# cont_ops23 STATUS (trinity-3-30; started 23:36Z 11-19; rotate by 05:00Z)
## 01:16Z (exact)
- DONE: H@544 merged 900 (parent 173258 482 + remainder 173412 418, COMPLETE), scored with the sealed kit's score() on local copies (/project 249.98 GiB free, 0 bytes added). RESULT events/cont_ops/20261120T0111Z_RESULT_H544_heldout_camera_merged_900.md; files events/cont_ops/files_h544m/ (+ out/h544m here).
- Corpus: 469ddece_s544_heldoutcam_H482p_173258 (partial), 469ddece_s544_heldoutcam_H418r_173412.
- Pool returns dd982cd5c4b250002a564 and dc863c3e6b41d0002a4ca renamed into ae71c903_fetched (result sha c4912084…dd645).
- Nothing of mine runs on Orchard. ORDER 0005Z item 3: nothing on advanced tonight; queue goes to general (empty). Optional routed-distance@600 kit: not built (advanced closed).
- Open: QUESTION 2054Z (11.7 GB partial tar on 3-30, user to delete). QUESTION 2339Z resolved by its default. Asked for an Astra review of the local-route driver (work/local_score.py) in the RESULT.
- Next: poll events/cont_ops for *_ORCH_* every 10 min; act on orders.
## 01:25Z
- ANSWER 0121Z: review yes; fb_pack table owed by 03:00Z -> DONE: events/fb_pack/20261120T0124Z_RESULT_cont_ops23_H544_reworded_camera_called_but_wrong.md (files_h544m/wclass*). Finding: reworded failures are wrong tool choice (object ground/gap on "frame N"/"camera"), not unit/sign.
- Astra review c23_revloc RUNNING on trinity-2-28 (tmux c23_revloc; dir /scratch/jjyeung/orch_n30/cont_ops23_c/rev, output REVIEW.md; log ../revloc_dispatch.log). Next: read REVIEW.md, post RESULT, then rotate/end (queue empty).
## 01:42Z (final unless an order arrives)
- Review c23_revloc GO (3 minor findings, no number changes) -> RESULT 20261120T0141Z_RESULT_H544_local_route_review_GO.md.
- RULING 0130Z: per-type aggregation only from now on; table kept in files_h544m with READERS.md.
- Queue empty; nothing on Orchard/GPUs. Lane ends per ORCH ANSWER 0121Z item 4 (no successor launched). Removal candidates: REMOVAL_CANDIDATES.md (+ /dev/shm/c23/rev, rev.tgz; 2-28:/scratch/jjyeung/orch_n30/cont_ops23_c).
