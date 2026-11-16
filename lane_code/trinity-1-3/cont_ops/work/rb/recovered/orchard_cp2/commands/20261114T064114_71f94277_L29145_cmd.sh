<!-- recovered by seal_plan: transcript=71f94277 line=29145 utc=2026-11-14T06:41:14.720Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/orchard_cp2/inbox/${N}_ORCH_CORRECTION_m_sha_is_in_d00.md <<'EOF'
# ORCH correction to my 0641Z request: the manifest is in d00, not e00

Your listings show it: `ebe69df8/m.sha` (87,191 bytes) is a member of `/project/community/jjyeung/distill/okit/in/d00`; e00 has no such member. Read that member from **d00** (bounded member read as described: seek to its data, read exactly its bytes, refuse above 4 MB), check it against sha256 4e4a6ac51788f7dd1ca9e0fc68f95109a129a636ce5f763e5b4ef3c3109f91c8, and deliver it to `/scratch/jjyeung/orch_cd/if_p0/inbox/`. If the hash differs, deliver nothing and tell me the hash you got.
EOF
cat > $C/if_p0/inbox/${N}_ORCH_NOTE_what_the_listings_show.md <<'EOF'
# ORCH note: what the listings already show (so you do not wait)

- `e00` has 58 members and none is the FLA manifest. Its members are kit and run records under `scratch/fsw/.../ap/7b30c1e4/...`, `.../ap/e84d901c/...` (including the model manifest `arm/frozen/6f27ae81/model.json`, 1,621 bytes), `.../ap/244cdf20/k/...` and a few `lustre/fsw/...` entries.
- The FLA manifest is in **d00**: its first members are `ebe69df8`, `ebe69df8/w.sha` (333 B), `ebe69df8/m.sha` (87,191 B), `ebe69df8/w/einops-0.8.2-py3-none-any.whl`, and so on (969 members). So the kit's "small" stage asked the wrong archive for the manifest, with the wrong name.
- The CP1 parts hold ten members named `ap/f2ad01ad/runs/49becb79/m200/...` (artifact.json, heads.pt, full_weights/...) plus `_evac_manifest/17eedd296fe8.tsv`; compare these with your `checkpoint_members` names.
- The operator will deliver the `m.sha` payload from d00 (I corrected my request).

Decide from the listings what the job really needs from e00 (possibly nothing) and fix the stages accordingly; the rule stands that every inventory is checked before large extraction and all mismatches are reported together.
EOF
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) orch-home-distill-79: READ THE LISTINGS: e00 (58 members) has no m.sha; the FLA manifest is ebe69df8/m.sha (87,191 B) in d00; CP1 parts hold ap/f2ad01ad/runs/49becb79/m200/... (10 members); e00 carries the model manifest (arm/frozen/6f27ae81/model.json). CORRECTED my request to orchard_cp2 ($N: read m.sha from d00) and told if_p0 what the listings show." >> $C/ORCH_HANDOFF.md