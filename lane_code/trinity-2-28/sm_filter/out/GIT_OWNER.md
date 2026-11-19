# Filter owner notes

This package replaces only `tools/lane_code_filter.py` and `tools/dry_count.py`. Install on trinity-3-30 under the existing sync lock using the commands in REPORT.md. Robust mode stays ON. This note accompanies the package; it does not replace the installed owner guide.

Only labels matching `trinity-<n>-<n>` protect all root children as lanes. `dry_count.py` passes the lane name, and `land_kit.py` passes `kit`, so their root contents receive ordinary directory and MAXDIR gates.

Ancestor gates apply even when `LCS_REVIEW2_FIXES` is unset. This changes dry_count's default behavior from checking only the selected directory to checking its ancestors too. Its main function remains byte-identical to the supplied input. With `LCS_REVIEW2_FIXES=1`, the existing cross-boundary filename-substring and dedup guards also apply. Counts deduplicate within each requested folder; hourly counts deduplicate across the node.

Kit landing uses the same filter and refuses skipped members unless the owner passes `--allow-skips`. New skip classes include test output directories, temporary suffixes (with the word-plus-number exemption), 32-hex directory names, attic/sandbox/rehearsal/fixtry trees, nested lane copies, unpacked archives, versioned Python library directories, payload environments, and generated build review/integration outputs. Ordinary `lib/python_compat.py` files remain eligible. Codex run-record directories remain traversable; generated children inside them still receive normal gates.

Inspect STATS and `skipped_timeout` after installation. Only trinity-2-28 has a fresh live scan; the other nodes have inventory replay coverage.
