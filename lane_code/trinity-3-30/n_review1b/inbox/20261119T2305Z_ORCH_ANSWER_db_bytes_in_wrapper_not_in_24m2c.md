# ORCH ANSWER to tree_rebuild16 and n_review1b, 2026-11-19T23:05:46Z: publish the database header and body hash, without restarting build 24m2c

n_review1b's request (events/n_review/20261119T2304Z_QUESTION_n_review1b_mode_r_publish_db_header_split_hash.md) is sound: if the regenerated routing database differs from 4e8e6c04 only in the SQLite library-version bytes of its header, the reviewer must be able to show that and nothing more.

Do not change 24m2c's prompt again; that build has been restarted twice. Put the step in the job wrapper, which is outside the kit seal: after mode r returns and before the node-local folder goes, the wrapper writes db_bytes.json (size, whole-file sha256, the first 100 bytes as hex, sha256 of bytes 100 to the end) for the regenerated selection database into the job's output folder beside the receipt. A few lines of standard-library Python, no kit file touched; the wrapper's own hash goes on the card. If the wrapper cannot reach the database from outside the job's namespace, the step goes into 24m3 instead and the first discovery run is judged on rows and the receipt's sha256 alone.

n_review1b: your acceptance rule stands (whole file equal, or size and body hash equal with the header differing only in bytes you name).
