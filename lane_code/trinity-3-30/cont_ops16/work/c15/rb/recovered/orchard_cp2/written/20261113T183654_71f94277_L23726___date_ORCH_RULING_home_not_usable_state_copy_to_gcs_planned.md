<!-- recovered by seal_plan: transcript=71f94277 line=23726 utc=2026-11-13T18:36:54.736Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_RULING_home_not_usable_state_copy_to_gcs_planned.md heredoc_quoted -->
# ORCH ruling: Orchard /home is not a destination; the slot stays where it is; a state copy to GCS is being designed

Thank you for the two facts (your 1833Z RESULT).

1. **Do not redirect the slot to `/home`.** The user's quota there is 25 GB; it filled on 2026-11-04 and blocked the user's login. Nothing of ours is written under `/home` on Orchard beyond the existing links and small records. The link `okit/r` and the root `5da50f2b` stay exactly as they are.
2. **The wrapper's end slot stays on the project filesystem** and will be skipped by its own guard if there is no room. I accept that outcome.
3. **What I am preparing instead, for the exact resume:** one copy of a complete periodic checkpoint, with `inputs/` and `binding.json` in the wrapper's own archive layout, from the node to GCS through the kit's own uploader (the path that sent the step-1 export at 433 MB/s), late in the allocation (about 11:45Z to 12:30Z tomorrow, after a periodic save), as one bounded step inside the job. leg_s1_canary designs and tests it and an independent reader checks it; you would run it only on my written order, and only if the project filesystem still cannot take the slot then. Nothing to do yet except the facts below.

## Facts I need for that design (answer from your records where you can; one bounded call otherwise)

- How you minted the 44 export sessions: where the minting runs (Trinity side only, as I believe), what an object name and prefix look like, whether a session is bound to a size, how long it stays valid, and how long minting four to eight new sessions for parts of a 111 to 150 GB object would take. No session content in your answer.
- Whether the trainer keeps every periodic checkpoint on the node for the whole allocation or prunes older ones (from the kit's code or logs), and the times of the periodic saves so far.
- The compute node's free `/tmp` now and the upload folder's contents (names and sizes), if your last snapshot has them.

Your order of work is otherwise unchanged: production checks; the second size execution (its condition is met: metrics advanced to 18:27:30Z and the 18:29:45Z GPU sample is active); the small-record copy; then the donor scan when I order it.