# Clearing copied units from AWS after their Mind copy is verified (2026-11-09)

## Question
The user ruled: "After we copy over from AWS, please remove it from AWS." How do we clear from AWS
(`users/jyeung/ap/` on code-aws Lustre, ~25M inodes) exactly the files that went into a sha256-verified Mind archive,
and nothing else, given that an earlier generator (rmkit15) cleared files that were still needed?

## Answer
A member-list tool, `awsclear.py` (version awsclear-2), runs inside the sender's own Slurm job (CPU, one thread,
standard library). It acts only on the members listed for each verified unit and re-checks every member at execution.
Code and tests: `/scratch/jjyeung/orch_cd/rmrun/work/tool/` (awsclear.py, build_plan.py, test_awsclear.py: 80/80 pass;
classes F01..F27 cover the three adversarial reviews, F28..F31 the verifier's gaps and the Codex review). Runbook: `/scratch/jjyeung/orch_cd/rmtool/STATUS.md`.

- Input: a streamed units file (one unit line, then one line per member) built by `build_plan.py` from the verified
  records (`_direct/ok/<tok>.json`) and each archive's own manifest, cross-checked against the archive's TOC. A TOC is
  required; a token needs exactly one queue item; rml-source units are left out.
- Root: pinned to `users/<user>/<root>` by hash; an alias must be the same directory (device and inode); a mount point
  inside the root refuses the run; a member or parent on another device is skipped (`mount_crossing`).
- Receipts: the dry run needs a receipt at most 24 h old (method `rehash` by default). Execution needs, per unit, a
  `rehash` receipt with `measured_sha256` equal to the unit's sha256, checked after the plan was made and at most 6 h old.
  The Mind step marks a receipt not ok when the archive is missing, has another size, is marked `_direct/pruned/<tok>`,
  fails its re-hash, or (tar) has an unreadable TOC or manifest.
- Unit refusals: bad record, duplicate id, receipt problems, no fin'd sender record (with `--sender-results`), any member
  on the deny list (other projects, case-insensitive, including `alpasim*` and the sibling tree), in the other owner's
  top-level trees (`main_tree`, named by hash), or on the protected list (tool, plan, GO, log, state dir, inputs, `~/.ssh`,
  sender queue dir, key, known_hosts, results, and by default `ap/f0d48c2b` and `ap/c553c6fc`). `--unprotect f0d48c2b/x`
  exempts a member only when its logical and real paths both lie under the prefix, and refuses a prefix that crosses a symlink.
- Holds: hold files (absolute paths under the root, `name:<basename>`, k15 HELD tsv and KREF audit tsv by column); the
  sources of sender-queue items that are pending or on hold; the workdirs of the user's other Slurm jobs. Relative
  entries, globs and tabs refuse the run; entries missing on disk refuse it unless `--allow-hold-missing`; the plan
