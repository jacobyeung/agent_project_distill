**REVIEW_VERDICT_DERIVE_KIT**

**GO AFTER FIXES.** The tool reproduces the supplied records, but it does not enforce a complete, data-only derivation. It accepts inconsistent config/deployment pins, retains stale launch metadata and authorization evidence, and permits changes outside its stated scope.

All paths below are relative to `/scratch/jjyeung/orch_n30/cont_ops`. No SSH, submission, or workspace edits occurred.

**1. Binding requirements derived from the sealed records**

The active configuration is `k/b02e4385.json`, selected by `k/1.json["0"]` and pinned independently by `k/launch.json.config`. It binds four streams—pose, VQA, routing, pointing—with no MDG stream.

| Change | Bindings that must agree |
|---|---|
| VQA row store | Config `streams.vqa`; receipt’s database pin and dependencies; staging coverage in `0.json.extra`, `tars`, or `staged_inputs`; launch `inherited_streams.vqa`. The original active VQA receipt/database are in `extra`, not `tars`. |
| Routing row store | Config `streams.routing`; receipt/database dependencies; corresponding staging entries—originally the r16 entry in `0.json.tars`; launch `inherited_streams.routing`. |
| Pool selection | `k/pool_selection.json`; config `s1_routing.selection`; launch `source_selection`; catalog mappings for referenced hashes; affected manifests, indices, exclusions, row packages and their staging inventories. |
| Init artifact | Config `init_artifact.artifact`; matching `0.json.init` after converting `path` to `file`; staging coverage for the artifact, heads, full-weight manifest, index and shards. Preserve `lm` and `heads` unless explicitly changing training settings. |
| Run identity | `run_key`, config `output` and `preparation_output`, launch `run_directory`, a distinct `persistent_run_root`, and `in_job_admission.directory == output + "/inputs"`. |
| Any config change | Config filename/key, `1.json`, launch config file hash, native config identity, source-seal config hash and seal digest, and manifest. Review/staging must cover the new identity; authorization must cover its scope. |

The native identity excludes `preparation`, `admission`, `authorization`, `milestone_gate`, and `readout.contiguous_clips`, with the additional `frame_layout=="spread"` normalization (`b/i.py:95–101`). The config filename instead hashes the complete compact config; the file hash includes its newline.

The trainer archive, `7.json`, `s1_record.json`, source revision, `b/`, job scripts, recipe, route policy and unaffected inputs should remain unchanged. Frame mappings and scene-census evidence need revalidation when the new rows change their coverage. These relationships follow from `b/g.py:55–116`, `b/d.py:16–134`, `b/c.sh:127–167,217–262`, and `b/s.py:176–196`.

**2. Findings**

1. **P1 — Config and staging can disagree without a derivation error.**  
   [derive_kit.py:44](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:44) applies config overrides independently of deployment overrides at lines 53–56. No check connects stream receipts, their database pins, pool metadata, or init artifacts to the staging plan.

   In-memory execution confirmed that `streams_only` and `init_only` overrides emit kits with **unchanged `0.json`**. Both supplied stand-in overrides also leave the new VQA/routing receipts uncovered by their staging plans.

   **Minimal guard:** validate the complete dependency chain from each active config pin to its staged bytes. Require config init and deployment init to match. For an intended row-store replacement, verify the expected database hash as well as the receipt hash.

2. **P1 — “Data-only” is not enforced.**  
   [derive_kit.py:33](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:33) permits arbitrary drops/additions; lines 44–55 permit arbitrary config/deployment replacements. An ordinary `recipe.learning_rate` change was accepted. `add_k` names also lack containment checks: `../b/g.py` can target the copied gate.

   **Minimal guard:** reject unknown overrides, allow only approved changed fields, protect source/runtime records, and require safe basenames for added records. Compare the final configuration and executable inventory against the baseline outside the allowed changes.

3. **P1 — Run identity can remain partially old.**  
   [derive_kit.py:26](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:26) defaults to the old run and kit keys. Lines 41–43 rewrite output suffixes, but lines 64–65 leave `persistent_run_root` unchanged unless supplied.

   A `run_key`-only override retained `/home/jjyeung/okit/r/5da50f2b`. `r8.py:93–100` normally rejects an existing marker for another run; that is a late failure, not correct derivation.

   **Minimal guard:** require a complete new run identity for changed inputs, including a distinct persistent root, and assert all output-path relationships.

4. **P2 — Launch provenance remains stale.**  
   [derive_kit.py:57](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:57) copies the launch record but never updates `inherited_streams` or `source_selection`. Both stand-in results retain the original VQA/routing entries in `inherited_streams`.

   **Minimal guard:** derive these launch fields from the selected stream and pool inputs, then assert agreement.

5. **P1 — Output readiness and evidence are incomplete.**  
   [derive_kit.py:64](/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py:64) retains `READY` and `production_authorized:true` by default. It carries the old `4.json`, review and staging evidence. It never creates root `ANON_OK.json`, which `b/a.py:9` requires. Lines 70–72 silently omit absent files from the new manifest, although `0.json` still references both missing tars.

   `4.json.config_sha256` remains old; neither `g.py` nor `i.authorize` checks that field. Replacing review/staging therefore does not repair the authorization scope.

   **Minimal guard:** emit changed kits as blocked pending applicable evidence, create an explicitly unreviewed manifest certificate, and distinguish incomplete reproduction fixtures from deployable kits. Verify the source manifest and require its referenced payloads for deployable output.

**3. Reproduction result**

The requested disk invocation failed at `out.mkdir()` because the sandbox also makes `/tmp` read-only.

I then executed the unchanged `derive()` implementation with filesystem operations backed by memory:

| Check | Result |
|---|---|
| `k/launch.json` | Byte-identical |
| `k/0.json` | Byte-identical |
| `k/1.json` | Byte-identical |
| `k/b02e4385.json` | Byte-identical |
| `k/7.json` | Byte-identical |
| Manifest, excluding the two absent tars | Byte-identical |
| Present input files against sealed manifest | All matched |

The omitted files were exactly:

- `k/np226_5204b3a0.tar`
- `k/t_e6456bcecb8d4a8f4f68158eb68275f8befff128.tar`

The reproduced config identity was `a7ad7051246ac58fb2aed30af0e992509e19486f4ba9c9bcba67f44613ba09ca`.

This establishes serialization and transformation behavior, **not a completed disk rerun**. The inspected trainer source files matched `7.json`, and every supplied `src/launch_s1/b` file matched the kit’s `b/`.

**4. What the gates catch**

**Yes, the tool can emit stale pins despite the caller’s intent.** However, inconsistent pins do not generally cause silent fallback to old data.

The distinctions below assume a valid new manifest certificate and applicable review/staging evidence. Without those, the earlier gates already stop execution.

| Inconsistency | `g.py`, `a.py`, `d.contract` | Native admission/training |
|---|---|---|
| Streams changed; staging still supplies old rows | `g.py` rejects the old review because config identity changed. With matching evidence, these checks do not compare config against the staging plan. | Missing/new-hash-mismatched receipts or databases fail. Correct new inputs already present can satisfy admission despite redundant old staging entries. |
| Config init changed; `0.json.init`/tars remain old | Same review rejection; no direct config/deployment equality check. | Parent grounding selects the **config-pinned** artifact. Missing or mismatched new artifact/metadata fails; it does not automatically substitute the old parent. |
| `pool_selection.json` replaced at the same path; config selection/catalog remain old | Config identity can remain unchanged. `g.py` does not read the pool file; `a.py` checks manifest consistency, not this relationship. `d.contract` accepts it. | `s1_pool_relocate.py:11` rejects the selection’s hash mismatch. |
| New pool record added under another name, or new staging inputs supplied, while active config remains old | These changes need not invalidate the old config identity. | The old pinned inputs may still be used successfully. No gate can infer the caller’s unrecorded intent. |
| New selection pin but stale catalog | No catalog-closure check in those gates. | Each resolved input is hash-checked. Missing mappings may fall back to original paths; execution fails if those inputs are unavailable or differ. |

Relevant checks are `student_pilot/p3_provenance.py:37–42`, `carrier_c1_data.py:543–551`, `s1_pool_relocate.py:11–19`, and `mdg_parent.py:40–54`.

`d.effective` additionally binds generated receipts to the reviewed config, original stream pins, routing inputs and parent (`b/d.py:64–101,109–134`). It does not compare them with `0.json`.

For this four-stream configuration, parent admission explicitly verifies metadata without verifying every parent-weight payload (`mdg_parent.py:66–74`). Full staging/loading remains necessary.

In-memory negative tests confirmed that `d.contract` accepted all three partial-change examples. Replacing only pool-selection bytes reached `g.py`’s persistence stage; persistence was stubbed, so this was **not** a full gate pass. The supplied `TEST_review.json`/`TEST_staging.json` likewise reached that stage despite stale `4.json`; their labels are not independent review evidence.

**5. Old-review rejection**

The actual harness ran successfully:

```text
bash work/d0/harness/gate_check.sh \
  /scratch/jjyeung/orch_n30/cont_ops/work/d0/t2_pass1 p
```

It rejected the existing derived kit at `b/g.py:103`:

```text
ValueError: Independent admission is not bound to the launch configuration
```

That kit’s gate matched the sealed gate. The newly derived pass1 result also produced this rejection in memory.

**6. Complete carried-file inventory**

By default, the tool copies **89 existing files** without regenerating them: 56 under `k/`, 31 under `b/`, and both job scripts. `add_k` can replace copied records; those replacements are caller-supplied, not regenerated evidence.

| Carried `k/` files | Binding retained |
|---|---|
| `4.json`, `review.json`, `staging.json`, `binding_evidence.json` | Old configuration authorization, review, staging and supporting admission evidence. They do not establish the derived run’s approval. |
| `28429cf9.json` | Old run `469ddece`, original streams, pool and init. An inactive config copy. |
| `c1d5e631.json`, `c1d5e831.json`, `prep_c1d5e631.json` | Earlier run/preparation identities and original stream/init inputs. |
| `7.json`, `s1_record.json`, `t_b01ce449beffe35b.tar`, `archive.json` | The unchanged trainer tree/archive. Reuse is appropriate for a data-only derivation. |
| `pool_selection.json`, `pool_manifest.json` | Original selected population and source metadata. |
| `pool_exclusion_0.tsv`, `pool_exclusion_1.tsv`, `pool_exclusion_2.tsv` | Original pool exclusion memberships. |
| `pool_indices_0.json`, `pool_indices_1.json`, `pool_indices_2.json`, `pool_indices_3.json`, `pool_indices_5.json`, `pool_indices_6.json`, `pool_indices_7.json`, `pool_indices_8.json`, `pool_indices_9.json`, `pool_indices_10.json`, `pool_indices_11.json`, `pool_indices_12.json` | Original source-specific selections. There is no `pool_indices_4.json`. |
| `scene_reference.json`, `dev_scene_exclusions.json`, `benchmark_scene_exclusions.json` | Original held-out scene policy/reference and census evidence. Revalidate their coverage for changed populations. |
| `frame_map.jsonl.gz`, `frame_plan.json.gz`, `frame_rates.json` | Original frame locations/hashes, extraction plan and source-derived FPS evidence. |
| `input_mdg_clips.json`, `input_mdg_rasters.json` | Original MDG inputs, despite MDG being absent from the active mix. Raster inputs remain referenced by staging. |
| `input_source_tokenizer.json` | Original tokenizer metadata; retain if tokenizer unchanged. |
| `8957d119.json` | Original pose mixture and source pins. |
| `600ef69d.json`, `dafa4a9c.json`, `932c0c4e.json`, `99e6eed6.json` | Original scene/pose/report exclusions. |
| `66c427e2.json`, `c2db2a1a.json` | Original question-ID exclusion sets. |
| `remove_0.jsonl`, `remove_1.jsonl`, `remove_2.jsonl`, `remove_3.jsonl`, `remove_4.jsonl`, `remove_5.jsonl` | Original row-removal rules. |
| `routes.json` | Frozen route policy, not a row-store identity. |
| `8.json`, `cf50c7ce.json` | Earlier routing-build input specification, source pins and output location. |
| `r.json` | Older trainer-runtime record for revision `31b57cf…`; active deployment uses `s1_record.json`. |
| `6.json` | Training wall-time metadata. |

The 31 copied `b/` files are:

```text
a.py ab.py b3900003.py c.sh d.py f2.py g.py gcsput.py h.py i.py
jc1.sh jp0.sh jt8c.sh kitx.py opaque.py p0.py p0.sh profile.json
q0.py r.sh r8.py rd.py s.py sg.py v.py w.py wh.json x.py z.py
sa/prestage_hooks.py sa/sitecustomize.py
```

`job.sh` and `job8.sh` are also copied unchanged.

`ANON_OK.json` is **absent**, not carried or regenerated. `world8.json`, `candidates.json`, `candidate_1.json` and `candidate_2.json` are absent and remain absent. The two missing tars remain absent even though their deployment pins survive.