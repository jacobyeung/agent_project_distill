The H1 packet pins the exact regenerated selection and its EQUAL report. Native validation, authentication and the routing implementation check pass on the final local configuration. Production preparation remains an Orchard prerequisite; this workspace contains no production preparation proof or submission approval.

The selection is the unchanged byte copy of `BUN/q_6c18a2bf/o/r.json` from the reported 03:50Z Orchard run. Its paired report is `o/q.json`; local copies are under `evidence/fix7_selection/orchard_equal_6c18a2bf/o/`. The guard verifies the SHA-pinned report, content, implementation, source tree, executed tool, input inventory and all index checks before deriving. The H1 implementation pin is scoped to H1. No selection field was relabeled or reserialized.

`tests/test_fix8_pin.py` independently rehashes all 12 native index files, compares every raw content field, applies the D0 direct-to-VQA projection and reproduces the new selection. The raw count is 92,607; the projected count is 83,184. Both difference lists are empty. The report records the exact imported dependency versions; the single Devin review of the tool and pin must inspect that report and its native outputs. The user launches that review.

| Binding or artifact | SHA256 / value |
|---|---|
| Selection r.json / payload/d_eac5f9f01587803b.json | `eac5f9f01587803b2402f80cc310b75ec1f960270a6bc059416b1e1407b1e7c9` |
| EQUAL q.json / payload/d_e48ab85bb9364aab.json | `e48ab85bb9364aab228da7b23033605935e384761f76b0e6527c5e221b1c14b4` |
| Native implementation digest | `2a4ef06888c59743516f5f7edad4ac3d45c6868cc5d3034ddae13654c8a6cc9c` |
| Config identity | `eb45ebfd7664a57226a6a9202c365ffba268d0bd0f295d879ad6adedde07a0c8` |
| Pending-review config key | `d12ae795` |
| Admission contract | `9a5270923627a9fae982acf90ac20ee4b695ac1932b98ae13038b63710a03ff9` |
| Regeneration tool | `2d5397aaf186a6be1637f2c68b53d5b45dae620a4a85dfd99d8468c2ad2d3b38` |
| Executed regeneration script build/q.sh | `af10e6d5a3546851b2d14f4baa8827b37e102432d30bd5dc8f50b6383c810fdd` |
| Deriver payload/d.py | `4f83f57f87fcec81a67d0ea1f63919e260ee6fc2f5db817f126b258b839c849a` |
| Proof build/a_8c74b291.sh | `22ddf08a37c911682043c0149f4ae5923e98c11afb0235245b23a875227e86b3` |
| Guarded patch build/c_patch.sh | `c642f2343237413bba08aa2ac62212d4373d97d19f3185e27e069f3c7f481975` |
| payload/sums.txt | `25a9554487488c2d303e766c67f6bc3ce34f6519954ffa682cb9830ca02c9f28` |
| Upload archive p_6c368db0485677ea.tar | `6c368db0485677eaa7096c326b04fd98e0f22fd96bdb7e73a09c3d372d51f574` |
| UPLOAD.json | `330dbef08fb9bf50b3902a365001026632424a66e90b2e7b15ddc61f10416f06` |
| orch_h1.sh | `d97b163518925f8bb5a66b0a65d97ff4b6aac5f9e20644d5d953f3799b1660a5` |
| Unchanged jb.sh | `3f4b074e93eb76dcfacb4504f85bd07a1f46dce51156df5efa99daae733f57db` |
| Unchanged EXPORT_OBJECTS.txt | `1be454c3c2ab6457e3e41c902100207880253c3218d0701c584128d7d5ad7bc2` |

The run key remains `17c4ffa4`; all 44 export object names remain byte-identical. KH remains `/project/community/jjyeung/okh7/x_3fdda0fb`, and the real persistent root remains `/project/community/jjyeung/okh7/r/39504485`. The trainer archive, code tree, production jb.sh and every derived training-wrapper byte remain unchanged. The selected input and its catalog mapping change the config identity; the admission contract remains unchanged. The local config key `d12ae795` includes the PENDING review pin. The supplied independent review changes that pin and therefore the final filename; read the definitive key from `compare.json`. Its identity must remain `eb45ebfd7664a57226a6a9202c365ffba268d0bd0f295d879ad6adedde07a0c8`.

The local source kit is incomplete. The local derivation uses an explicitly recorded fixture-manifest authority and stays FIXTURE; the shipped deriver retains the production source-manifest authority `de6e7e0fac4036889fb4112792fbaa2d6f362a0cde09722ba6e93a6a39e7f32b`. Config, selection and training source bytes are real. Full sealed-source reproduction, READY derivation and certification occur on Orchard. Repeated local derivations produce identical manifests; all packet generators reproduce identical output hashes.

| CPU audit on the final config | Result and scope |
|---|---|
| `carrier_c1_run.validate`, H1 policy, route-policy authentication, native source/archive authentication | PASS |
| `s1_routing.build` implementation conditional | PASS with exact `eac5f9f0…` bytes; zero changed closure members |
| Native `s1_routing.build` through line 219 | Reached the missing r16 receipt with real selection bytes; relocation and model descriptor are isolated fixtures |
| Native synthetic routing through line 456 | PASS; 2 rows; negative blocker, division, count and suffix-budget cases pass |
| Full native `s1_admission.admit` locally | PARTIAL: missing `/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/f02f16ad/s/a2v3/receipt.json sha256=30612832cc84ad83f9500ecbeac57704767568ff24482475feb42a92c7f166b8`; no fabricated parent/model/row receipt |
| Remaining preparation | Production streams, legacy DB, models, frame reads, faithful >=95% camera gate, complete seals and first-batch boundary require Orchard |
| Regression suite | test_admission_config and all five fix7 tests PASS; deriver 19 checks; patch 7 cases; gate binding PASS |
| Proof and submission tests | Local proof logic/mount isolation PASS; 13 submission receipt cases PASS; native indices and deterministic rebuild PASS |

The regeneration runtime test deliberately retains the D0 reference configuration because the equality tool compares against that baseline. The admission and routing tests use the final H1 configuration. Exact results and logs are in `evidence/fix8_admission/`; `config_tests.json`, `pin_tests.json`, `proof_tests.json` and `submit_tests.json` identify their retained test directories. The routing limits are recorded in `evidence/fix7_admission/latest.json`.

The production CPU proof is `build/a_8c74b291.sh`, also shipped as `BUN/a_8c74b291.sh`. Its embedded driver checks the certified FINAL KH, manifest, exact config pin, identity, contract, selected bytes, equality report, jb.sh and runtime hashes. It executes jb.sh's exact cold-start prefix through export-session and staging-entry validation, followed by job.sh's certificate check, production import preflight and `g.py p`, then the unchanged `b/r.sh p 0 -> b/i.py -> b/w.py -> s1_admission.admit(prepare_only=True)` path. It never executes the training-mode selector or mode t. The import preflight checks p/t/u dependencies without executing training. The production 3.8 TB node-local free-space guard and actual session-name validation remain in force.

An outer bubblewrap namespace maps a fresh physical `/tmp/jjyeung/p_8c74b291_<job>/tmp/` onto `/tmp`, isolates the persistent root, and isolates KH's arm/run mirrors. The production configuration, logical paths, source bytes and staging functions remain unchanged. The rest of the filesystem is read-only; only proof-local storage and KH/o receive writes. Network access and GPU device nodes are absent in the outer namespace; `CUDA_VISIBLE_DEVICES=''` is forced throughout. No existing jb.sh, job.sh, go.json, production run or persistent slot is edited. The real job automatically reuses **nothing** from this proof: staging, preparation and cold-start claims are isolated, and the real wrapper performs its normal staging and admission again.

After mode p returns, the driver calls native `b/d.effective` against the isolated physical run and validates the prepared source/config/frame seals. It writes `KH/o/<job>.proof.json` with PASS/FAIL, rc, start/end/elapsed timing, full admission result, prepared pins/seals, exact manifest/config/runtime bindings and physical locations. `KH/o/<job>.proof.log`, `.proof.out`, `.proof.err`, `.w.steps`, `.steps` and `.preflight.*.json` retain diagnostics. The native receipt remains at `/tmp/jjyeung/p_8c74b291_<job>/tmp/jjyeung/a_17c4ffa4/runs/17c4ffa4/inputs/data_receipt.json`. PASS means full production preparation and RGB audit reached the first-batch boundary. It does not mean a CPU forward batch or GPU first step ran: native prepare_only returns immediately before `first_batch_check` (`s1_admission.py:277–281`). Catchable failures produce FAIL with rc; a forced kill may leave RUNNING, which never qualifies for submission.

Mode p's native resource contract requests zero GPUs (`b/i.py:26–28`, `b/w.py:32–43`). The exact submission below omits GPU GRES. Four hours allow 1 h 39 min beyond D0's 1 h 51 min preparation plus approximately 30 min staging. Orchard partition policy and production imports were not queried under the local-only scope; no code requirement for a GPU allocation was found. If the scheduler rejects a zero-GPU job, preserve that refusal for the operator; this packet does not silently request a GPU or retry. The local mount test omits only the network namespace because this sandbox denies NETLINK_ROUTE; the shipped script retains it.

The operator sequence is **patch -> o.sh -> g.sh -> review.json -> z.sh derive -> anon/certify -> proof job -> go.json -> s.sh**. These commands are provided for the operator; none ran on Orchard in this task.

1. Deliver `build/c_patch.sh` as `/project/community/jjyeung/okh7/t_c8b460a1.sh` through the authorized opaque transport. Verify SHA256 `c642f2343237413bba08aa2ac62212d4373d97d19f3185e27e069f3c7f481975`. The patch targets bundle `i_1be16f28` and authenticates the exact retained live starting state in `evidence/fix6_before/payload/`; it refuses another state, occupied target KH/root, linked targets, bad sums and foreign review/staging evidence before mutation. It retains replaced files and obsolete identity-bound evidence in `BUN/v_8`, adds the new selection/report/proof files, and rechecks sums. It preserves the trainer and old KH. A refusal is a stop for operator inspection, never a reason to bypass its guards. `orch_h1.sh` is the reproducible fresh-bundle transport and is not the command for an existing live bundle.

```bash
O=/project/community/jjyeung/okh7
BUN=$O/i_1be16f28
KH=$O/x_3fdda0fb
printf '%s  %s\n' c642f2343237413bba08aa2ac62212d4373d97d19f3185e27e069f3c7f481975 "$O/t_c8b460a1.sh" | sha256sum -c -
bash "$O/t_c8b460a1.sh"
cd "$BUN"
bash o.sh
PY_GATE=/project/community/jjyeung/latency/envs/fit/bin/python3 BW_GATE=/usr/bin/bwrap bash g.sh
```

2. The user launches one Devin review of the tool and exact selection/report pair plus packet bindings. The operator supplies the resulting PASS `review.json` with this identity, source revision, contract, reviewer and `admission_scope=pinned-template-and-native-data-derivation`. Do not convert the bundled PENDING record into a claimed review. Then derive, inspect `compare.json`, perform the actual content scan, supply CLEAN `anon.json` and certify:

```bash
bash z.sh derive
python3 -m json.tool compare.json
# Supply the actual independently checked CLEAN anon.json for this manifest and its external records.
bash z.sh certify
# Ensure the existing real sess.json contains the 44 unchanged, unused, unexpired export sessions, mode 0600.
PROOF_JOB=$(TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch --parsable -J a15_cot_ap8c74b291 -o "$KH/o/%j.proof.out" -e "$KH/o/%j.proof.err" -A mt01 -p general -N1 --ntasks=1 -c 48 --mem=800G -t 04:00:00 --no-requeue "$BUN/a_8c74b291.sh")
PROOF_JOB=${PROOF_JOB%%;*}
export PROOF_JOB
printf '%s\n' "$PROOF_JOB"
```

3. After the proof job finishes, inspect `KH/o/$PROOF_JOB.proof.json`. Require PASS, rc 0, PREPARED, effective-config verification and matching final config/manifest/identity/contract/wrapper bindings. A failure stops the sequence. No automatic retry or resubmission is provided.

```bash
python3 -m json.tool "$KH/o/$PROOF_JOB.proof.json"
# Supply separately authorized go.json bound to this final identity, contract, jb.sh SHA and final KH manifest.
bash "$BUN/s.sh"
```

`s.sh` checks the separate GO and `PROOF_JOB` receipt before sbatch. It rejects missing/failed/stale proofs and wrong configuration, manifest, contract, wrapper, CPU visibility or preparation status. The proof itself grants no production GO. No production review, anon certificate or go.json was manufactured locally. All work here used local CPU and workspace files; no SSH, network, Orchard, GPU, Git or deletion command ran.
