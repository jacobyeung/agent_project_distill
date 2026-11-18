<!-- recovered by seal_plan: transcript=71f94277 line=23726 utc=2026-11-13T18:36:54.736Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_canary/inbox/$(date_ORCH_ORDER_state_copy_to_gcs_design.md heredoc_quoted -->
# ORCH order: after the full-filesystem analysis, design a copy of the training state to GCS from inside the job

Do the analysis of my 1822Z order first; this is the next item and extends its point 3.

**Why.** The project filesystem had 388 GB free at 18:31Z and is falling about 240 GB per hour; `/home` on Orchard has a 25 GB quota and cannot take the slot. If the wrapper's guard skips the slot at the end, the exact training state (FP32 masters, optimizer state, rank random state) dies with the node. The kit's own uploader moved 21.6 GB from the node to GCS in 49.8 s (433 MB/s, four parts), and node-local `/tmp` has about 5.6 TB free. So the state can leave the node through the path that is already proven.

**What to design (note first, at most 60 lines, `out/STATE_COPY_TO_GCS_DESIGN_169097.md`, posted as a RESULT; build only after my word):**

1. One bounded step inside job 169097 (`srun --jobid=169097 --overlap`, low priority, a hard time limit), run by the operator on my written order late in the allocation, after a periodic save has completed and well before the trainer's stop at hour 23.
2. It selects the newest checkpoint whose `complete.json` exists and whose files have not changed for a stated quiet period, and proves from the trainer's own records that no save is in progress.
3. It builds an archive with **exactly the wrapper's slot layout and member rules** (the reviewed template a3efb28b: checkpoint directory, `inputs/`, `binding.json`, hard links stored as regular files, the same content checks against `complete.json`), into a private folder on node-local `/tmp` outside the run and upload folders, with its SHA256.
4. It uploads that archive with the kit's own `gcsput.py` against freshly minted sessions for new object names under a separate prefix; receipts and all output go to standard output or the private folder, never to the project side; no credential leaves the node; the run folder, the upload folder and the kit's `sess.json` are not touched.
5. It returns a small record (step, archive bytes, SHA256, object names, per-part server checksums) in a form that survives the operator's transport (encoded; raw response saved before parsing).
6. Restore side: say how that object becomes a slot the reviewed wrapper accepts (downloaded into the persistent root in slot form when the project filesystem has room, with the slot index record the wrapper expects; or, if it has no room, what the smallest wrapper change would be to restore from a node-local download), and how your continuation checker would verify it first.
7. Risks to the running job, each with its bound: CPU, memory and page cache inside the job's allocation, read load on the node's disk while the dataloaders run, network, time; what happens if the trainer starts a save during the copy; what is left on the node (nothing is removed by any agent; the node's `/tmp` vanishes with the job).
8. What must be measured or rehearsed before the real run, and where (a rehearsal on `general` with a synthetic checkpoint of realistic size is acceptable if it needs no GPU).

Ask orchard_cp2 (through me, by a QUESTION event) for facts you lack about session minting and checkpoint retention; I have asked it for them already. Reading and design only for now.