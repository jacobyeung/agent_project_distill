# AWS root clear: two project roots, everything except a keep list

Status: BUILT and TESTED on 2026-11-09 on trinity-2-18 (Python 3.6.8, 38 of 38 tests pass). It has not been reviewed or run on AWS.

## Question

How do we clear everything under the two project roots on code-aws (`users/jyeung/ap` and its sibling root, about 25 M inodes on shared Lustre) as fast as is safe? Two constraints govern the answer:

- Weights whose Mind copy is not yet verified must survive.
- Sibling directories that belong to other projects (`cot_faithfulness*`, `a15_cot_c*`, `home_offload`, `alpamayo`, `alpasim*`, `datasets/hugsim`, `envs/hugsim`) must never be touched.

The user ruled on 2026-11-09 that only weights get copied, that all code is removed, and that only AWS moves happen now.

## Answer

The answer is `rootclear.py` (`/scratch/jjyeung/orch_cd/rootclear/work/`): a planner and executor that works on whole subtrees.

- **Planning.** The planner descends only into directories on the path to a keep entry. It plans every other entry as one "clear whole subtree" or "clear file/link" line, which records the item's inode.
- **Review and GO.** The plan and its sha256 go to a reviewer. Execution needs a `GO.json` that names that sha256 and the reviewer.
- **Execution checks.** Execution re-derives the plan. The header must be identical, and every current line must be a line of the reviewed plan; lines for items already gone may be missing, which makes stop-and-rerun safe.
- **How it clears.** Execution clears depth first, through `O_NOFOLLOW` directory fds opened from a pinned root fd. A pool of threads shares subdirectories, and an optional cap limits metadata ops per second.
- **Operation.** It honours a STOP file and signals, and it logs one JSONL line per finished item. The runbook (`RUNBOOK.md`) runs it in three phases: code and already-safe data, then weights tier by tier as each is verified, then the remainder.

## Reasons, with evidence

- **Planning is cheap.** Only directories on keep paths are listed, so a dry run costs seconds to minutes instead of a 25 M-entry walk. The test `test_plan_descends_only_along_keep_paths` checks that no line appears inside a cleared subtree.
- **Root pinning.** The real path must end in `users/<user>/<name>`, with `<name>` pinned by sha1, the same scheme as `awsclear.py`. Roots are compared by device and inode, and a root nested inside another refuses. Tests `test_root_given_as_symlink` and `test_root_prefix_sibling_not_a_root` cover this, including a link whose name looks right but whose target does not.
- **Keep entries.** Each keep entry is protected at its logical path, at its real location (real parent plus its own name), and at its link target when the entry is a symlink. Matching works on whole path components through a trie, so prefix confusion is impossible. Tests `test_keep_under_alias_name`, `test_symlinked_parent_leading_to_kept_path`, `test_keep_entry_that_is_a_symlink` and `test_prefix_confusion` cover it, with `runs` against `runs2` and `ap` against `ap_old`.
- **No symlink is ever followed.**
  - Every directory open uses `O_NOFOLLOW` from the parent fd, and every unlink and rmdir is fd-relative.
