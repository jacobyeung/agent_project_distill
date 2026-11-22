# RESULT PASS n_review1h (to ORCH, tree_rebuild25; copy n_ops9): task A as restated by ORCH RULING 0211Z item 3, for arming
Verdict: PASS. Approved routing hashes for arm_launch.sh / arm_routing.py:
- routing_selection.json sha256 a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73
- regenerated_sha256 (compact sorted digest of receipt.json 38c52f008d131a8554d3d18974f4d2de1e77bdf092c747132df477db8ff08398) 522a3be39b90d6fd8ec4dd599d89e1d5762c3a1a150e198c0c0bbb70f931ba39
- N routing database (receipt database) 5e35c3ce600a867be194911642caccb23098035b4bf08909e519a170a1c243df, 849,543,168 B, 43,101 rows
- P base routing database (selection inputs_pinned.routing_database) 4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84, 837,255,168 B
Grounds, each opened or run by me or my predecessor n_review1g:
1. (a), (b), (c) on evidence run 173881 (evidence/n_review1g/taskA_evidence_run_173881.md): field list = f.json 8be6cc63, content_field_counts empty; four classes, unclassified empty; routing chain refused 0 of 43,101, complete, key sets c2ba56c5, exempted 10,945, still checked 32,156, three controls; (ii) 4,768 a1869ae2 scenes + 29 on 6add0ad5; (iii) U_Faithful 747 -> 718.
2. Identity (my reads 02:12Z, evidence/n_review1h/arming_inputs_s74_0212Z.txt and pool_identity_o34_0212Z.txt): routing_selection.json a49f117f and receipt.json 38c52f00 are byte-equal in X/o/173881, X/o/173912 and 1-18 W/work/d173912/173912 (the arming inputs); selection rows 43,101 = receipt count 43,101, receipt schema c1-routing-stream-v1 stream routing; my compact digest of receipt.json = 522a3be3 = the selection's regenerated_sha256; selection regenerated_receipt pins 38c52f00; db_bytes.json lists 5e35c3ce 849,543,168 B and 4e8e6c04 837,255,168 B.
3. Pool objects on Orchard, sha256sum run by me at 02:12Z: X/u/a49f117f (10,997 B), X/u/5e35c3ce (849,543,168 B), X/u/4e8e6c04 (837,255,168 B), each equal to its name in full.
4. arm_routing.py w24z11b 3dbd7af2 differs from 1a4b900b only in kit_layout plumbing; its verdict gate is unchanged (my diff, work/s71.out).
Under RULING 0211Z, (d) sampler population = N database, P1 reader_filters, the census, item 3's actual counts and item 8's grounds are judged at the review gate of the launch job, not in this verdict.
