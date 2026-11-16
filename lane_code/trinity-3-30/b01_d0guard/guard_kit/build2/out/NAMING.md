# Naming status

Runtime naming is incomplete and blocks release (`NAMING.json`). Outer candidate metadata member names are opaque, and unpacking reproduces every original file byte (`NAME_ROUNDTRIP.json`). The config and item projections round-trip exactly, but the runtime does not consume them (`NEUTRAL_CONFIG_PROJECTION.json`, `OPAQUE_ITEMS.json`).

The required trainer inventory contains prohibited names, including `trace_format/vsi_scannet_vocab.json` (`NAMING.json`). Its unchanged source verifier hashes relative member names as well as file bytes (`guard_kit/sj/orch_cd/evalx/work/milestone/native/out2/runtime_tree.py`). Renaming those files changes the required source-tree identity. The signed training configuration also binds nested paths and keys; rewriting them changes the required config identity (`CLOSURE_ADMISSION.json`).

`NAMING_OCCURRENCES.jsonl` lists every matched textual occurrence in the shipped code with a file and line. Code identifiers and prose are distinguished from the unresolved operational literals. `CLOSURE_NAMING_OCCURRENCES.json` lists signed metadata occurrences. `NAMING.json` lists the actual baseline-config occurrences and trainer member names. These lists are evidence of unfinished migration, not exemptions.

The job name, packet directory, return prefix and outer metadata members are neutral (`guard_kit/packet.py`, `FAMILY.json`, `candidate_m50/CLOSURE.json`). The internal request keys, capture-scope names and authenticated dependency paths remain unchanged. A complete solution needs a reviewed representation that preserves canonical source/config identities while translating all operational names; that representation is not delivered here.

No original-to-opaque map is treated as a completed migration. `TRINITY_NAME_MAP.json` and `TRINITY_KEY_MAP.json` remain build-side evidence. Operator source-copy commands appear in `RUN.md`; they preserve the source bytes but do not resolve the remaining runtime names.
