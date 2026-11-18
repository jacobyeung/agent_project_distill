Cause: whole-tree mode inventory compared 90 unmanifested runtime entries present only in the real source kit; shared member modes matched.
`tools/sealed_output.py:7,20,24` / `payload/d.py:51,64,68`: inventory SHA256SUMS members, their ancestor directories and the root only.
`tools/make_deriver.py:138` generates `payload/d.py:567,627`: validate and copy only sealed members; never walk source runtime trees or copy unlisted b/k files.
`payload/d.py:417,653`: restrict source JSON dependency reads and overwrite checks to manifest membership.
`payload/d.py:632,702`: create fresh empty 0700 runtime directories and an UNREVIEWED certificate; do not read or copy source runtime state or its certificate.
`payload/r.py:55,83,88`: prepare, final comparison and mode digests share the scoped inventory; z.sh dispatches these checks.
`tests/test_runtime_inventory.py:1`: exact 193-entry SRC fixture includes all 90 runtime entries; fix-3 fails at member modes, current prepare/empty/final/certify pass.
The fixture denies unlisted source opens/stats/traversal, ignores poisoned b/k records and a dangling link, and rejects sealed-file/directory/root mode differences.
`tests/test_sealed_modes.py:28,77`: reproduction helpers compare sealed scope; six permission derivations, restoration, confinement and certificate writes pass.
PASS: four originals, stop_bridge, fix1, visible_names and four runnable reviewer checks; review harness syntax passes. Evidence: evidence/fix4/tests.json.
PASS: deterministic repeated upload/fixture builds, independent trainer rebuild, archive metadata, embedded transport and payload sums (evidence/fix4/package.json).
REVIEW4.md covers orch_h1/o/prepare/stage, g, z/final/certify, s, v and jb preflight, with OK/FIXED verdicts and retained prerequisites.
Changed d.py SHA256: a82b01974363e15574a65820876e29a3c8a0b4b076f144bc9642c3667848f548; r.py: 6d47561ea169159695261682f741794ef8b2ecfe78bf343892872b5979b3f45f.
Changed sums SHA256: 308ba77b881ddb2c2021e07436c0bf9e2a62873598098687cec5dcec096a725d; orch_h1.sh: e0b8f429ab7d0e6bff49b24de7bb0d926b8a2b55f9dacdcbbe27906bb76800b4.
Upload SHA256: 620e72ebf6c2727b920767d8fd9f4f5b092af513168c1f8bf2f7c89a52df5a9c -> fd50d3b218f6d478aeea8d4e0e680ce33c141e67db288ea2258bfe708176bf3c (build/p_fd50d3b218f6d478.tar).
All changed file hashes are in evidence/hash_changes_fix4.json; SHA256SUMS.txt seals that record, current reports and evidence.
Identity 6e4f2846e45377f5b25da0113bf70d625d41d0bee80ae26840d2dee839f85965 and contract 9a5270923627a9fae982acf90ac20ee4b695ac1932b98ae13038b63710a03ff9 are unchanged; all IDs, trainer pins, fixture manifest and wrapper are unchanged.
The operator must rename i_1be16f28 to i_1be16f28.f2 before re-upload; the target-exists refusal remains active.
Work was local and CPU-only. No SSH/network/Orchard/GPU/Git/deletion, chain creation or chain-runner edit occurred; the four-rank harness was not run.
