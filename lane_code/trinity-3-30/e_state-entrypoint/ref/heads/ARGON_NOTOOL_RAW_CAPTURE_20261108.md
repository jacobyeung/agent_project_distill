The native Google SDK boundary preserves Argon response data without changing the matched no-tool grading protocol.

The recorder captures every returned SDK response before LangChain converts it into a message. It retains all parts, provider thought text, opaque signatures, finish reason, usage, served model, and latency. Binary fields use base64. Each attempt has a unique ID and a separate raw record; errors retain the available `APIError.details` body, response text, status, and exception.

The three 600-question cohorts use `gemini-4-argon`, 32 displayed frames, temperature zero, high thinking, a 32,768-token output cap, `include_thoughts=True`, and a 3,600-second request timeout. Their prompts, questions, displayed-image hashes, and scorer match the registered Gemini 3.1 Pro no-tool controls.

All 1,800 terminals passed the package and trace integrity checks. The pinned scorer gives STI-Bench 56.00, ReSTI 48.83, and OSI-Bench 49.62. The archives contain 1,800 native responses and 71 failed-attempt records. Provider thought text is present in 1,688 terminals; the recorder preserves empty fields when the provider returns no thought text.

The scorer reads non-thought answer text. Its existing final-text fallback applies to two STI traces. Every registered question stays in the denominator, including budget-limited outputs.

Capturing only LangChain message text would omit native fields. Using `str()` for signatures would lose their portable byte representation. Grading thought text or expanding the output cap would change the matched protocol. Those options are unsuitable for this baseline.

The transport uses native non-streaming generation with the registered retry policy. Streaming remains an untested alternative for a future collection blocked by provider deadlines. It would require chunk-level persistence, an explicit terminal-event check, and source-version provenance across any handoff.

The main limits are provider visibility and request completion. The recorder cannot recover content that the provider never returned. Integrity checks compare thought and answer text against native parts, authenticate every attempt record, and reject incomplete or foreign traces. Both the scheduler and executor must support the configured worker count.

Offline evidence covers native generation-argument equivalence, signature preservation, thought/answer separation, complete synthetic 504 error capture, and scorer invariance under added raw-thought fields. Real evidence consists of three first-thought gates, all 1,800 authenticated terminals, and archives verified member-by-member against their manifests.

Evidence and executable sources live in the three answer banks named in the lane's `ALL_SCORED_V3.json`. The lane artifacts are under `/home/jjyeung/agent_project/agent/scratch/devin_lanes/argon_notool/out/`; the immutable source packages are `r2880_v3`, `r2881_v3`, and `r2882_v3`.

Status: collection, scoring, bank registration, and the canonical mirror are complete. All results remain provisional and un-nominated. Registration and mirror receipts are in the lane's `registry_apply/` and `registry_mirror/` directories; `MIRROR_PATHS.txt` lists the files for the designated commit owner.
