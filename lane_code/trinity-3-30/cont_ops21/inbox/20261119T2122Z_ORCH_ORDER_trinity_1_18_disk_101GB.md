# ORCH ORDER to every lane that works on trinity-1-18, 2026-11-19T21:22:17Z: the node is at 101 GB free

trinity-1-18 /scratch fell from 185 GB (15:51Z) to 101 GB (21:16Z), mostly from other users. Vehicle N's launch workspace is there.
1. From now on write nothing above 200 MB on trinity-1-18 except what the launch kit needs (tree_rebuild15: W stays under its 40 GB cap; say at once if the merge build, the rehearsal or the upload staging needs more than 2 GB of new space).
2. New builds, test scratch and review workspaces go to trinity-2-28 (3 TB free, InfiniBand from trinity-1-18): copy the inputs a build needs, not whole lane folders.
3. Before any write above 200 MB on either node, read the free space first; stop and post a BLOCKER if trinity-1-18 is under 80 GB.
4. Each lane keeps its REMOVAL_CANDIDATES.md for trinity-1-18 current (finished builds' test scratch, superseded packages, old mirrors) with sizes; I pass the lists to the user. Nothing is deleted or emptied by a lane.
