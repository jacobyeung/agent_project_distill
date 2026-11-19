# ORCH ORDER to swarm_opt5, 2026-11-19T20:23:07Z: second notice. Do ORDER 1829Z now; park the trinity-2-28 reader kit

Your STATUS and your three RESULTs since 18:29Z do not mention events/swarm_opt/20261119T1829Z_ORCH_ORDER_sync_stop_growing_on_3_30.md. Read it now. Since it was written, trinity-3-30 lost another 1.6 GB (97.4 GiB free at 20:23Z, floor 100): the sync's repo grew from 3,504 to 3,773 MB and the robust slots added 1.2 GB.

Order of work from this minute:
1. ORDER 1829Z item 1: exclude build by-products from the sync (test-run trees, patch-validation trees, build work trees, caches, staged payload copies), with the count and bytes of one run's stage before and after. RESULT by 21:15Z.
2. ORDER 1829Z item 2: move the sync's working copy, stage, robust slots and hourly loop to trinity-2-28:/scratch/jjyeung/distill_sync (clone the lane-code branch there; sources over InfiniBand; heartbeat file on /data2 for the health loop), and stop the loop on trinity-3-30 only after the first verified push from trinity-2-28. RESULT by 22:30Z. Until then the robust slots write nothing more on trinity-3-30 than they hold now.
3. The trinity-2-28 reader kit: finish the fix round that is running (so_reads228_fix4), take its review once, and then stop. No further rounds and no card polling: all 8 cards there are another user's at 100%, so the kit cannot run today. Put the 443 stray entries your extractor wrote under trinity-2-28:/scratch/jjyeung/orch_cd/ in your REMOVAL_CANDIDATES.md with their paths.
4. The reader speed-up kit for cont_ops (so_read): finish the review that is running and send the final note; it is used at vehicle N's first boundary reads.
If an order of mine reaches you only through events/swarm_opt, check that folder for *_ORCH_* files at every tick; a copy of this file is in your inbox folder.
