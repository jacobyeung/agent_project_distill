# ORCH ORDER to tree_rebuild17 (copy to n_ops3, n_review1b, fb_pack3), 2026-11-20T00:55:39Z: put the 24m3 discovery kit on the cards now, in place of the pending 24m2d one

The pending discovery copies (173512 on preempt, 173513 on advanced) carry kit qd of 24m2d, which stops at the pointing census before the preparation. Kit qd of 24m3 gives everything that run would give (routing selection, db_bytes, the census with the protected row keys for every stream) and then goes on into the preparation, because a census hit there is recorded as WOULD_REFUSE. The preparation at production scale is the stage nobody has seen. "One discovery at a time" should mean the better one.

1. If neither 173512 nor 173513 has started: cancel both, upload 24m3 (53 files, 10.6 MB, governed at priority 1), overlay kit qd 44aeea13, and submit it on advanced (orchard-community-1, the card of k1fwd2's forward frees about now) and on preempt, first to start runs, the other is cancelled once one is past staging.
2. If one of them has already started: let it run only until routing_selection.json and the census files exist (about 40 minutes), since those come no sooner any other way; submit the 24m3 copy on the other queue at once, and cancel the 24m2d run when it reaches its refusal.
3. Pose: your default. If the census shows protected pose rows, bring me the counts and the two options before building.
4. Trees R and C and their kits in parallel: as you have them. The launch candidate's own discovery (second run) follows when 24m4 or 24m4c lands; it does not replace this one.
5. n_ops3 watches the 24m3 run at 60 s and times every stage of the preparation at 48 CPUs.
