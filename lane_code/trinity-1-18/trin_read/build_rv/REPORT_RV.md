# build_rv result

The four ReVSI commands are implemented and CPU-tested. **294 tests pass**, including the 260 inherited build_t6 tests and 34 new ReVSI cases. The supported execution path is the reviewed step-544, tier-32 read. D0 and 64-anchor reads refuse explicitly because they conflict with the unchanged kit's hard pins.

`TESTS_RV_FULL_01.log` records the complete suite with fresh basetemp `tests/rv_full_01`: 294 passed in 82.37 seconds. `TESTS_RV_01.log` records the 34 new cases with fresh basetemp `tests/rv_fixture_01`. System Python 3.6 accepts the CLI and parses all new boundary code. No test required media arrival, a real model, or a GPU.

## Delivered behavior

- `rv-stage` admits exactly the 261 manifest-pinned regular videos, writes a receipt only after all hashes pass, and refuses existing or partial destinations. Fixtures reject traversal, absolute paths, links, FIFOs, duplicates, wrong sizes, missing/foreign files, and wrong content. The media source fields under `/data2` are never opened.
- `rv-proof` runs the kit's phase A, including its accepted 20-item prompt-byte/processor comparison and 10-item synthetic generation exercise. `rv-read` runs its full 679-item production chain, after requiring a successful authenticated proof for the same payload and artifact. Both retain the kit's batching and scoring semantics.
- Each run uses the build_t6 sandbox, host bwrap, private caches/shm, vnice, two empty card readings separated by 60 seconds, import probe, generation-time stub audit, and memory sampler. The stub must record imports and zero calls. Failure receipts cannot pass on the strength of the kit's COMPLETE marker alone.
- The packet retains `a0/results/0/` journals and the kit's three `report/*.json` files. EXIT authenticates the principal reports, journals, configuration, and audit evidence. Fixtures exercise successful proof/production and failed process, stub, sampler, and processor-parity outcomes.
- `rv-compare` checks all 679 IDs, compares exact token-ID lists and first divergences in every arm, checks native scorer rows against journal scores, and reports category equality and subtype-weighted means. Comparison tests invoke the actual unchanged scorer on fixture answers and reject corrupt membership, tokens, scores, means, and terminal markers.

`REFERENCE_SELF_COMPARE_FINAL.json` compares Orchard return 170037 with itself. All 679 items have identical tokens in all three arms; all category scores and means agree. Its B2048 five-category mean is 0.6494461380258723. This validates return-layout parsing and comparison, not Trinity parity or new accuracy.

## Source and runtime evidence

The copied `rv_payload/` matches all 84 production payload pins in job 170037's CONFIG. The reviewed package archive hashes to `ea1a1b2d5b965017f7cacce9c02c13cbbe5522d87be8cc55ab755176ecd55d3b`; overlapping archive members match the active payload. The three additional active support files are unchanged and pinned. `RV_SOURCE_EVIDENCE.json`, `PACKAGE_MEMBER_CHECK.json`, and `RV_PAYLOAD_PINS.json` record these checks.

Every `ORCHARD_ASSETS.json` field matches the staged build_t6 configuration, including the complete runtime archive groups. The kit and staged environment both specify vLLM 0.32.0 at the same logical interpreter path. No different runtime pin was found. The live import probe remains an operator-run check; the build uses existing staging receipts and static descriptors.

The engine settings remain BF16; max_model_len 49,152; memory utilization 0.90; max_seqs 32; inflight 16; max_num_batched_tokens 8,192; tensor parallelism 1; seed 17; one video and zero images; disabled prefix caching; source max_tokens 16,384; temperature zero. Step-544's weight manifest records 9,409,813,744 parameters and 17.527 GiB of BF16 weight files. Weights fit a 48 GiB card, but **full engine fit has not been established**. KV cache, activations, graphs, and multimodal profiling require an actual run. No setting was reduced to claim a fit.

## Unsupported paths and measurements

D0 is not implemented through the unchanged reader. `official_adapter.model_specs`, `bind`, and `launch` pin the step-544 artifact hash and step, so replacing only CONFIG cannot select a staged D0 export. The wrapper admits the inherited lineage first and then refuses unsupported identities. A narrow adapter-contract change requires a user ruling on the unchanged-reader requirement; no such override is applied here.

`--frames 64` is exposed but refuses before GPU admission. The supplied media is tier 32. A real tier-64 read needs new videos, tier-64 rows/video pins, 64-anchor decoded/source-index plans, 128 expanded input frames, and fresh prompt/processor pins. The adapter and frame checker also require review. Repeating the supplied frames again is not equivalent.

`RUNTIME_FIT.json` and the README quantify the available cost evidence. At fixed spatial resolution, 64 anchors would add approximately 2,853,312 visual tokens across 679 items, from 3,111,992 observed prompt tokens to roughly 5,965,304 before additional text effects. The Orchard generation stage took 7.99 minutes and its chain stages totaled 8.91 minutes. Trinity time and tier-64 time remain null because neither was measured; processor resizing also prevents an exact tier-64 token count without a valid plan.

No production archive staging, production media decoding, model execution, GPU workload, SSH, network, Git, Slurm submission, or deletion command ran during this build. All edits and generated evidence stayed under `build_rv/`. Source directories, root, dl, kit_src, and evalx27 remained read-only. The 5.1 GB build_t6 copy and local fixture work followed the requested build boundary.

The README and report apply the no-archaeology skill. The requested comparison against build_t6 and kit_revsi is confined to DIFF and source-validation evidence. No narrative of revisions is needed to operate the build.
