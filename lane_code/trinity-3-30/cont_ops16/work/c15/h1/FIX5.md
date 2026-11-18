Cause: binding `/` read-only prevents missing logical parents; bwrap status 1 was mistaken for a measured gate failure.
`payload/g.sh:95`: build a tmpfs root with read-only host entries, recreated symlinks, private /dev, /proc and /tmp, and writable logical ancestors.
`payload/g.sh:119`: mount both pinned receipt aliases and writable BUN; retain user/uid/gid mapping, nice 19, offline settings and BUN/c caches.
`payload/g.sh:18,36,78`: refuse an existing gate.json; verify/reuse t/u against the archive bytes and pinned receipt/SQLite hashes, without deletion or overwrite.
`payload/g.sh:123`: require fresh bound JSON; pass is 0, measured false is 1, missing/invalid output or runtime failure is 2.
`tools/make_orchard.py:25`: package canonical g.sh unchanged so rebuilding cannot restore the broken sandbox; no other deployed executable changes.
`tools/build_gate_patch.py:1`, `build/g_patch.sh:1`: deterministic 13979-byte patch verifies old/new digests and retains g.sh.r4/sums.txt.r4.
Patch compatibility: p/e/staging/archive remain valid; z.sh derive/certify and s.sh use updated sums and bind the new g.sh in final external review; no full re-upload is required.
Apply the patch before gate/final evidence; its preflight refuses existing gate/ready/compare records or backups. Carry its body through the authorized wrapper, then rerun g.sh.
`tests/test_gate_sandbox.py:1`: real f.py/trainer and SQLite fixture; round-4 fails on an absent top-level parent, fixed script reuses its t/u and passes.
Gate tests PASS: failure->2, below-threshold->1, pass->0, missing/import/invalid reports, receipt binding, existing top-level parent, mount properties and tamper refusal.
PASS: four originals, stop_bridge, fix1, visible_names, sealed_modes, runtime_inventory, four runnable reviewer checks; review harness syntax only (`evidence/fix5/tests.json`).
PASS: patch preservation/refusal tests and repeated deterministic transport/patch builds (`evidence/fix5_patch/results.json`, `evidence/fix5/package.json`).
g.sh SHA256: c277738e63881e13d089e0379ef8dd3d823ec2010240afc32fae1b489c2e1630 -> 757a00e4c338d28f05d6b560b6aa339463068e5add707f09b34b0712875cefda.
sums.txt SHA256: 308ba77b881ddb2c2021e07436c0bf9e2a62873598098687cec5dcec096a725d -> d23b6e394df2a6de73c4eec95e83e7dda6cf84348494b962e2c796dfcaea8958.
Upload SHA256: fd50d3b218f6d478aeea8d4e0e680ce33c141e67db288ea2258bfe708176bf3c -> d1279a8677c91e577d67933139bd52e320d9054b999d99b2d9a2b447d794ceb2; orch_h1.sh: 87fb17b7c50f675122ccce6f2bc8aad10f6ec2bf7312ece25cdfc19c94ee1acb.
Patch SHA256: f240e251f52780468c43bd8e4274ab0c416e1ed46a18b029a9bc0f0ef892312c. All affected hashes are in evidence/hash_changes_fix5.json and sealed by SHA256SUMS.txt.
Identity 6e4f2846e45377f5b25da0113bf70d625d41d0bee80ae26840d2dee839f85965 and contract 9a5270923627a9fae982acf90ac20ee4b695ac1932b98ae13038b63710a03ff9 are unchanged; trainer, fixture manifest and batch wrapper are unchanged.
Tests used local bubblewrap 0.4.0; Orchard 0.9.0 remains untested here. Work was local/CPU-only; no SSH/network/Orchard/GPU/Git/deletion or chain creation/runner edit occurred.
