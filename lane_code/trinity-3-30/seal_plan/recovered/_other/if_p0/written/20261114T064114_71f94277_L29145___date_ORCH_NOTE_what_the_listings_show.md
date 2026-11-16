<!-- recovered by seal_plan: transcript=71f94277 line=29145 utc=2026-11-14T06:41:14.720Z kind=written original_path=/scratch/jjyeung/orch_cd/if_p0/inbox/$(date_ORCH_NOTE_what_the_listings_show.md heredoc_quoted -->
# ORCH note: what the listings already show (so you do not wait)

- `e00` has 58 members and none is the FLA manifest. Its members are kit and run records under `scratch/fsw/.../ap/7b30c1e4/...`, `.../ap/e84d901c/...` (including the model manifest `arm/frozen/6f27ae81/model.json`, 1,621 bytes), `.../ap/244cdf20/k/...` and a few `lustre/fsw/...` entries.
- The FLA manifest is in **d00**: its first members are `ebe69df8`, `ebe69df8/w.sha` (333 B), `ebe69df8/m.sha` (87,191 B), `ebe69df8/w/einops-0.8.2-py3-none-any.whl`, and so on (969 members). So the kit's "small" stage asked the wrong archive for the manifest, with the wrong name.
- The CP1 parts hold ten members named `ap/f2ad01ad/runs/49becb79/m200/...` (artifact.json, heads.pt, full_weights/...) plus `_evac_manifest/17eedd296fe8.tsv`; compare these with your `checkpoint_members` names.
- The operator will deliver the `m.sha` payload from d00 (I corrected my request).

Decide from the listings what the job really needs from e00 (possibly nothing) and fix the stages accordingly; the rule stands that every inventory is checked before large extraction and all mismatches are reported together.