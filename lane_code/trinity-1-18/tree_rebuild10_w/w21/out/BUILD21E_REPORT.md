PASS: both resolver defects are fixed. Production execution remains unrun; GO stays false.

`work/build21/joblib.py` preserves JSONL members as hash-verified values. It requires single-document
JSON for the artifact, config, binding, preparation, model manifest and reachable metadata pins.
Metadata parse failures identify the member. Explicit removal-list pin positions use the line-record
reader; the same hash used in a metadata position still refuses. No hash check is bypassed.

`work/build21/kit.py` pins both identities, the original kit config, and the real config/binding/preparation
pins shared by e.json and r.json. The resolver checks the runtime identity against the artifact, binding
and preparation. Restoring the kit streams and preparation output must recover the kit identity.
`donor_config_sha256` receives the runtime identity. Evidence: `work/build21e/IDENTITY_READERS.json`.

- Kit identity: `774503e26f274a10c96ad06210d339c49ebc9a704ac254df81f389b0da4d98a1`.
- Runtime identity: `9459724f1b925b7d750628ccb36d7a29f871e953751c0e1d2c9abaea67d567e4`.

No sealed-tree reader needed a change. The export-only and persisted readers and handover donor
already use historical P `export_identity`; N preparation uses the current N identity independently.
`init_from_artifact` authenticates the artifact and export tensor pins and topology, not a kit identity.
P opener rows, the step-544 lineage path, admission, legality and the DEFERRED boundary are unchanged.

Other edits: `jobtest.py` models both identities; `resolver21e.py` contains the new tests; the `*21e.py`
helpers reproduce replay, tracing and delivery. `OPERATOR.md` specifies the exact listing fields and
resolve command. `work/build21e/LISTING_TEMPLATE.json` pins the eight production metadata entries.
`work/build21e/CHANGES.json` and `FIX.diff` record changed files and code details.

Real-byte fixture evidence: `work/build21e/FIXTURE.json`, `MUTATIONS_MAIN.json`, and `REAL_INPUTS.json`.
The old resolver raises exactly `JSONDecodeError: Extra data: line 2 column 1` on the real JSONL
members. With JSONL handling substituted, it raises exactly `E23` on the real artifact. The repaired
resolver passes. Repinned JSONL metadata refuses by member name; unknown or kit artifact identities refuse.
The fixture keeps all supplied real member and e/r/DONE/RP bytes. Missing archive members use tiny
placeholders with rewritten manifest hashes/lengths. Export parts and the completion marker use fixture
bytes. External metadata checks use a declared boundary stand-in because those bytes are absent.
The omitted archive tokenizer adds one fixture entry to the eight production external files.

Tests (overlapping suites are separate; counts and per-suite paths: `work/build21e/TESTS.json`):

| Suite | Tests | Failures/errors |
|---|---:|---:|
| resolver21e | 14 | 0/0 |
| resolver_edges21e | 1 | 0/0 |
| final_focused | 112 | 0/0 |
| edges | 4 | 0/0 |
| producer_edges | 11 | 0/0 |
| kit21c | 12 | 0/0 |
| naming21c | 23 | 0/0 |
| extra21c | 3 | 0/0 |
| naming21d | 16 | 0/0 |
| coverage21d | 1 | 0/0 |

Changed-statement coverage: 76/76 AST statement heads (`work/build21e/COVERAGE.json`).
Decoded scan: PASS, 76251 strings across 13 maps (`work/build21e/SCAN.json`).
The tree and staging paths did not change, so the conditional capacity restaging/q-preview rerun was
not required. The focused regressions cover the synthetic handover and initialization paths.

Real pre-forward reader replay (`work/build21e/REPLAY.json`; unchanged real pins, CPU):

| Reader | Result |
|---|---|
| p3_provenance.pinned/load: config | PASS |
| p3_provenance.pinned/load: artifact | PASS |
| p3_provenance.pinned/load: preparation | PASS |
| p3_provenance.pinned/load: binding | PASS |
| source_seal.check_binding:artifact | PASS |
| source_seal.check_binding:preparation | PASS |
| r1_persisted.verify: e.json/r.json | PASS |
| r1_handover.donor | PASS |
| r1_handover.compare_configs | PASS |
| r1_training.training_components | PASS |
| r1_handover.bind_target | PASS |
| p_opener_witness.prepared_vocabulary | REFUSE: base-model config/tokenizer metadata absent |
| p_opener_witness.produce | REFUSE: base-model config/tokenizer metadata absent |
| r1_training.start | PASS: step 400 |
| r1_persisted.admission(weights=False) | PASS |
| production_proof.bind_handover | REFUSE: N production r2_sampling has not been produced |
| r1_persisted.admission(weights=True) | REFUSE: production heads absent |
| r1_handover.donor_meta_model | REFUSE: base-model topology metadata absent |
| r1_handover.verify_trainable_groups | REFUSE: base-model topology metadata absent |
| carrier_c1_run.prepared:N | REFUSE: N scene-rebuild receipt has not been produced (exact pin required) |
| carrier_c1_run.init_from_artifact:lm | REFUSE: production export index absent |
| carrier_c1_run.init_from_artifact:heads | REFUSE: production heads absent |
| p_export_receipt.collect | REFUSE: production heads absent |
| mutation: donor receives kit identity | ValueError:P_EXPORT_CONFIG_MISMATCH |
| mutation: unbound export-only mode | ValueError:P_EXPORT_ONLY_PROOF_MODE_Q_REQUIRED_TRAINING_REFUSED |

No production tensor load or GPU forward is claimed. Initialization uses only model metadata attributes
and stops at real missing tensor I/O. The final N binder stops at its missing produced row plan.
These refusals preserve the production requirements; no identity or admission check was relaxed.

Delivery values below come from `work/build21e/DELIVERY.json`; every archive member was streamed
back and checked against `work/build21/PACKAGE_MANIFEST.json`.

- Package: `out/tree_rebuild_b21e_ac8fa8e3.tar` (gzip), 82937617 bytes; 4279 verified members.
- Package SHA-256: `9ca1907c5d07a38b83af10438badc1a81595aef3bf41cc9ed75db42b0daeff2e`.
- Package content seal: `ac8fa8e3bdc3f3e0f7b9da9b037430c46c94da1e0954003ebe703456dd3e9672`.
- Tree seal: `b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8` (936 files; unchanged).
- Kit q seal: `5d300f192c97134c441696df0ab09435e2ad15be879603b230e6cd0c5d615522`.
- Upload inventory: 137108099 bytes in 164 files; actual uploads: none.
- Changed uploads versus build 21c: `q/BUILD.json`, `q/SHA256SUMS.txt`, `q/b/z.py`, `q/k/p.json`.
  Exact before/after hashes and lengths: `work/build21e/UPLOAD_DIFF.json`.
- Bundled real fixture inputs: 81 files, 19113814 bytes.
- Workspace growth: 251054929 bytes, below the 2 GB limit.
- Both build-21c and build-21d packages and reports remain unchanged.
- Completed: 2026-11-19T10:33:48.539774+00:00.

The focused-suite prerequisites omitted from the earlier delivery remain listed in
`work/build21c/DEPENDENCIES.json`. No SSH, network, Orchard, GPU, Git, scheduler or agents were used.
The report and final package checksum stay outside the archive to avoid a circular checksum.
