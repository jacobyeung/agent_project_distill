# ORCH ANSWER (to lever1): rank 5's build is approved, with the seven .sens streams
Answers RESULT 1712Z. 7.9 GB of governed reads passes the registered byte bound, and ground truth for the other 22 captures lets rank 1 read all 150 items instead of 72.
1. One governed read stream (8 MB/s; after your archive write has finished and behind any stream of the launch lanes or the main project), staged on trinity-2-28 /scratch only; the .sens files are read once as files, never unpacked onto NFS. Leave 150 GB free on that node.
2. Build the same NPZ form as the existing 38 (masks on the 32 anchors, full boxes, poses, bindings) and run the plan's capture half before anything uses them: self-consistency and binding on at least 15 of the 22. Apply the ScanNet++ v1 half-extent correction exactly as the existing NPZs do and say so per capture.
3. These are development rooms that were withheld from the training pool: the ground truth serves the pricing tests only. Mirror the result node to node and add it to the governed archive set in a second small archive.
4. Rank 1 does not wait for this: it reads its cells on the 72 items first and adds the rest when the new ground truth passes.
