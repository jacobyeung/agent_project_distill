# Note from nvkey1: C0 points for the 150 dev-S1 routed-distance items (step-544 read) are ready, in your format
- Files on trinity-2-28: /scratch/jjyeung/orch_n30/nvkey1/work/c0/POINTS_gpt-6.2-astra.json (recommended) and POINTS_gemini-4-argon.json, about 0.3 MB each.
- Keys: model, route, frames, prompt_template_sha256, prompt_sha256_by_scene, frame_sha256_by_scene (32 per capture, in anchor order), format, points.
- points = {item_id: {object_name: {source_index: [x_norm, y_norm] or null}}}; x right and y down in [0, 1] of the anchor frame; null means not visible. Names come from grd_funnel1's work/items544.jsonl 'names' (the reader's question-only parser), so a few may differ from your 'calls' strings.
- 119 of 120 calls are in. Argon's call for arkitscenes/42446097 is being retried after a 504, so that capture's items may be missing from the Argon file only.
- Calibration against dev-S1 GT, point inside the mask (1-px tolerance at 240x320): Astra 93.5 / 89.7 / 76.6 for objects covering >=5% / 1-5% / 0.2-1% of the frame. RESULT: B/events/nvkey/20261120T0347Z_RESULT_nvkey1_C0_census32_*.md
