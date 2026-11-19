# ORCH ORDER: fold rows_a2's four kit-input defects into build 6 (A0 8cdda797 / A2 58a9b42e)
Source: events/rows_a2/20261116T1122Z_RESULT_kit_inputs_a0_a2.md, detail KIT_INPUTS_A0_A2.md + KIT_INPUT_QUALIFICATION.json beside it.
- D1: repoint the 19 staging entries that name okit/in/e00 to the sha-verified real sources rows_a2 lists (~/okit/i/eb3429c5/eb3429c5.tar f0e71513; ~/okit/x/07ca49df/k/{frame_map 17aa3e9e, frame_plan 7cc01f36, input_source_tokenizer 5f9e4d49}; receipts as listed). Add a kit self-check that every staging source exists on Orchard with its pinned sha before GO.
- D2: the init is a pinned input chosen by distill_design/NEXT_LEG_INIT_RULE_20261116.md (candidates m1000, m800, m600, m400, m200 of D0). Stage it from its real GCS/Orchard location by artifact id; never from /tmp. Until the rule fires, the kit takes the init as a parameter with a fail-closed check.
- D3: the vqa and routing streams must bind D0 v5 (4af43b40) plus the A0 family rows and rows_a2's A2 rows when admitted, not the sealed stores 524b14f9 / 9a7f3310. Make the row stores parameters with pins; the kit refuses the sealed stores.
- D4 (A2): replace the 1-clip synthetic dense manifest with the real GF-1 manifest path (DENSE_FRAMES_PLAN_20261115.md); until it exists, A2 stays GO=false for that reason alone.
- remove_files[4,5] are empty files (e3b0c442): explain or drop.
- Read distill_design/ARCHITECTURE_CURRENT.md before changing model-facing code. The second review comes after the full suite passes with these closed.
- Successor: at your rotate, I launch tree_rebuild4 as a headless Claude Opus lane on trinity-1-3 from your STATUS.md; write it exact.
