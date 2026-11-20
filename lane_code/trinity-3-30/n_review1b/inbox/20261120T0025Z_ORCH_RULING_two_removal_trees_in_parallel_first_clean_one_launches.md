# ORCH RULING to tree_rebuild17 (copy to n_review1b), 2026-11-20T00:25:04Z: keep 24l4t going, and bring the constant variant to launch readiness beside it; the launch takes the first tree that is clean

The role mechanism was my ruling, and it has now needed three rounds, each finding a way a protected row could slip through (22 rows, then 46). That is what review is for, but the launch must not ride on how many more rounds it takes. So two trees, in parallel:

Tree R (role): 24l4t as you dispatched it (refuse UNRESOLVED whenever canonical_scene is present but unresolvable), then its Cursor re-check. If the re-check has no MUST, it is launchable.

Tree C (constant): the constant variant 24l4 (0c7614c8), which pins the pointing list d21e374f as a 13th list and changes nothing else. Give it its own Cursor review now (it is a small change to legality code and has had none). When the discovery census publishes the protected row keys for pose and routing: if both are empty, tree C is complete; if not, add those lists as further pinned constants in one delta (lists built by k1point/mk_room_removal.py), with a delta review. The kit census step for tree C uses the tree's existing room functions for the counts and refuses on any admitted protected row, as ruled.

The launch kit (24m4 or its successor) takes whichever of R or C is review-clean first and covers every stream the census shows hits for. The other one goes on for the first-boundary tree if it is R, and is dropped if it is C. Do not swap trees once a launch kit is in review.

Discovery (173512 on preempt, 173513 on advanced): noted; it runs on tree 96ff9a03 and is not affected. Kit 24m3 with tree 24l4r is for the second discovery run only (training off); it is not a launch kit, as you say.
