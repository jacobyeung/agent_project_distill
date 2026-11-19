# 64-viewpoint read versus the 32-frame read plan (read package A)

The student reads the same nested 64 viewpoints it trained on. The anchors, the question text and the G3T
tower input stay as in the 32-frame plan.

| Item | 32-frame read plan | 64-viewpoint read |
|---|---|---|
| Student frames | 32 anchors from FRAMES.json (`parity.trainer_row`) | the anchors plus 32 bisection frames, nested by `frame_input.nest_row`, the training function |
| Nesting rule | none | `carrier_c1_data.nested_indices(anchors, 64)`, as in training |
| Student frame source | FRAMES.json pins | FRAMES.json pins for anchors; `student_manifest` pins for bisection frames |
| Read layout | `parity.py:208` hard-codes `count=32` for both read and export layouts | read layout comes from settings `frames`; export layout from `artifact.json` `frame_input`; every key must agree |
| Layout check | `core.check_layout` compares a constant with itself | `f64_read.check_layout` compares layout, count, anchors and rule, so a 32-frame export refuses a 64 read and the reverse |
| Markers, carriers | `Frame 1..32`, 32 carriers | `Frame 1..32` on anchor groups only, 32 carriers on anchors; bisection groups carry pixels only |
| Visual tokens (4:3 / 16:9) | 4,160 / 4,608 | 8,320 / 9,216 |
| Private depth input | 32 groups | 32 anchor groups (`frame_input.anchor_view`) |
| Tower (G3T) frames | DENSE_MANIFEST (`devs1_tower_v2`) | unchanged |
| Video identity | digest over 32 anchors | digest over 64 frames (`devS1-pinned-PNG-clip-nested64-v1`), so memo keys differ |
| Adapter record count | `parity_adapter.py:134,245` require 32 | follow `settings.frames.count` |
| Settings | `prepare.py:54-62` | adds `frames`, `student_manifest`; `tree` is the sealed tree_f64 |

The tower's `devs1_tower_v2` dense rule differs from the nesting rule in all 55 of its 64-frame captures
(nearest GT-available frame to each midpoint plus one farthest frame), so the student cannot reuse it.
1,131 of the 4,864 bisection frames already exist as decoded PNGs in that manifest; 3,733 need decoding.
