# Gemini frame-cache efficiency round

The sealed r2947 Pro and r2948 Flash packages are ready for launcher validation. The Orchard handover measures all 150 timing questions per SPLIT planner and reports VSIB50 first. A separate Trinity route runs Flash50 then Pro50 for answer and step inspection; its timing is explicitly not reportable. The build made no model call, created no API cache, ran no GPU workload and submitted no job.

## Question and design

Can API-side frame preparation reduce SPLIT and no-tool latency while preserving their ordered model inputs? K1 caches each exact leading image prefix before question dispatch. It uses Gemini 3.6 Flash for frame tools, Pro 3.1 for r2947 planning, and Flash 3.8 for r2948 planning. Each no-tool arm receives its own model's cache when the orchestrator releases it.

r2947 preserves the r2932 prompts, frames, R1 routing and V1 VSTIBench pre-calls. It uses the S1 twelve-second delayed hedge, L1 critical-first lookup scheduling, C1's 30,000-character ReVSI bound and the summary-only closest-point helper. VSIB P1 is absent. Retained helper values, including `min_raw` and `median_raw`, match the source. r2948 changes only the planner model and required identities; the telemetry implementation is shared.

Flash frame searches cache their leading labels and images. No-tool caches include all text before the final image, preserving its place. Runtime expansion must reproduce every original part in order. Single-frame requests use byte-identical Files references because padding them or adding 32 images would change the input. Newly rendered planner images retain their original inline representation.

Each cache manifest pins the model, ordered prefix, image bytes, API resource and expiry. TTL is twelve hours. Preparation merge requires ten hours remaining; launch admission normally requires four. Missing, reordered, mismatched or expired resources refuse before generation. The planners retain implicit text-prefix caching.

r2819's Pro no-tool worker already uses HIGH, temperature zero and a 32,768-token cap. HIGH is the highest documented level, so the fresh r2947 no-tool arm also supplies the highest-thinking baseline.

## Evidence and interpretation

The official pages below were read on **2026-11-10**. Their snapshots and hashes are in the Orchard archive's `docs/` directory.

- [Context caching](https://ai.google.dev/gemini-api/docs/caching?generate-content=true): explicit caching supports Gemini 3/2.5 through `v1beta`; the minimum-token table lists 4,096 for the selected models. A cache is a model-specific prompt prefix. TTL defaults to one hour with no stated minimum or maximum. Explicit-cache suffixes do not also receive implicit caching; cached tokens still count toward rate limits.
- [CachedContent API](https://ai.google.dev/api/caching): a resource can hold contents, a text system instruction, tool declarations and tool configuration. Contents are immutable; expiry is updateable. Generation references `cachedContent`.
- [Optimization](https://ai.google.dev/gemini-api/docs/optimization): caching can improve first-token latency, but the page gives no numerical guarantee and no evidence that an explicit planner text cache beats an existing implicit hit.
- [Files](https://ai.google.dev/gemini-api/docs/files): references avoid repeated upload; retention is 48 hours, with a 2 GB file limit and 20 GB project limit. File references do not establish a token-cache hit.
- [Thinking](https://ai.google.dev/gemini-api/docs/thinking): Pro 3.1 supports HIGH as its highest level.
- [Pricing](https://ai.google.dev/gemini-api/docs/pricing): the priority columns list Pro input/cached/output rates of $3.60/$0.36/$21.60 per million tokens up to 200k input, and $8.10 per million token-hours. Flash 3.6/3.8 list $1.35/$0.135/$6.75 and $0.50 storage through the stated promotional period. Cache creation exposes no service-tier selector, so storage billing must be reconciled with the provider.

At an illustrative 34,000 cached tokens per video, twelve-hour storage for 46 videos costs $9.38 for shared Flash-tool caches and $152.02 for deferred Pro no-tool caches at those priority-column rates. Storage alone breaks even after about five Flash or thirty Pro reuses. Existing implicit hits reduce incremental savings. Long-lived explicit caching can therefore increase the one-question-per-video baseline's cost.

`EFF_STALL_RULE_v1.md` reports Flash32 request medians of 10.2 seconds for r2932 and 5.3 seconds for r2933. Flash critical-path work averages 7.9 and 5.2 seconds per question. The no-tool answer request has a 23.5-second median and 48.1-second mean. SPLIT's question median/mean is 43.4/56.2 seconds for r2932 and 34.5/48.6 for r2933. These are mixed-set observations, not K1 forecasts.
