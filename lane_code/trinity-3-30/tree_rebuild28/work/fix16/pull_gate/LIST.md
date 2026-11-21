# fix16 pull_gate: receipts of walk w1 that the reviewer gate reads (pulled 21:33:39Z, one Orchard call, 201,016 bytes of base64)
Source: orchard-community-3:/tmp/a15_f16_174198/w1 (scratch walk of mode q under the candidate; w/top is the namespace, w/live stands for X/o/174198/live). Archive pull_gate/w1_receipts.tgz (148,802 bytes); every file checked against its node sha256 after extraction (node_sums.txt).
Gate read: n_review1k/work/gate (gate.py header and need() calls, run_gate.sh fetch list, spell.py), read 21:33Z.

## Gate files present in the walk
| gate name | pulled file | note |
|---|---|---|
| live/s1.json | w/live/s1.json | written at plan time (pl.py:279-281); gate point 8 scene_census |
| live/s4.json | w/live/s4.json | same |
| request.json (spell.py) | w/top/p/q/p/request.json | frame_roots and frame_root_map under /tmp/jjyeung/q_22c714e1 |

## Gate files missing, and why
| gate name | writer | why absent |
|---|---|---|
| live/v.json, identity.txt, WAITING_REVIEW.json, e0.json-e3.json | rv.py | rv.py did not run (it follows the proof, d.py and h.py) |
| live/h0.json | h.py | h.py did not run |
| live/c0.json-c4.json | cs.publish from a.py:115 | runs only when the proof returns ADMIT; the walk stops in the frame audit |
| live/s2.json | sv.publish | no caller in kit 929ab213; n_review1k's gate.py no longer requires it (need() list read 21:33Z) |
| b/population.json, b/indices.json, b/reader_filters.json, b/binding.json, b/receipt.json | r1_population.bind_prepared | follows the frame audit (81 min in the first walk); not reached before the stop at 21:45Z |
| f.json | production_proof.forward | not run by design: the walk sees no device and stops before the forward |
| frames.json (spell.py) | frame audit finish() | the audit was still running at the pull; its inventory holds only second-name paths (REPORT 4b) |
| ADMIT.json | admit_test.sh on trinity-1-18 | needs v.json |

## Also pulled (not read by the gate; the walk's receipts so far)
- w/live/s0.json (30452 bytes, sha256 db91895cec8014cf)
- w/top/p/q/p/phase_prepare.complete.json (877 bytes, sha256 5878f9629755e40d)
- w/top/p/q/p/prepare_9bfb0f3bb6174ac8ab06e08c5b25c5cb/config.json (29818 bytes, sha256 63e6ed295ba68e7d)
- w/top/p/q/p/prepare_9bfb0f3bb6174ac8ab06e08c5b25c5cb/result.json (10218 bytes, sha256 f00139a4147f96e7)
- w/top/p/q/p/prepare_9bfb0f3bb6174ac8ab06e08c5b25c5cb/parent_grounding.json (1395 bytes, sha256 8a7f9bc1b6c529ea)
- w/top/p/q/p/prepare_9bfb0f3bb6174ac8ab06e08c5b25c5cb/handover.json (1116 bytes, sha256 6576ef67eda5218e)
- w/top/p/q/p/prepare_9bfb0f3bb6174ac8ab06e08c5b25c5cb/prepared/receipt.json (151380 bytes, sha256 9f8599321c295ea6)
- w/top/p/q/p/prepare_9bfb0f3bb6174ac8ab06e08c5b25c5cb/prepared/s1_receipt.json (151606 bytes, sha256 b85460492b730e0e)
- w/top/p/q/p/prepare_9bfb0f3bb6174ac8ab06e08c5b25c5cb/routing/receipt.json (34508 bytes, sha256 2159d6e599ae3371)
- w/top/p/q/p/prepare_9bfb0f3bb6174ac8ab06e08c5b25c5cb/routing/materialization.json (50392 bytes, sha256 10ea7d15bbbe9c11)
- w/top/p/q/p/prepare_9bfb0f3bb6174ac8ab06e08c5b25c5cb/pointing/receipt.json (13555 bytes, sha256 7151a8a453bc869f)
- w/top/p/q/p/prepare_9bfb0f3bb6174ac8ab06e08c5b25c5cb/vqa/receipt.json (6411 bytes, sha256 73e673d824460709)
- w/top/p/q/selection/receipt.json (34057 bytes, sha256 38c52f008d131a85)
- w/top/p/q/selection/materialization.json (49941 bytes, sha256 6faab9ccf0a47a5e)
- w/top/p/q/twins/room_audit.json (4655 bytes, sha256 ffa3d4c405d3e83b)
- w/top/p/q/twins/receipt.json (805 bytes, sha256 72b2a433c1606535)
- w/top/p/q/twins/augmentation.json (750 bytes, sha256 890f0171cbbe8e07)
- w/top/p/q/v.json (485 bytes, sha256 ccdd6a019da4aee3)
- w/top/p/q/m.json (1116 bytes, sha256 b4fcc91165c344a6)
- w/top/p/q/c.json (29680 bytes, sha256 1ace12d5be6252ae)
- w/top/p/q/n.json (33808 bytes, sha256 5c6126d20972a342)
- w/top/p/q/e.json (5220 bytes, sha256 b467c32bc1cace47)
- w/top/p/q/ss.json (6458 bytes, sha256 2a33fc61ed3f6704)
- log/go.log (699 bytes, sha256 471ee820f809ca19)
- log/q.log (230777 bytes, sha256 9921a9e264b56990)
- log/q.err (266 bytes, sha256 168d851032463f13)
- log/stop.log (192 bytes, sha256 7fd275fbad4fc933)
- log/bwrap_args.txt (8198 bytes, sha256 f113c4dc0d02cc59)

## All pulled files with sha256
(node_sums.txt: sha256, bytes, path)
