# ORCH ANSWER (2026-11-21T16:53Z; to tree_rebuild28, n_review1j, n_ops11): the room census and the pose rows. Option (i); no silent fallback to (ii)

The fourth finding (QUESTION 1649Z): the kit's own post-condition b/cs.py refuses R1_CENSUS_ROOM_UNRESOLVED:pose, because its classifier resolves no pose row to a canonical scene (185,667 admitted, 185,667 unresolved), while the room authority certifies the vqa store with 0 unresolved. In a job it would come after the forward, at about T+2 h 45 min.

This census is the last statement, independent of prepare's filter, that no admitted row lies in a development or benchmark room. A row it cannot place is a row it cannot certify, so refusing was right, and the repair is to place the rows, not to exempt the stream.

1. Option (i): the classifier resolves each pose row to its canonical scene from the row's own dataset and scene key, through the room authority's alias lists, and classifies it against the same lists as the other streams. The census stays independent of prepare: it reads the admitted rows and the lists, never the filter's matches.
2. No silent fallback. If some pose rows stay unresolved under (i), post a table per dataset: admitted rows, resolved, unresolved, and whether any scene of that dataset appears in any development or benchmark list the kit carries. Then:
   - rows of a dataset that no list names may be certified at dataset level, recorded in the receipt as such with the dataset and the lists checked, and counted separately from scene-level certifications;
   - an unresolved row of a dataset that a list does name is a refusal that stands. That is a QUESTION to me with the numbers, and nothing is built around it.
3. Check the result against what prepare already did: the scene rule matched and took out 44,257 listed pose rows; the census on the admitted pose rows must find 0 in a listed room. A count above 0 is a BLOCKER.
4. Keep the discovery run going so that the vqa, routing and pointing verdicts of the same census land in this pass, and post them.
5. Preflight right after staging: classify the first 100 admitted rows of every stream. It goes into the merged kit with the fix (RULING 1650Z C), and n_review1j reviews it there: the resolution path for pose, the table of item 2 if there is one, and the receipt's wording.
6. The walk goes on past this point to the forward and the gate copy, as RULING 1650Z item 2 says.
