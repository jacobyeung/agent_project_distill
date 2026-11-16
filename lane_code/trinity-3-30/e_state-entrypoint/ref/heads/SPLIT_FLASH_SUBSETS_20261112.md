# SPLIT with the Gemini 3.8 Flash planner on the static subsets

Question: How does the planner affect SPLIT's accuracy on the 500-question VSIBench subset, VSTIBench-450 and official ReVSI-999?

Answer: Compare the Flash planner with the Pro planner on exactly the same questions. The Flash cells inherit their Pro parents' prompts, tools, native parsers, input stores, SAM3 settings and official scoring. They use the Flash thinking policy from r3025, including the inherited HIGH/LOW routing and 32,768-token cap. The accuracy answer remains pending production completion and registration.

| Benchmark | Pro parent | Flash cell | Held-only continuation |
|---|---:|---:|---:|
| VSIBench, 500 questions | r3014 | r3063 | r3067 |
| VSTIBench, 450 questions | r3015 | r3064 | r3066 |
| ReVSI, 999 questions | r3016 | r3065 | r3068 |

The final continuation delivery is `/scratch/jjyeung/split_flash_subsets_1112/bundle_v11`, with delivery-seal SHA-256 `ab3022d304434a6b0c406faa23d5e865396afbab0a18e1fe59bf08064466a1f7`. Each package and the complete delivery pin their files by SHA-256. The original production packages and committed answers remain immutable.

The VSIBench membership is bound to SHA-256 `2de71c248b9b9817d515510b48dd4d9a5a3800583f5ea64ea2be855b16220fbf`. The VSTIBench membership is bound to SHA-256 `d7c16986eb7e70fd1d4a8559f32794cc00bc6fbc56e8f9deaa7c8a7ce7f5fca9` and its provenance. ReVSI uses the official 999-question membership. Comparison code requires exact question identity and uses the official eight-task, five-task and seven-task means, respectively.

Evidence: All three continuation packages pass full-cohort admission and the constant-origin gate. The VSTIBench repair passes nine native dispatch-to-official-score cases, including question 3192. A ToolNode replay uses a SHA-pinned recorded SAM3 mask, exercises a real cache hit, preserves the returned mask, and records zero fatal asset events. All 19 tools pass their native dispatch probes; identical tool and service bodies retain the parents' evidence.

The VSTIBench repair restores the registered-access hook and the admitted video digest. The defect audit identifies the incorrect digest pin for question 3192; the admitted video content matches the parent. The Pro-parent audit covers 477 attempts and finds no recorded missing-hook failure, cache-hit event, precall failure or affected scored-wrong/held case. The available evidence does not attribute any Pro-parent accuracy loss to this defect.

Continuations preserve every committed answer. Eligibility depends on authenticated infrastructure outcomes: provider timeouts, empty replies, the exact missing-hook failure, and the identified VSTIBench input-pin failure. Whitespace-only selected text is empty when `text.strip() == ""` and no function call or other response payload exists. The recorded reply for question 1753 passes that rule despite its original `valid_reply` flag.

The native continuation test retains nine answers, dispatches only the held question, retries its whitespace-only attempt and keeps its first committed answer on resume. The combined ten-category fixture passes the pinned official scorer twice. The diagnostic bank archive builds locally and cannot be published. These tests use no paid calls or GPU runs; mocked scores are never accuracy evidence.

Execution: The launcher owns services, paid calls and ongoing experiment health. The cells use GPUs 5, 3 and 7 on trinity-3-3, with independent pinned SAM3 services and up to 16 initial workers per cell. Input stages are reused read-only. Evidence caps are 16, 8 and 26 GiB on the RAM disk. Optional model-specific caches are unnecessary: direct inputs preserve the answers without cache preparation or expiry dependencies.

The supplied estimate is about $0.54 per question: $270, $243 and $539 for the three original cells. Expected durations at 16 workers are about 1–2 hours for VSIBench and VSTIBench, and 5–7 hours for ReVSI. Continuation cost scales with the eligible question count and can increase with repeated provider failures. These are planning estimates, not timing results.

Options rejected: The 150 timing questions cannot answer the full-subset question. Correctness cannot select which SPLIT answers to regenerate. Empty provider text cannot become a scored answer. A change to the duplicate-request policy would add another experimental variable; the traces do not establish that duplicate requests cause empty replies. Prepared caches add expiry and model-binding dependencies without changing the intended answers.

