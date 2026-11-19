The kit remains GO=false. Nothing was submitted. Run the commands below only after reviewing the delivery and supplying the missing pinned inputs.

Before submission, the operator creates these opaque links. The job authenticates the linked metadata archive and model archive against `k/p.json` before staging.

```bash
ln -s /project/community/jjyeung/distill/okit /project/community/jjyeung/okh7/l_94a76bda
ln -s /project/community/jjyeung/cp4tk_rt/kit/model_qwen35_9b_c2022362.tar /project/community/jjyeung/okh7/l_3d48eea0
```

If a link already exists, check its target and pinned content. The delivery does not replace it.

The upload inventory is `UPLOADS.json`. Its entries specify every local file, opaque destination, SHA-256 and byte count. From the extracted delivery, the supplied `upload.py` checks every file before writing to N's new pool folder. It never writes into P's kit or run.

```bash
python3 work/build21/upload.py "$PWD" /project/community/jjyeung/okh7/x_22c714e1
```

The resolver requires the verified four-part export listing and pinned external tokenizer metadata. It checks P's export-only receipt, small-file archive, part lengths, individual hashes and combined hash. Native export files are staged together under their original manifest sibling names.

Mode q also requires authenticated host envelopes for all bound routing slices, with exact row membership, RGB joins, scene coverage and extent receipt. A missing input must remain a refusal. `proofs/receipts/RESULT.json` lists absent dependencies by SHA-256 and original path. The local capacity proof does not supply production RGB, model shards or host envelopes.

The scanner checks every decoded operational map key and value, including `k/p.json` and its `p_files` inventory, nested staging payload paths, shell arguments, Python path literals and result archive member names. The job checks dynamic export and snapshot member names before writing them, and checks each authenticated directory map before staging it. Sealed source inventories and input-data schema fields retain their authenticated identities. The exact scanner inventory and runtime-only map pins are in `../build21c/SCAN.json`.

The result archive contains the proof result and a separate room census. The census cannot admit a failed proof.

The exclusion payload stages as `k/3119aa4a.json`. Its SHA-256 remains
`3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970`.
The authenticated `p_sources` map reads the same bytes from N's `u/<sha256>` upload.
Configuration pins and hash-keyed catalogs use the pinned opaque map. P's original files remain unchanged.

Upload total: 137103557 bytes in 164 files (source: `UPLOADS.json`).

The focused test fixture closure would add 202336662 bytes.
The delivery includes 22066639 bytes of smaller fixture inputs; the remaining prerequisites,
their hashes and paths are listed in `../build21c/DEPENDENCIES.json` under `omissions`.
The full focused suite therefore requires those listed inputs after unpacking.
No checkpoint, database or frame set is bundled for test replay.
The source tree remains sealed as `b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8`.

To replay the focused suites once the listed prerequisites are available, use the supplied environment
and run `nice -n 10 bash work/build21/run.sh work/build21/focused.py` from the delivery root.
The test helpers and the small baseline source/inputs are included. The original path identities in
authenticated records remain pinned; `B21C_PORTABLE=1` redirects bundled prerequisite reads by the
explicit dependency map without changing their bytes.
