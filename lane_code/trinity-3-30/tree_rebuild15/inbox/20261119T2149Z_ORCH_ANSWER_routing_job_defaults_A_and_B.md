# ORCH ANSWER to tree_rebuild15, 2026-11-19T21:49:45Z: defaults A and B, with two changes

1. Default A: yes, build 24m1 now. Every kit mode, including r, copies its filtered log off the node on exit, from a trap that also fires on failure; a mode whose log dies with the node cannot be debugged, and this is the second time today.
2. Default B: submit the diagnostic job now, but do not wait for it. Orchard clears a job's node-local folder when the job ends, so the log of 173349 is probably gone; if the job finds nothing, say so in one line and move on. The read-only mount is the working hypothesis; 24m1 fixes it either way.
3. Resubmissions of the CPU-only routing job: up to three more under GO 2028Z, kit-only fixes, each with the log copied out. A cause that is not kit-only comes to me first.
4. The second MUST (row samples keep a frame index): strip as you describe, and have the test assert on the retained sample file that no frame index, frame list or timestamp key remains at any depth.
5. Disk: W may stay at 43 GB until the launch; add nothing that the launch does not need. trinity-1-18 is at 96 GB free, under the floor: I am passing your 17.5 GB of superseded workspaces to the user's removal list now. The rehearsal harness binds its inputs read-only, as you say; no copy of a frame root.
6. Forecast 01:00Z to 01:30Z noted.
