# ORCH RULING (to tree_rebuild23, n_ops8, lever2): Orchard host-key warning: continue on the verified connection; never bypass the check; hold on a second occurrence
1. Continue. The retry verified against the recorded key with no change to known_hosts, and the refused attempt sent nothing; the warning fell inside the login side's two minutes of closed connections.
2. No lane edits known_hosts, removes an entry, or passes any host-key option (StrictHostKeyChecking, UserKnownHostsFile, -F), now or later. A refused connection is a refusal, not something to work around.
3. tree_rebuild23: copy the warning's fingerprint line and key type from the failed call's stderr into your next RESULT (it is not a secret), so the user can compare it with Orchard's published keys.
4. If the warning appears a second time in any lane: that lane stops every Orchard call, posts a BLOCKER with the fingerprint line, and the other lanes hold new Orchard connections until I answer. Jobs already running on Orchard are not touched.
5. No GCS session is minted or installed in the ten minutes after a warning; n_ops8 checks `ssh -O check` first.
