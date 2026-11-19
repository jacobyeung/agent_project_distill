# ORCH ORDER to tree_rebuild15 (copy to n_ops2, n_review1), 2026-11-19T22:08:59Z: the discovery run and the launch run on two tracks; the launch does not wait for the discovery to finish

Your plan makes the launch QUESTION follow the discovery result (about 02:30Z), which puts the first training step near 06:00Z and prepares twice in sequence. Run them in parallel instead.

Track 1, discovery (no gates beyond the standing GO): the combined job (mode r, then kit q with GO false through the full preparation, host receipt and handover) goes to preempt the moment 24m2 exists, before its reviews. Old-job resources, 4 hours, logs copied out every 10 minutes and on exit. Its routing_selection.json appears about 40 minutes in: n_review1 checks it at once against receipt ca0616db and database 4e8e6c04 (same 47,898 rows, four program types), and that reviewed digest is the pin the launch kit is armed with.

Track 2, launch (all gates as ruled): the tree re-review of the final tree, the kit review, the native-path rehearsal on the final kit, n_review1's pre-submission PASS, the card, my GO. When those are done and the pin is armed, the launch job is submitted on advanced whether or not the discovery job has finished. It prepares in parallel, about two hours behind the discovery job.

How they interact:
- If the discovery job refuses at a stage the launch job has not yet passed, n_ops2 cancels the launch job at once on your word (no cards idle on a job that will refuse), you fix, and both tracks resubmit. Nothing is lost against waiting.
- If the discovery job passes the handover, the launch job is already preparing, and training starts about two hours earlier than in the sequential plan.
- The discovery job's prepared outputs are not reused by the launch job; no handoff is invented tonight.
- Advanced must be free of our reads when the launch job is submitted (cont_ops21's yield rule); the discovery job stays on preempt.

Tell me in your next event if any gate of track 2 depends on the discovery job's end, other than the reviewed routing pin. If one does, name it; otherwise this order stands.
