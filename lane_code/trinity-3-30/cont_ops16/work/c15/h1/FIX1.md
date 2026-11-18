F1 and R1–R4 are fixed and pass local CPU tests. F2 needs the orchestrator’s ledger update. The fixed four-rank stop chain awaits the operator run outside this sandbox. No requested optional fix was skipped.

| Finding | Change location | Change | Test/evidence |
|---|---|---|---|
| F1: login-node source argv | `payload/g.sh:21`, `payload/r.py:16` | Copy the sealed routing archive through Python to BUN/a_b8b60bce.tar; compare its streamed/readback SHA256 and sealed member hashes before extraction. | `tests/test_fix1.py` executes the real copy function and rejects a corrupt member; `tests/test_visible_names.py` checks the extraction argv and all new naming surfaces. |
| F1: names and private directories | `payload/o.sh:4`, `tools/derive_kit_h1.py:533`, `payload/r.py:73`, `payload/s.sh:28` | Every entry refuses an unsafe okh7 mode before writing and prints chmod 700. BUN/KH/slot roots are created and verified as 0700; the job name is a15_cot_ap5ee9da63. REPORT.md lists inherited exposures. | `tests/test_fix1.py` runs all seven entrypoint refusals and verifies no filesystem/mode change; it tests private root creation. `tests/test_visible_names.py` checks new shell literals, Python strings and fixed runtime additions. |
| R3: shared node-local tree | `build/fx/b/c.sh:18`, `build/fx/b/p0.sh:9`, `build/fx/b/r.sh:42`, `runtime/jb.sh:24` | Staging, namespace, preflight/training jobs, runs and uploads use a_17c4ffa4. Foreign normal or hidden run entries are refused before creating output directories. K and all GCS keys remain unchanged. | `tests/test_fix1.py` checks every active root and runs the exact preflight for clean, foreign and hidden-foreign roots. `tests/test_derivation.py` reproduces D0 identity/contract. |
| R1: absent source authorization | `tools/derive_kit_h1.py:379` | A code_tree override must supply add_k 4.json before any output directory is created; source/config bindings remain enforced. | `tests/test_fix1.py`, `tests/review/rv_mut.py`, and `tests/review/rv_g_a2.py` pass. The last also confirms the unchanged native gate refuses the reviewer’s stale-authorization fixture. |
| R2: final identity and checksums | `payload/r.py:74`, `payload/z.sh:17`, `payload/s.sh:18` | Final derive asserts the registered identity before publishing result.json or comparing manifests. Both final entrypoints recheck immutable sums. Mutable review/staging attestations are semantically validated and re-pinned; executable files and 4.json stay checksum-pinned. | `tests/test_fix1.py` injects a wrong derive identity, verifies ordering, and rejects a corrupt checksum fixture; native binding tests and copied reviewer checks pass. |
| R4: unused resume condition | `tools/build_packet.py:69` | The conditional authorization drops “and canary-2 resume”; it still grants no production GO. | `tests/test_fix1.py` verifies the condition is absent; the rebuilt authorization and manifest are sealed. |
| F2: central token ledger | `ORCHARD_LEDGER_PENDING.jsonl:1` | The five token/role rows are prepared locally. The central work/ORCHARD_LEDGER.jsonl is outside the authorized write scope, so registration remains an operator action before any Orchard call. | The pending file contains exactly the five ids.json tokens. No Orchard call was made. |
| Fixed four-rank CPU stop chain | `tests/RERUN_CHAIN.sh:1`, `tests/review/prepare_chain.py:1` | A fresh chain_r1 copy runs signal, fileonly, hfail and full200. Each case gets result.json and a PASS/FAIL summary line. Input hashes bind the copy to this packet; no case is retried. | Only bash -n and Python AST syntax checks ran. The four-rank runner/harnesses were not executed here. The local CPU fallback and real bwrap stop-bridge test pass. |

The original derivation, gate-binding, staging and 200-step CPU fallback checks pass, along with `test_stop_bridge.py`, both new fix tests, and all four copied reviewer checks. The fallback reports `H1_STOP`, step 200, `stopped_for_resume=false`, m100/m200 and a verified slot. Its local collective stand-ins do not prove four-rank behavior.

The trainer tar and derived kit reproduce deterministically. The upload archive also reproduces exactly. `REPORT.md` gives the identity/contract/hash table and inherited visible names; `evidence/hash_changes_fix1.json` records the changed hashes. `DIFF.md` gives exact source/runtime patches. Old outputs are retained and listed in `REMOVAL_CANDIDATES.md`.

Run the pending four-case test once:

```sh
bash /scratch/jjyeung/orch_n30/cont_ops/work/h1/tests/RERUN_CHAIN.sh
```

Read `chain_r1/summary.txt` and `chain_r1/evidence/cpu/<case>/result.json`. The runner refuses an existing chain_r1 directory and stops execution after a harness failure; it does not erase evidence or retry a killed job.
