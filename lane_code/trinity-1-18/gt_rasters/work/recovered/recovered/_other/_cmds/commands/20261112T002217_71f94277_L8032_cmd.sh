<!-- recovered by seal_plan: transcript=71f94277 line=8032 utc=2026-11-12T00:22:17.141Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ)
cat > leg_s1_tree/inbox/${T}_ORCH_mdg_sources_located.md <<'EOF'
# ORCH: the MDG inputs are located (all on trinity-2-18; none on Orchard)
Inventory with paths, sizes, shas and evidence: /scratch/jjyeung/orch_cd/mdg_assets_inv/MDG_ASSET_SOURCES.md (30 lines; read it whole). MDG-A trained on trinity-0-18, never on Orchard, so every MDG input must travel. Root R = /scratch/jjyeung/orch_cd/mdg_build/work (read-only for you).
Decide and bind, as pinned inputs (path + sha256) in the kit config:
1. clips: MDG-A used TWO files (R/data/r7/x/r_119970/clips_c.jsonl and r_119971/clips_c.jsonl); your config has one slot. Take both (a list, or one concatenated file you build in your lane with its sha) and say which.
2. frames: R/data/frames holds 109,080 AWS-resized PNGs; the frame shas in clips_c.jsonl refer to these resized files, so the admission's frame hash audit for the MDG stream must check against clips_c / R/data/c/C_MANIFEST.json, not the original RGB stores. The same frames exist as four tars R/data/c/c_0..c_3.tar (13.4 GB); the kit should stage from those tars.
3. rasters: R/data/r7/x/r_119970/c and r_119971/c (712 MB, no sha manifest): compute one (per-file sha list, CPU, local disk, nice) and pin its hash.
4. init artifact: best step 2100 (mdg.pt sha a3ec5da5...) or final step 5000 (78ac736f...). MDG-A was trained on frozen T0 m800 and judged NO-GO as a standalone decoder (held-out in-mask 65.1 against a bar of 84). State which one the leg starts from and why, and check that it loads onto the leg's parent (CP1 m200) with exact key and shape coverage. confusers.json was built from T0 m800's input-embedding rows: rebuild it for the parent if those rows differ (make_confusers.py), else pin the existing file and record the equality check.
5. exclude list: your dev-S1 and benchmark-v2 lists supersede R/cfg/exclude_scenes.json; bind the old one only if the config requires the key, and say so.
Then write out/MDG_INPUTS.json (each asset: source path on 2-18, bytes, sha256, target key) and send its path to orchard_cp2's inbox; it pushes exactly that list to Orchard (I pre-approved the copy). Create no new large files on 2-18: /scratch is at 96 GB free, below the 100 GB floor.
EOF
cat > orchard_cp2/inbox/${T}_ORCH_mdg_inputs_push.md <<'EOF'
# ORCH: MDG inputs located; pre-approved push once leg_s1_tree sends its list
Inventory: /scratch/jjyeung/orch_cd/mdg_assets_inv/MDG_ASSET_SOURCES.md. MDG-A trained on trinity-0-18, never on Orchard, so nothing is in the Orchard cache. Correction to your plan line 38: e84d901c/z (986ba20f.npz) is the pose/gravity/depth readout bank, not an MDG input.
leg_s1_tree will send you out/MDG_INPUTS.json (each asset with its 2-18 path, bytes, sha256). When it arrives, this push needs no further go:
- about 14.3 GB in total: four existing frame tars (mdg_build/work/data/c/c_0..c_3.tar, 13.4 GB; send them as they are), one tar stream of the rasters (712 MB), and one small tar (clips, vocab, confusers, stem, init artifact);
- from 2-18 straight to Orchard, one transfer at a time, at most 8 MB/s, registered with the governor as your earlier pushes were; build no new tar file on 2-18 (stream the rasters; /scratch is below its floor);
- destination: your cache under /home/jjyeung/okit on Orchard (937 GB free), NOT /project/community (main asked us to write nothing large there); sha256 checked on arrival against the list;
- if a transfer is killed or drops, do not retry: post a BLOCKER.
Report when done, in the same RESULT as the first tar if they finish together.
EOF
echo "$(date -u +%Y-%m-%dT%H:%MZ) MDG inventory (Sonnet; mdg_assets_inv/MDG_ASSET_SOURCES.md): MDG-A trained on trinity-0-18, never on Orchard; verdict NO-GO as a standalone decoder (in-mask 65.1 vs bar 84); all eight MDG inputs exist on 2-18 under mdg_build/work (clips 2 x 22 MB, rasters 712 MB no sha, frames 13.4 GB as c_0..c_3.tar + extracted, init mdg.pt 171 MB best step 2100 / final 5000, stem 47 MB, vocab, confusers built from T0 m800 embeddings); frame tars also on Mind (mdg_000/001.tar); none on Orchard. Told leg_s1_tree to bind them as pinned inputs (out/MDG_INPUTS.json) and check init/confusers against CP1 m200; pre-approved orchard_cp2's push (14.3 GB, 2-18 -> Orchard /home/jjyeung/okit cache, 8 MB/s, governor, no new tar on 2-18)." >> ORCH_HANDOFF.md