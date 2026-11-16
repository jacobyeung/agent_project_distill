# Build N7 + R5: salt the token digest tables in builds N and R; pin the production-root gate (one-shot Codex build)

Same rules as `builds/BRIEF_N4.md`, `BRIEF_N5.md` and `BRIEF_N6.md` (read all three): source, docs and final evidence only
inside `/scratch/jjyeung/orch_n30/b07_offread/builds/N/` and `.../builds/R/`, at most 60 MB of new bytes there; every pytest
basetemp, rehearsal, fixture run and packet build under `/dev/shm/b07_n7/<fresh name>` or under a production-style root
`/tmp/a_900000_<12 hex>` (below 20 MB each); no ssh, network, Git, GPU, Slurm or Orchard command; no deletion of any file
(write new names instead; `shutil.rmtree`, `rm`, `unlink` are refused by a guard); Python
`/scratch/jjyeung/envs/p1cpu/bin/python -B`; never open a benchmark answer or score.

## Context
- The same name-opacity module ships four times: R `kit/xnames.py`, `kit/vsi/launcher/xnames.py`, `kit/revsi/launcher/xnames.py`
  and N `offnative/opacity.py` (byte-identical up to the module name). `runtime_table()` writes `x0.json` with
  `tokens: {sha256(name): token}` and `aliases: {sha256(logical path): target}`; the job's `install(root)` reads it.
  A reviewer showed that hashing ~20 dictionary words inverts the table. Ruling (orchestrator): in-job file contents are
  exempt from the naming rule, but salt the digests per packet so a dictionary cannot invert them.
- Gate status: the reviewer's F1/F2 tests (`builds/R/tests/test_review_offnative2.py` + `sim_r_namespace.py`, byte-equal
  copies; do not edit) pass when the sim root is the Orchard spelling (`ROFF2_ROOT=/tmp/a_900000_<hex>`), and fail with a
  root that has named ancestors (e.g. the reviewer's default `/scratch/jjyeung/orch_n30/review_offnative2/work`) only because
  xnames then exposes the root as `/proc/<pid>/fd/<n>` and the sim looks the bind source up by its logical spelling. The
  kit is correct there; `builds/R/tests/test_prodroot.py` (new, mine) checks F1/F2 under both root kinds with a
  mapping-aware lookup. Keep it, run it, and run the reviewer file with `ROFF2_ROOT=/tmp/a_900000_<fresh hex>`.

## Fix: salted digest table (all four copies identical, both kits)
1. Secret: `/scratch/jjyeung/orch_n30/b07_offread/work/salt/SECRET` (64 hex, mode 0600, Trinity-only). Never copy it into
   any package, payload, log, report or test fixture; reports may name its sha256 only.
2. Per-packet salt = HMAC-SHA256(secret, sha256 of the packet's payload member pins excluding `x0.json`), hex. Deterministic
   so rebuilding the same payload yields the same package bytes; distinct packets get distinct salts. A build without the
   secret refuses to package (tests inject a fixture secret, never the real one).
3. `x0.json` gains `salt`; every digest in `tokens` and `aliases` becomes sha256(salt bytes + name bytes). Keep the build
   host's in-process tables as they are and re-key only when emitting `x0.json` (store aliases' logical names on the build
   side so they can be re-keyed). `install(root)` reads `salt` and uses it for every lookup and every digest it computes
   afterwards (`_key`, `_learn`, aliases, `component`). An `x0.json` without `salt` is refused at install.
4. Tests: (a) a dictionary of all WORDS plus every name in the build's NAME_MAP hashed unsalted finds no key in either
   shipped `x0.json`; (b) two packets with different payloads have different salts; same payload rebuilt gives the same
   salt and package sha256; (c) the secret's bytes and hex appear in no shipped member; (d) every existing
   name-mapping, media-alias, F1/F2/F3 and rehearsal test still passes with the salted table; (e) one full CPU rehearsal
   per kit under a `/tmp/a_900000_<hex>` root.

## Deliver
Rebuild R `package_vsi.tar`, `package_revsi.tar` and N `code.tar` with all manifests and pins (refresh N's R snapshot
deliberately), update both readiness reports (first sentence READY / NOT READY per benchmark x reader), RUN.md (add the
`ROFF2_ROOT` gate line), DIFF.md, and write `out/N7_*.json` / `out/R5_*.json` evidence (tests log, salt check with the
secret's sha256 and each packet's salt, archive check, storage). R must still reproduce 68.77 [66.5, 71.0] and
64.94 [61.3, 68.4]. Nothing submitted or uploaded. Final message under 10 lines: hashes and test counts, including the
reviewer's three and test_prodroot.
