# REVIEW_CONFIRMATION_DERIVE_KIT_R5

**GO AFTER FIXES.** The named regressions mostly reject, but archive enforcement, sealed-file collisions, and the Job A→B lifecycle remain unresolved.

Reviewed `derive_kit.py` SHA-256 `ef166e88696e22ff40b159fb4f4f44a0002c079f5b9d19af6990b89139c3cb15`. The saved `derive_kit_r5.py` matches the round-4 reviewed hash. I ran in-memory probes and inspected the supplied **75-check, FAILS 0** log. I did not rerun the write-producing suite, submit jobs, or write files.

| Round-4 required fix | Verdict | Evidence |
|---|---|---|
| **1. Preserve inherited catalog closure** | **FIXED** | Every sealed mapping must remain unchanged. Removing a mapping with the sealed selection retained rejects. [derive_kit.py:224](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:224). |
| **2. Replace untrusted small-member evidence** | **PARTLY FIXED** | `small_members` now rejects, and `sealed_docs` hashes must match sealed stream receipts. However, the fallback accepts a sealed pin even when a new placement explicitly supplies different bytes at that path. [derive_kit.py:198](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:198), [230](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:230). |
| **3. Protect runtime executable/import destinations** | **FIXED for declared placements** | The reported FLA `sitecustomize.py` addition rejects; X destinations and executable suffixes are restricted. Undeclared archive members remain covered by fix 4 below. [derive_kit.py:296](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:296). |
| **4. Bind inventories to actual archive contents** | **PARTLY FIXED** | Names-only READY rejects, foreign export names reject, and manifest-backed listings must match exactly. These checks still compare declarations: runtime extracts every actual member without enforcing that inventory or the archive hash. [derive_kit.py:271](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:271), [c.sh:151](/scratch/jjyeung/orch_n30/cont_ops/work/d0/v1/out_v1_t5/b/c.sh:151). |
| **5. Validate status-only preparation requests** | **FIXED** | Status-only `PREPARATION_ONLY` rejects. Changed derivations require a fresh identity-bound `4.json` with exactly `["p"]`. [derive_kit.py:432](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:432). |

**Round-4 probe recheck**

- Hidden AS extra under `X/u`, hidden tar member under X, runtime database waiver, and init declaration without placement: **reject**.
- Unchanged-selection catalog removal, `X/b/i.py`, `X/b/g.py`, both traversal paths, e00/a1rows part reuse, and a1rows destination collision: **reject**.
- Fabricated `small_members`, FLA `sitecustomize.py`, foreign export names, and a declared executable archive extra: **reject**.
- Status-only preparation: **reject**, with source/output operations mocked to reach that branch.
- Omitted actual archive members: **still unenforced**.

**New defects and remaining blockers**

1. **`sealed_docs` can conceal a conflicting placement.** I retained the real VQA receipt’s division pin, added an extra containing `{}` at that division’s AL path, and added a catalog mapping that reaches the replacement. Closure **accepted** while reporting the original division as closed by sealed admission. Runtime stages small inputs before extras, so the extra overwrites the required division. Reject explicit conflicts before applying sealed fallback, and protect unenumerated sealed destinations. [derive_kit.py:230](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:230), [c.sh:315](/scratch/jjyeung/orch_n30/cont_ops/work/d0/v1/out_v1_t5/b/c.sh:315).

2. **Archive evidence does not survive as an enforced runtime constraint.** `tar_members` is not written into the deployment entry. `tk_stage_tars` extracts first and hashes only `files`; extra members can therefore evade the data-only checks. Also, the full-weights requirement runs only when init changes relative to the source kit. Promotion from a complete names-only preparation kit must revalidate this requirement too. [derive_kit.py:266](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:266), [c.sh:141](/scratch/jjyeung/orch_n30/cont_ops/work/d0/v1/out_v1_t5/b/c.sh:141).

3. **Preparation claims the persistent training run.** `g.check(..., "p")` calls `persistent_launch`; `r8` chooses cold-start mode and creates `RUN.json` with Job A’s ID. Job B then fails with **“An earlier run leg or state slot exists; refusing a cold restart.”** I reproduced that second-job rejection in memory. Preparation must avoid claiming the training leg, or the lifecycle needs an explicit supported handoff. [g.py:88](/scratch/jjyeung/orch_n30/cont_ops/work/d0/v1/out_v1_t5/b/g.py:88), [r8.py:98](/scratch/jjyeung/orch_n30/cont_ops/work/d0/v1/out_v1_t5/b/r8.py:98).

4. **Existing `m.tar` bypasses repack verification.** `ja.sh` skips repack whenever the destination exists, without requiring its verified receipt or checksum. This also skips receipt recovery after an upload/receipt failure that occurred after the tar was published. Require verified reuse or fail explicitly. [ja.sh:14](/scratch/jjyeung/orch_n30/cont_ops/work/d0/job/ja.sh:14).

**Real D0 v1 and Job A**

`make_over.py` reproduces `over_v1.json` as JSON. Real v1 closure passes: four new documents walked, eleven additions, nine removals, seven chained export members. The sealed division and provenance-only source are reported separately.

`out_v1_t5` remains **FIXTURE / unauthorized**, has `ANON_OK=UNREVIEWED`, retains the old authorization, and lacks the two sealed tar payloads. It cannot run as supplied. With an identity-bound preparation authorization and preparation status substituted in memory, **`g.py` before persistence and `i.authorize(..., "p", "0")` pass**. `a.py` correctly refuses the supplied unreviewed certificate. The packet’s rebuild and scan steps are necessary.

The repacker implements the claimed **input integrity chain**: generation-qualified reads, per-part size/hash checks, whole-stream size/hash checks, member-name comparison, artifact/head/manifest hashes, and every manifest-listed file hash. It verifies the project copy before renaming. The GCS upload check verifies **size only**, and the repack receipt is not enforced by subsequent staging. [repack_m544.py:25](/scratch/jjyeung/orch_n30/cont_ops/work/d0/job/repack_m544.py:25), [86](/scratch/jjyeung/orch_n30/cont_ops/work/d0/job/repack_m544.py:86), [105](/scratch/jjyeung/orch_n30/cont_ops/work/d0/job/repack_m544.py:105).

The packet also understates writes: mode p creates project `KH/arm`, `KH/runs`, persistent-root marker files, and shared node-local `/tmp/jjyeung/okit_8865619b` staging/run trees beyond the repack work directory. These follow explicit code paths; include them in the stated effects. [c.sh:394](/scratch/jjyeung/orch_n30/cont_ops/work/d0/v1/out_v1_t5/b/c.sh:394), [r8.py:71](/scratch/jjyeung/orch_n30/cont_ops/work/d0/v1/out_v1_t5/b/r8.py:71).

**GO AFTER FIXES:**

1. Reject conflicting sealed placements and protect unenumerated sealed files.
2. Enforce actual archive contents before extraction, including during READY promotion.
3. Fix the preparation-to-training persistent-run handoff.
4. Verify existing `m.tar` before reuse.
5. Complete the preparation kit, authorization and scan; document all write paths.