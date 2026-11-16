# REVIEW_JOB_B_R9

## 1. Configuration, contract, and pin closure

**PASS for the scoped review attestation.** Recomputed using `out_b_t3`’s own `b/i.py` and `b/d.py`:

| Item | SHA-256 |
|---|---|
| Configuration identity | `3ec51ba9f853e1b20bda0dd07d125e0a84d41384b1af8ee0fc94972e7434342d` |
| Admission contract | `aaf2d7b045632f14d96cfc62adbf2a1eab5212d713ac6ebaed03c1b44309ca19` |
| Config file bytes, `428d1cfa.json` | `8316911be254036461dee80d9031474fe825a0e4f6583c839eba12cd0b91a7f1` |

The config differs from the sealed config only in the six requested locations: `streams.vqa`, `init_artifact.artifact`, `s1_routing.selection`, `s1_routing.catalog`, `output`, and `preparation_output`.

Verified:

- `receipt_b.json` differs from `r_orchard_v4.json` only in `database.path`. Its pin is `bfabb1f0`; it names rows `444fa953` and the unchanged sealed division `0d28fdd4`.
- Artifact `1d6eeb28` pins heads `8bb5e151` and full-weights manifest `211ae87b`. The manifest bytes equal the repack receipt’s embedded bytes. Its five shards, index, and manifest match all seven corresponding repack members.
- Selection `f232d416` is byte-identical to `bb5483e7` after replacing only `route_planning_moved_to_vqa_store_d0` with `moved_to_vqa_store`.
- `k/0.json` removes the m200 tar, adds m544 with exactly nine matching member hashes and stream hash `42457dbd`, updates `init`, and adds the rows and receipt extras. No other deployment changes appeared.
- All `b/` files remain byte-identical to the sealed kit. The trainer archive matches its sealed hash. `make_over_b.py` reproduces `over_b.json`.

The division remains supported by the sealed receipt; `S.sha256` remains an explicitly waived provenance input. These checks establish pin closure, not a fresh read of remote payloads.

Suggested `attestation` text, with `verdict: "PASS"` and `admission_scope: "pinned-template-and-native-data-derivation"`:

> Independent review of source seal sha256:b01ce449beffe35be3bf0b48ad3d69f331f1523f96a69cbd3d10aab3dbb42a99 and configuration identity 3ec51ba9f853e1b20bda0dd07d125e0a84d41384b1af8ee0fc94972e7434342d, including the pinned-template-and-native-data-derivation admission contract with digest aaf2d7b045632f14d96cfc62adbf2a1eab5212d713ac6ebaed03c1b44309ca19, verdict PASS. Basis: independently recomputed both digests using the derived kit’s own gate code; verified the permitted configuration changes, unchanged gate code and sealed trainer archive, receipt and selection bindings, and all nine export-member pins against the repack receipt. This review extends the supplied sealed-source review; it does not claim a fresh audit of the entire trainer. Remote payload bytes and upload capabilities were not independently checked. Job B’s native real-data derivation, parent-grounding checks, all-rank GPU first-step admission, resume and export remain mandatory and are not claimed to have passed. This attestation does not grant submission authorization.

## 2. Authorization

**`4b.json` is structurally valid for `p`, `t`, and `u`.** Relative to sealed `k/4.json`, only `config_sha256` and `scope` change.

- `p`: authorization and `x.ready` pass.
- `t/u`: resource checks pass for one node and four GPUs. `x.ready` passes when supplied a preparation binding.
- The raw fixture cannot yet pass `t/u`: it lacks Job B’s native `inputs/data_receipt.json` and effective preparation. The preparation-binding test used synthetic data solely to isolate authorization checks.
- `resume: "latest"` supports `u`; it does not prove a resumable checkpoint exists.
- Expiry is `2026-11-26T00:00:00Z`.

The inherited authorization remains conditional: `production_go_granted` is false, separate GO is required, and its historical evidence does not establish Job B’s admission.

**The fixture still carries the old `k/4.json`, review, and staging records.** Install the new authorization and identity-bound evidence during the final derivation.

## 3. Wrapper

**The executable diff is limited to paths, removal of `-J/-o`, and the two added checks; comments also change.** The submission command must supply the removed options. The entire restore-through-exit suffix is byte-identical to the earlier wrapper. `bash -n` passes.

The session check requires **44 keys**: eight configured milestones plus `mstop`, `mstopB`, and `mstopC`, each with four parts. They exactly match:

```text
q8/8865619b/359fcc3c_<m>.tar.part00-of-04
…
q8/8865619b/359fcc3c_<m>.tar.part03-of-04
```

`c.sh` retains `K=8865619b`; `gcsput.part_names()` produces the same names. A missing file, missing key, invalid JSON, or mode other than `0600` causes exit before restore or training.

The check establishes key presence and file mode, not session validity or usability. No session file was opened during this review.

`vt.py` runs before restore. Neither addition resets `TK_JOB_START`, changes trainer arguments, nor changes slot logic. Their runtime consumes the existing wall-clock budget.

## 4. ANON pre-scan

**NOT CLEAN: six new local Trinity paths in [over_b.json](/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/over_b.json:10).**

All share `/scratch/jjyeung/orch_n30/cont_ops/`:

| Line | Remaining path |
|---|---|
| 10 | `work/d0/v1/pool_selection_aa128e6f.json` |
| 80 | `work/d0/base/runs/469ddece/m544/artifact.json` |
| 81 | `work/d0/jobB/full_weights.json` |
| 82 | `work/d0/jobB/receipt_b.json` |
| 392 | `work/d0/v1/E00_MEMBERS.json` |
| 397 | `work/d0/v1/sealed_vqa_receipt.json` |

Replace these with neutral, valid bundle locations before carrying `over_b.json` to Orchard.

I scanned all five changed manifest records and the five specified external files. The other nine files have **no new identifying hits**. The scan counted 358 inherited matches separately and three Python `.split()` calls.

The supplied R8 review file is absent; I recovered the scan rules from `PROMPT_derive_confirm8.md`. The current `ANON_OK.json` remains `UNREVIEWED`; this pre-scan cannot certify the future final manifest.

## 5. Staging attestation

The required fields are:

```json
{
  "status": "PASS",
  "source_revision": "sha256:b01ce449beffe35be3bf0b48ad3d69f331f1523f96a69cbd3d10aab3dbb42a99",
  "config_sha256": "3ec51ba9f853e1b20bda0dd07d125e0a84d41384b1af8ee0fc94972e7434342d",
  "missing": [],
  "project_community_write_bytes": 0
}
```

The zero-write claim must describe the staging-verification operation, not Job A’s repack or training writes.

I confirmed that Job A’s `k/0.json` differs from Job B’s only in the two extras and the m544 entry’s expanded member list and stream pin. Taking the reported Orchard checks as supplied evidence:

- Job A’s successful staging supports unchanged inputs.
- Its repack receipt and `vt.py` PASS support all nine m544 members, including the six newly explicit shard/index entries.
- The v4 store’s Orchard hash check supports rows `444fa953`.
- **Those checks do not establish the new uploaded `vb.json` bytes.** Record its Orchard hash as `bfabb1f0b08327102afbb6997d3bc142b5ab630f3748ba358ba758bd1f04e1ef` and verify the final kit’s arrival hashes.

Job A’s preparation cannot substitute for Job B’s native admission under its new identity.

**GO AFTER FIXES:**

1. Replace the six identifying paths in the carried override file.
2. Verify uploaded `vb.json`; issue the new staging and review records, and install `4b.json`.
3. Derive the complete `READY` kit from the sealed kit, regenerate its pins and manifest, and scan the final carried contents before issuing `ANON_OK.json`.
4. Retain the authorization’s separate submission GO and mandatory native admission gates.