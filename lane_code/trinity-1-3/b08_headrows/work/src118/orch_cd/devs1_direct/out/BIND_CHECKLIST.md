The operator runs these checks on the host that holds `/scratch/jjyeung/devs1_frames`. The builder has not opened that directory.

- Resolve the 161 label gaps listed in `MISSING_LABELS.jsonl`, or obtain a ruling that changes their treatment. No value may be copied from `answer` into `released_answer` merely to make the bind pass.
- Check `PINS.json` and `STRATA.jsonl.sha256` before any inference. The binder recomputes every pin and every stratum. Keep both checkpoints on the same frozen payload.
- Use the reviewed successor of each named kit. Run both dry binds after adopting it; review `CODE_PINS.json`, `PROMPT_PINS.json`, and the two `DRY_BIND` records. The baseline thinking kit's AWS binder rejects every non-ReVSI cell; this adapter supplies a native `devrows` request directly to the evaluator.
- Stage authenticated base, CP1 m200, and f17 model specifications in `MODELS.runhost.json`. `MODELS.reference.json` records their existing pins and AWS paths. Those paths are references, not claims that weights exist on this host.
- Confirm all 4,864 planned anchor PNGs exist under the frame root. The binder checks all 152 captures, including captures without selected items.
- Verify the fixed 64-file sample in `FRAME_SAMPLE.json` against PLAN SHA256 values. Its order is ascending sha256(`devS1-byte-sample-v1|` + relative path). No model output chooses the sample.
- For the 142 selected captures, verify every used PNG hash, RGB mode, dimensions, and exact anchor order. The binder decodes one capture at a time, computes the kit's NumPy pixel hash, and hard-links the PNGs into its local cache. The cache and frame root must share a filesystem. A cross-device link fails; there is no hidden bulk-copy fallback.
- CP1 receipts expand `[a,b,...]` to `[a,a,b,b,...]`. f17 receipts retain the original 32 indices. Both carry PLAN fps=1 as an identity placeholder, not a measurement of physical frame rate.
- Check `BIND_STATUS.json` says `ready: true`. `frames/0.json` binds receipt paths and hashes to the request and source hash. `frames/BYTE_CHECK.json` records byte checks. Template receipts in this delivery deliberately have `pixel_sha256: null` and cannot be used for inference.
- Let the kit authenticate model weights and run its 16 prompt-ID and two pixel parity probes at launch. A failed parity gate prevents a report.
- Run one cell on one assigned card. Keep journal attempts on their bound kit. Never resume a pre-patch journal under a changed kit. The cluster's no-retry-after-kill rule still applies.
