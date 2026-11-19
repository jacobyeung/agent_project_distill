# Relative distance at step 200: near ties and stable perception errors, not instance ambiguity (lane san_dd_reldist, 2026-11-19)

Scope: all 131 items wrong at step 200 (run 673bc60f, B2048 arm), 40 of 150 on dev-S1 and 91 of 279 on R0-dev (59 of 186 closest, 32 of 93 farthest), each read beside the same item at step 100 and step 544 (run 469ddece). Loader: `san_kit` (sources in `K.SOURCES`). Per-item table: `work/WRONG131.tsv` (131 rows: orders at steps 200 and 100, step 544's four values, reference citation, picks, flags, class). Parsers and rules: `work/rd.py`. Every count below comes from those files; guesses are labelled.

## 1. Answers

**Q1. Most errors are near ties (74 of 131) or stable perception errors (35 of 131); instance ambiguity touches 10 and ranks first for only 4.** I classified each wrong item by the first rule it meets, in this order:
- (e) wording: the reference's name is contained in the truth's name, the truth is a part of the reference, or the reference is the generic class "structure";
- (a) near tie: step 544's values for the truth and the step-200 pick differ by a factor of at most 1.25, or the truth sits at the endpoint or the rank next to it at all three steps;
- (c) gross: the truth sits two or more ranks from the endpoint at all three steps;
- (b) several instances: the truth or the reference is a class the same room's counting items count at 2 or more, or carries a plural name;
- (d) unstable: the pick changes between steps;
- (f) the rest. Every one of the 12 (f) items has the same wrong pick at all three steps while the truth's rank moves, so (f) is a stable wrong pick, closer to (c) than to (a).

Every record parses: the step-200 and step-100 orders name all four options on 429 of 429 items, and step 544 states a metre value for all four candidates on 429 of 429. The three steps pick the same candidate on 58 of 131 wrong items (21 of 40 dev-S1, 28 of 59 closest, 9 of 32 farthest). Answer-letter mapping fails on 1 of 131 (`d6eea8cb010f2e223a6eb0a0`, already known).

| Class | dev-S1: n; type pts; VSI pts | R0 closest: n; leaf pts; ReVSI pts | R0 farthest: n; leaf pts; ReVSI pts | R0 type pts (of 279) |
|---|---|---|---|---|
| (a) near tie | 24; 16.00; 2.000 | 30; 16.13; 1.152 | 20; 21.51; 1.536 | 17.92 |
| (c) gross | 5; 3.33; 0.417 | 13; 6.99; 0.499 | 5; 5.38; 0.384 | 6.45 |
| (f) stable pick, rank varies | 4; 2.67; 0.333 | 6; 3.23; 0.230 | 2; 2.15; 0.154 | 2.87 |
| (d) unstable | 4; 2.67; 0.333 | 6; 3.23; 0.230 | 4; 4.30; 0.307 | 3.58 |
| (b) several instances | 3; 2.00; 0.250 | 1; 0.54; 0.038 | 0; 0; 0 | 0.36 |
| (e) wording | 0; 0; 0 | 3; 1.61; 0.115 | 1; 1.08; 0.077 | 1.43 |
| Total | 40; 26.67; 3.333 | 59; 31.72; 2.266 | 32; 34.41; 2.458 | 32.62 |

The two near-tie tests barely agree: of the 75 wrong items that pass either (74 after the wording class takes one), 31 pass only the value test, 31 only the adjacency test and 13 both. On the farthest leaf the value test carries 18 of the 20. Flags overlap (non-exclusive counts over the 131): value near tie 44, adjacent at every step 44, gross at every step 30, unstable 73, any counted or plural name (the brief's literal rule (b)) 41, truth or reference multi-instance 10.

**Q2. Instance ambiguity does not lower accuracy, and R0-dev has almost none.** On dev-S1, the 62 items with a candidate counted 2 or more in the same room score higher than the other 88 at both steps: 48 of 62 (77.4%) against 62 of 88 (70.5%) at step 200, and 47 of 62 (75.8%) against 59 of 88 (67.0%) at step 544. When the truth class itself is multi-instance the score is 19 of 25 at step 200 (18 of 25 at step 544), against 91 of 125. The reference is never a counted class (0 of 150). R0-dev's generator appears to choose unique objects: of 1,029 distinct room-and-name pairs among its relative-distance objects, only 1 matches a single-class counting item ("boxes", `6464a926199c466038e0ed4a`), although every R0-dev room has such counting items. In the two-class counting items, 79 of 108 mentions of a relative-distance object prove exactly one instance (the sum equals the number of classes); the other 29 are undetermined, and those items score 19 of 29 at both steps. Plural names on R0-dev (70 items) score 44 of 70 against 144 of 209 at step 200, a 6-point gap with a standard error near 6.6. Fifteen wrong items name a counted class (list in section 2, table C); in 7 of them the counted class is neither the truth nor the pick.

Training rows: I joined all 20,665 rows of `object_rel_distance|w1g|rows_rebuild_d0_v1` (store v7, primary-key reads) with the store's 20,669 counting rows of the same scene. Of the 18,248 rows whose scene has counting rows, 10,836 (59.4%) name a class counted 2 or more, 3,496 (19.2%) have a multi-instance truth class, and 488 (2.7%) a multi-instance reference. A question carries an instance instruction on 926 of 20,665 rows (340 of the 10,836). No trace names an instance (0 of 20,665). No row field records how the truth treats instances: the provenance holds only `gt_kind: gt_canonical_trace`, a frame-map hash and a source pack on trinity-2-18 or 2-28 (`/scratch/jjyeung/orch_cd/weak_data/out/a3/PACK_object_rel_distance.jsonl.gz`), which cannot be read.

**Q3. Two thirds of the 62 adjacent-rank errors are confident by step 544's own numbers, but those numbers still predict difficulty.** Step 544 puts the truth and the step-200 pick within a factor of 1.25 on 20 of 62. Its own endpoint margin (its endpoint value over the next) is at most 1.25 on 21 of 62 adjacent errors, 33 of 69 farther errors and 48 of 298 right items. Medians: 1.38, 1.28 and 2.08. Step 544 is also wrong on 45 of the 62 and picks the same wrong candidate on 37. The margin predicts correctness at both steps: step 200 scores 48 of 101 (47.5%) where step 544's margin is below 1.25, 94 of 142 between 1.25 and 2, and 156 of 186 (83.9%) at 2 or more. So small margins mark items that are close to coin flips. The 48 right items with the same small margin are mostly luck: the small-margin bin splits about evenly between right and wrong. Correctness flips between steps more often on the adjacent errors (25 of 62, 40.3%) than on farther errors (13 of 69) or right items (68 of 298, 22.8%).

**Q4. The reference line cites a frame, a value above 32 or a region word; frame citations go with higher accuracy, and no trace at any step locates a candidate.** At step 200 a frame from 1 to 32 scores 29 of 37 on dev-S1 and 70 of 94 on R0-dev; a value above 32 scores 10 of 13 and 20 of 31; a region word ("in the left", "in the right half of the rightmost image") scores 71 of 100 and 96 of 151. At step 544 the gap vanishes on R0-dev (24 of 37 against 153 of 236), so it may reflect which items the model can find rather than the citation itself (guess). Every training row cites a frame from 1 to 32 (max 32 over 14,363 parsed citations), yet step 200 writes a region word on 100 of 150 dev-S1 and 151 of 279 R0-dev items, and a value above 32 on 13 and 31. The reference is never multi-instance on dev-S1; R0-dev plural references score 7 of 11. No trace at any step locates a candidate: the regex hits (5 at steps 200 and 100, 4 at step 544) are all a reference line naming an overlapping candidate, for example "find the vase, first seen in the flower vase". Step 544's "and each candidate" carries no location. The reference line names a candidate as its place on 9 items at step 200 and 32 at step 544.

**Q5. On farthest questions only the far end is wrong in 14 of 32; the truth is ranked nearest in 9 of 32.** In the step-200 order, the truth of a wrong farthest item is third on 14, second on 9 and first on 9. Far-end accuracy matches near-end accuracy in the same 93 rooms: 61 of 93 (65.6%) farthest against 127 of 186 (68.3%) closest at step 200, and 61 of 93 against 120 of 186 at step 544. The training rows hold no farthest question (0 of 20,665), so the far end transfers from the closest rows.

**Q6. A routed form would cost 9 calls and about 650 tokens. Under optimistic assumptions it beats direct by 2 to 8 points, but the only measured routed read lost by 28, so a gain is not established.** The gap head prints a distance on 85 of 150 routed distance items at step 200. Its median relative error is 0.11, 68% of its values fall within 25%, and its own MRA is 65.3. Across pairs of distance items it orders the true distances correctly on 0.60 of pairs whose true ratio is below 1.10, 0.65 at 1.10 to 1.25, 0.81 at 1.25 to 1.5, 0.83 at 1.5 to 2 and 0.87 at 2 or more (n = 316, 431, 538, 631, 1,651). Resampling those 85 errors independently for four candidates gives 0.715 when candidate distances are drawn from the 150 distance truths and 0.772 when they follow step 544's stated configurations; direct scores 0.695 (298 of 429). Both simulations assume independent errors, every call served and every object grounded as often as on distance items (guesses). The only measured routed relative-distance read is the deployed-mask program: 44.0 against direct 72.0 on dev-S1 (61.7 against 74.8 on answered items), and +2.1 with ground-truth masks (`TRACE_RULING_20261115.md`, lines 115 and 161). The head is weakest where direct is weakest: below a 1.25 ratio it orders 0.60 to 0.65 of pairs correctly, and direct scores 48 of 101 where step 544's margin is below 1.25. The routed read never served more than 3 calls on any of 636 items at either step, and 115 of 134 room items at step 544 stopped with `max_calls` after 2 recorded calls. The cap value sits inside the sealed payload, so 9 calls very likely exceed it. Cheaper variants: gap calls for the direct top two (5 calls) score at most 0.839 times the pairwise accuracy, because the truth is in the direct top two on 360 of 429; break-even needs 0.83 pairwise, and random pairs give about 0.80, so expect about 0.67 (guess). A direct trace that compares the top two needs no call, but the closest evidence is negative: step 544's explicit comparison of all four candidates in metres scored 2.5 to 2.7 points below step 200's bare order.

**Q7. Four wording defects cost 0.19 ReVSI points; one label cluster is suspect.** Priced defects (all wrong at step 200): `ba14ba2ac2a20cfb282711e3` (farthest; reference "adapter" inside the truth "power adapter"; wrong at all three steps; 0.077), `fc7bcd5a41ea580a57516a22` (truth "toilet flush button" is part of the reference "toilet"; wrong at all three steps; 0.038), and `5f8c9f829534c0f4a3b3727f` and `927caec4a53e4ce8b3c76fa1` (reference "structure"; 0.038 each; the second is right at steps 100 and 544). Unpriced defects:
- `22fa7c6e26a05938ffcf0e22` lists the reference "bullettin boards" as the candidate "bulletin board"; right at every step.
- Two candidates share a singular name in `2dfe54ef125627d1c8db395d` (book, books), `451397fd37033022bcf9a0a9` (book, books) and `7d833161ac70701dbfb90f28` (bag, bags); the two wrong ones pick an unrelated candidate.
- The pick of `ae22896a9fe9c0348c050344` is the misspelled "whtieboard eraser".
- `9ae6eee6ed7f4c46f1aeff3c` carries the raw label "object/blanket"; it is right.

The suspect cluster is d1/scene0642. Eight items ask what is nearest the mirror, and their labels agree: the door is nearer than the bed, which is nearer than the rest. The model puts the bed (0.71 m at step 544) before the door at every step on 4 of them: `vsi590k_085253`, `vsi590k_085265`, `vsi590k_085273` and `vsi590k_085289` (2.67 type points, 0.33 VSI points). The consistency of the labels argues against a random label error. Frames would settle it.

## 2. Evidence

**Table A. Accuracy by step 544's endpoint margin (all 429)**

| Margin | Items | Step 544 | Step 200 |
|---|---:|---:|---:|
| 1.00 to 1.10 | 30 | 15 (50.0%) | 12 (40.0%) |
| 1.10 to 1.25 | 71 | 32 (45.1%) | 36 (50.7%) |
| 1.25 to 1.5 | 61 | 32 (52.5%) | 35 (57.4%) |
| 1.5 to 2 | 81 | 62 (76.5%) | 59 (72.8%) |
| 2 or more | 186 | 146 (78.5%) | 156 (83.9%) |

**Table B. Accuracy by reference citation at step 200**: dev-S1 frame 1 to 32, 29 of 37; above 32, 10 of 13; region, 71 of 100. R0-dev frame 1 to 32, 70 of 94; above 32, 20 of 31; region, 96 of 151; "the question", 2 of 3. Among the 131 wrong items the citations are 32 frames in range, 14 above 32, 84 region words and 1 "the question".

**Table C. Wrong items naming a counted class** (T = truth, P = step-200 pick, o = other; count from the same room): `vsi590k_069864` window=2 (o); `vsi590k_069918` window=2 (T); `vsi590k_085265`, `vsi590k_085289` trash bin=2 (o); `vsi590k_194281` ceiling light=3 (o); `vsi590k_204702` table lamp=2 (P); `vsi590k_211211`, `vsi590k_211213` plant=7 (T), pillow=4 (o); `vsi590k_211219` pillow=4 (o); `vsi590k_218297` trash can=3 (o); `vsi590k_220547` door=2 (T); `vsi590k_282416` chair=2 (P), stool=2 (o); `vsi590k_282446` table=5 (T), sofa=3 (P), chair=9 (o); `vsi590k_282448` table=5 (T), chair=9 (o); `6464a926199c466038e0ed4a` boxes=2 (o).

**Claim: near ties by step 544's own numbers.**
- `2f441715cdb7285993d5a92c` (R0, closest). Q: "...which of these objects (computer tower, curtain, monitor stand, paper towel) is the closest to the trash bin?" Truth paper towel; answer monitor stand at every step. Step 200: "the nearest-to-farthest order from the trash bin is: monitor stand, then paper towel, then computer tower, then curtain." Step 544: "monitor stand 3.77 m; ... paper towel 4.01 m."
- `vsi590k_211083` (dev-S1). Q: "...which of these (bed, tv, shoe rack, pillow) is closest to the table?" Truth bed; answer tv (steps 200 and 100), bed at step 544. Step 200: "...order from the table is: tv, then bed, then pillow, then shoe rack." Step 544: "bed 0.86 m; tv 0.89 m".
- `873ef453f65d671b455ba7db` (R0, farthest). Q: "...(cup, laptop stand, monitor, shelf) is the farthest from the pedestal fan?" Truth shelf; answer laptop stand. Step 200: "...is: shelf, then cup, then monitor, then laptop stand." Step 544: "laptop stand 1.13 m; ... shelf 1.16 m. The farthest is the shelf."

**Claim: many adjacent errors are confident, persistent swaps.**
- `vsi590k_085265` (dev-S1). Q: "...(bed, trash bin, tv, door) that's closest to the mirror." Truth door; answer bed at all three steps. Step 200: "...order from the mirror is: bed, then door, then tv, then trash bin." Step 544: "bed 0.71 m; door 1.33 m."
- `vsi590k_069864` (dev-S1). Q: "...which one of (table, desk, refrigerator, window) is closest to the closet?" Truth desk; answer refrigerator at all three steps. Step 200: "...is: refrigerator, then desk, then table, then window." Step 544: "refrigerator 0.67 m; desk 1.16 m".
- `vsi590k_220563` (dev-S1). Q: "...(trash can, monitor, laptop, headphones) to the bed". Truth headphones; answer trash can at all three steps. Step 200: "...is: trash can, then headphones, then monitor, then laptop." Step 544: "trash can 0.71 m; ... headphones 1.31 m".

**Claim: gross errors rank the truth last at every step.**
- `vsi590k_282416` (dev-S1). Truth dishwasher; answer chair at all three steps. Step 200: "...order from the refrigerator is: chair, then stool, then table, then dishwasher." Step 544: "dishwasher 2.13 m; stool 1.91 m; table 1.96 m; chair 1.56 m."
- `c6224959a11be46ca8e04b63` (R0). Q: "...(faucet, sink, soap dispenser, toilet paper dispenser) is the closest to the toilet brush?" Truth toilet paper dispenser; answer sink. Step 200: "...is: sink, then faucet, then soap dispenser, then toilet paper dispenser." Step 544: "sink 0.00 m; ... toilet paper dispenser 1.65 m."
- `a8ba0a37ca62817cfeac9d5d` (R0). Q: "...(bookshelf, hanger, heater, trash bin) is the closest to the door frame?" Truth heater; answer hanger. Step 200: "...is: hanger, then trash bin, then bookshelf, then heater." Step 544: "hanger 0.00 m; heater 6.78 m".

**Claim: multi-instance items read like the others; no trace handles instances.**
- `vsi590k_282446` (truth table, 5 in the room). Step 200: "...order from the fireplace is: sofa, then tv, then chair, then table." Step 544: "table 0.39 m; sofa 0.25 m".
- `vsi590k_211211` (truth plant, 7 in the room). Step 200: "...order from the ceiling light is: chair, then coat hanger, then pillow, then plant."
- `vsi590k_069918` (truth window, 2 in the room). Step 200: "...order from the chair is: sofa, then window, then lamp, then refrigerator." Step 544: "sofa 0.00 m; window 0.23 m".

**Claim: wording defects.**
- `ba14ba2ac2a20cfb282711e3`. Q: "...(dustbin, power adapter, roll up whiteboards, smoke detector) is the farthest from the adapter?" Truth power adapter. Step 200: "...is: power adapter, then roll up whiteboards, then dustbin, then smoke detector." Step 544: "power adapter 0.00 m".
- `fc7bcd5a41ea580a57516a22`. Q: "...(counter, soap dispenser, toilet flush button, trash can) is the closest to the toilet?" Truth toilet flush button; answer trash can at all three steps.
- `5f8c9f829534c0f4a3b3727f`. Q: "...(closet, door stopper, keyboard, mattress) is the closest to the structure?" Step 200: "find the structure, first seen in frame 37."

**Claim: on farthest questions the most common error is the far end alone (14 of 32).**
- `aac90962d6d1af05b59fe655`. Truth jacket; answer pinboard. Step 200: "...order from the heater is: banner, then telephone, then jacket, then pinboard." Step 544 is right: "jacket 2.76 m; ... pinboard 2.22 m".
- `2c5b2b9f4806d7dcbc0ce847`. Truth paper; answer photoframe. Step 200: "...is: stovetop, then postcard, then paper, then photoframe."
- `535915eba29aece6192cccde`. Truth mini oven; answer counter. Step 200: "...is: shoe box, then mattress, then mini oven, then counter."
- Reversed case, `304c9523c47669064c02432a`. Truth box; answer metal tray. Step 200: "...order from the books is: box, then trash can, then suit, then metal tray." Step 544 also gives "box 1.25 m" as the smallest value.

## 3. For vehicle N (ranked)

1. **Add hard pairs, keep the form.** Add about 3,000 rows (guess) to `object_rel_distance|w1g|rows_rebuild_d0_v1`, built from training scenes whose ground-truth nearest and second-nearest candidates differ by a factor below 1.25, in the current trace form. The row builder has the geometry; the rows store no distances. This addresses class (a): 74 dev items, 2.0 VSI and 2.7 ReVSI points. Basis: Table A shows the small-margin bin is a coin flip (48 of 101); the rows store no distances, so I cannot tell how many hard pairs the family already holds, but the builder can count them from its geometry. Expected effect: unknown, guessed at a quarter of class (a). The next read shows failure if accuracy in the bin where step 544's margin is below 1.25 stays at or below 50% and adjacent-rank errors stay at 55 or more of 429. Example (a real store row, `qe9607f3d46dcc20440d27cf0`; a hard-pair row keeps exactly this form):
   `Step 1: find the backpack, first seen in frame 12.` / `Step 2: the nearest-to-farthest order from the backpack is: thermos, then box, then air vent, then broom.` / `The question asks for the closest object, the thermos.`
2. **Locate each candidate by frame.** Reword the family so Step 1 locates every candidate, not only the reference, with frames taken from the builder's visibility map; the trace ruling already asks direct traces to locate objects by frame. This addresses classes (c) and (f): 35 items, 0.75 VSI and 1.27 ReVSI points. Basis: no trace at any step locates a candidate, and 16 of 23 gross errors repeat the same wrong pick at every step, the signature of a wrongly identified object (guess). The next read shows failure if items with the truth two or more ranks from the endpoint stay at 20 or more of 429, or if the cited candidate frames do not show the candidate. Example (frame numbers are placeholders the builder fills):
   `Step 1: find the closet, first seen in frame 20; the desk is in frame 20, the refrigerator in frame 23, the table in frame 17, the window in frame 26.` / `Step 2: the nearest-to-farthest order from the closet is: desk, then refrigerator, then table, then window.` / `The question asks for the closest: the desk.`
3. **Routed minority, only if the call cap allows 9 calls.** Ruling item 6 (both paths per type) would give about 2,000 routed rows, assigned where the head's ordering is right. Expect no gain as the main form (Q6); the rows exist for RL exploration. The next read shows failure if routed dev traces end in `max_calls`, or if the routed answer scores below direct on the same items. Example for `vsi590k_069864` (responses are filled by the heads at build time; 5 ground and 4 gap calls; about 5 x 84 + 4 x 38 + 80 = 650 tokens, against a median of 319 for the 3-call distance traces; the routed choice traces end with the letter, as here):
   `I will ground the closet and each candidate, then measure the gap from the closet to each.` / `<ground obj="closet" mode="box">` `<tool_response>`...`</tool_response>` / `<ground obj="table" mode="box">`...; `<ground obj="desk" mode="box">`...; `<ground obj="refrigerator" mode="box">`...; `<ground obj="window" mode="box">`... / `<gap a="closet" b="table" rule="box_grid_5cm">` `<tool_response>distance <d1> m</tool_response>`; the same for desk, refrigerator and window / `The gaps from the closet are: desk <d2> m, refrigerator <d3> m, table <d1> m, window <d4> m.` / `The question asks for the closest: the desk. That matches option B.` / `</think>` / `B`
4. **Wording filter.** Drop or rename the 143 training rows whose reference name overlaps a candidate's name and the 575 with generic or raw names ("structure", "object", "stand", "board", names with "/"). Flag the four (e) dev items and `22fa7c6e26a05938ffcf0e22`. The training change can recover at most the 0.19 ReVSI points of class (e) (guess: little).
5. **No change for instances or farthest.** Multi-instance items score higher, not lower (Q2), and the far end scores as well as the near end (Q5). An instance clause ("the nearer of the two chairs") would be honest only from ground-truth instance distances, and the data give it no target. The next read would contradict this if the 62 multi-instance dev-S1 items fall below the other 88.

## 4. Refuted or corrected

- First wave (`san_m200_rel_dist`, sections 2 and 8) calls actual room multiplicity unknown. The same rooms' counting items supply it: dev-S1 multi-instance items score 77.4% against 70.5%, and R0-dev's objects appear to be unique (1 of 1,029 room-and-name pairs is counted).
- The first wave's hypothesis that missing candidate locations permit instance confusion, and its change 2 ("distinguish instances" across about 3,000 rows), do not survive the instance half. Locating candidates stays plausible for gross errors.
- The deep wave says a perfect comparison of the two candidates nearest the endpoint recovers 62 of 131. The ceiling is right, but only 20 of the 62 are near ties by step 544's numbers, and the gap head orders pairs below a 1.25 ratio correctly 0.60 to 0.65 of the time, so a head-backed comparison will not reach it.
- The first wave lists `ba14ba2ac2a20cfb282711e3` as a possible ambiguity. Step 544 resolves it toward a wording defect by writing "power adapter 0.00 m", treating the two names as one object.

## 5. Not established

- Whether near ties by the model's numbers are near ties in geometry: no dev item carries candidate distances. Ground-truth closest-point distances for the 429 items (from the scene annotations) would settle it, and would also show whether the small-margin bin needs better perception or is near label noise.
- How the training truth treats instances: no row field says, and the source pack sits on an unreachable node. Reading the pack's generator or its per-row fields would settle it.
- The gap head's accuracy on relative-distance objects, which are often small R0-dev objects ("coax outlet", "toilet flush button"): measured only on distance items. A diagnostic that serves the 4 gap pairs of each of the 429 items (1,716 calls) would settle it.
- The routed call cap: inside the sealed payload; the read's owner can state it.
- Whether region-word citations cause errors or mark hard items: a row-form ablation with forced frame citations would settle it.
- Whether d1/scene0642's mirror labels are right: viewing the frames would settle it.

Files: `work/rd.py` (loaders and rules), `work/WRONG131.tsv` (per item), `work/reproduce.py` (prints the five numbers above; `/usr/bin/python3`, about 1 minute).
