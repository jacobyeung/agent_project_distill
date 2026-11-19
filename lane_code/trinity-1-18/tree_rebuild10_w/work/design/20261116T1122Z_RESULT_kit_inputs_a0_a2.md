# RESULT kit_inputs_a0_a2 (rows_a2, trinity-1-3): why kits A0 8cdda797 / A2 58a9b42e are GO=false, inputs qualified
Detail: KIT_INPUTS_A0_A2.md and KIT_INPUT_QUALIFICATION.json beside this event (3 Orchard calls, sha256 on Orchard).
- GO=false by design (k/4.json): blockers component evidence, post-filter counts, host admission, independent review.
- Four defects the frame-host job or the leg would hit (both kits unless noted), for tree_rebuild3:
  D1 19 staging entries point at okit/in/e00, which lacks them (13 eb3429c5 shards, frame_map, frame_plan, input_source_tokenizer, vxm_m4 receipt, 7c9f2d84 receipt). Real sources, sha-verified on Orchard today: ~/okit/i/eb3429c5/eb3429c5.tar f0e71513; ~/okit/x/07ca49df/k/{frame_map 17aa3e9e, frame_plan 7cc01f36, input_source_tokenizer 5f9e4d49}; okit/in/cr/524b14f9f180.p00; okh7/7c9f2d84/receipt.json 93b21a3a.
  D2 init artifact 1d6eeb28 staged from /tmp/jjyeung/in/… : absent on Orchard; needs the real export location (or the D0 export the init rule picks).
  D3 streams/vqa and routing bind the SEALED stores (vxm_m4 524b14f9, r16 9a7f3310); no D0 v5, A0 family or A2 row is staged: the kits would train the sealed rows.
  D4 (A2) dense manifest is the 1-clip synthetic fixture with a Trinity path (GF-1 track).
- Qualified equal: 34/34 inline payloads per kit; e00 4b66cc24 (bank + training_scenes members OK); rt_b8b60bce (r16 receipt OK); bwrap; rows_inventory d6d6a53a; depth_init fd60ac2f. venv tar (8.1 GB) not hashed. remove_files[4,5] are empty files (e3b0c442): flag.
- I close none of D1-D4 myself (tree code and the init choice are not this lane's); D3 closes when my A2 rows are admitted and uploaded.
