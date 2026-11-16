The thought-capture implementation is staged and passes 81 offline tests in each planner interpreter on trinity-3-30. It is not installed, and no shared harness, environment, existing round, or sealed package was edited. The user must confirm installation at a quiet point.

**Question.** How can new SPLIT and baseline runs request and save provider thought text by default, reject accidental capture suppression, and stop after the first completed episode if thinking tokens were generated but no thought text was saved?

**Answer.** Use a lazy interpreter startup hook, explicit carrier serialization, and a durable completion gate. The hook requests capture without enabling thinking or changing a budget. The carrier records the returned text and hook provenance. The runner publishes its first completion only after telemetry and a clean trace are saved; the supervised launcher stops its owned evaluation if that completion fails the gate.

**Artifacts.** All paths below are relative to `/home/jjyeung/agent_project/agent/scratch/devin_lanes/thought_capture_build_1112/out/`.

| Artifact | Purpose |
|---|---|
| `staging/sitecustomize.py` | Lazy Google SDK, LangChain Google, and OpenAI/vLLM request wrappers; explicit dual-variable opt-out; runtime hook hash and patch status. |
| `staging/stall_watch.patch` | Unapplied unified diff for the shared watcher, launcher, and shell wrapper; patched copies sit alongside it. |
| `staging/carrier_templates.patch` | Unapplied diffs for future full copies of the r2900 Gemini, r2723/r740 Gemini, and r3027 open-model parents, including completion adapters and vendored gate modules. |
| `staging/SOURCE_MANIFEST.json` | Exact source preimages, staged outputs, and patch labels. |
| `staging/DELIVERY_MANIFEST.json`, `RELEASE_RECEIPT.json` | File pins, SDK source pins, test receipts, and verification that the patches reconstruct the proposed files without changing a parent. |
| `TESTS.md`, `TEST_RESULTS_local.json`, `TEST_RESULTS_nfs.json` | Every offline test and its result; retained attempt logs and fixtures explain the test scope. |
| `EXPLICIT_FALSE_AUDIT.json` | Bounded audit of the 75 exact source files provided by the orchestrator. |
| `RISK_AND_IMPACT.md`, `INSTALL_PLAN.md` | Evidence, current consumer reports, timing/billing limits, and exact commands that remain unexecuted. |

The patch kit contains selected source files for review, not a complete launchable package. A future builder must copy the entire parent to a new directory, apply the matching changes, assign the new identity, and regenerate the full contract/manifest.

**Reasons and evidence.**

- `/data3/jjyeung/orch_n13_20261026/rebuttal_iclr/REASONING_TRACE_AUDIT.md` identifies missing Gemini summary requests and discarded thought parts. The r2723/r740 carrier still discards those parts. The newer r2900 carrier requests summaries in several paths but omits nonstreaming point-tool thought text and serialized planner reasoning counts.
- `agent/docs/NEW_ROUND_PROCEDURE.md:59-60` identifies r310 as the reference shape. The orchestrator confirms there is no central live template: new rounds copy their parent packages. The Gemini patch uses the supplied r2900 parent and the available local r2723/r740 parent; the open-model patch uses r3027_dsi_v8.
- Both tested environments expose Python 3.12.13, google-genai 1.75.0, openai 2.44.0, and the required LangChain fields. The hook preserves the original classes and wraps request boundaries, so nested configuration dictionaries cannot bypass the policy. Library absence or interface differences log once when encountered; no third-party SDK is imported merely to start Python.
- `include_thoughts=False` on an enabled-thinking request raises `RuntimeError` unless `SPLIT_DISABLE_THOUGHT_CAPTURE=EXPLICIT_OPT_OUT` and a nonempty `SPLIT_DISABLE_THOUGHT_REASON` are both set. Budget zero and explicit disabled-thinking requests retain their settings. The gate's `--allow-no-thought-text` is a separate deliberate exception.
- vLLM 0.23.0 declares `ChatCompletionRequest.include_reasoning: bool = True` in its public source. The supplied Qwen launcher uses `--reasoning-parser qwen3`; the request enables thinking through the chat template. The hook uses `extra_body.include_reasoning=True`, preserving sampling fields. The current installed server source and tokenizer template remain unverified on this node.
- r3027's raw HTTP receipts already preserve replies, but its LangChain subclass retains reasoning only on empty STOPs. The new transport saves ordinary planner reasoning in response metadata, reads both supported reasoning field names, and preserves the existing rescue input without feeding the new metadata into model messages.
- `stall_watch.py` receives only active episodes, and `stall_watch_launch.py` deliberately preserves an evaluation when its watcher exits. A watcher-only exception cannot halt the evaluation. The patch adds a durable first-completion marker, synchronous completion calls, admission checks, and an owned-process-group halt with exit code 86.
