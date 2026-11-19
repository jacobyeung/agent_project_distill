# Relative direction on R0-dev (ReVSI-style), step 200: deep read (lane san_dd_dir)

I read all 190 wrong R0-dev direction traces at step 200 (41 easy, 68 medium, 81 hard) beside their step-100 and step-544 traces, the 300 facing twins and all 450 dev-S1 direction items. I also read 159 training rows in compact form (question plus the first 230 characters of the target, up to 9 per family across all 18 direction families) and parsed every one of the 93,370 direction rows in store v7 by primary key (opening, clause, turn, forward relation, answer, object names, frame citations). Scores are the B2048 arm. Code and small tables are in `work/`; `work/reproduce.py` prints the five numbers marked [R1]-[R5] in 8 s.

## 1. Answers

**Q1. Consistency across levels and subtypes.** R0-dev almost never repeats a triple: only 2 of its 576 (room, observer, facing object, target) triples are asked twice (4 items), and both are consistent and right, so the requested test has no power on R0-dev itself. Every linked source that does exist shows a stable asserted geometry whose errors are mostly consistent, not noisy. Six R0-dev pairs share the observer with the facing object and target swapped (the side must flip and front/back must stay): 4 are consistent and right, 2 consistent and wrong, 0 inconsistent. On the 150 facing twins (one triple asked toward and away), the away trace states the same forward relation as its toward twin on 144 of 150: 132 consistent and right, 12 consistent and wrong, 6 inconsistent. On dev-S1's 46 repeated triples the counts are 40, 4 and 2. On the same R0-dev item across checkpoints, 70 of the 115 toward items wrong at step 200 state the same wrong relation at step 100, and 69 of 115 are wrong at steps 544, 100 and 200 although step 544 wrote angles and step 200 writes words. Consistent-and-wrong outnumbers inconsistent by 1.6 to 2 times, so the remaining relation errors point to a stable misreading of the scene (or a label problem I cannot check), not to noise in the asserted line.

**Q2. The no-turn clause on away items.** Confirmed: 43 of 202 R0-dev away traces carry it, 14 of 66 easy, 5 of 65 medium and 24 of 71 hard; 31 of the 43 are wrong (5, 5, 21). One hard trace (`9a6a1be6...`) writes "keep that heading but flip forward to backward" and turns correctly, so 42 actually skip the turn. **The opening selects it, completely:** all 43 open with the D skeleton ("Step 1: find ..."), and 0 of the 159 away traces that open with "Seen:" skip the turn [R1]. No training row pairs an away question with the D opening: 0 of 49,901 D rows carry an away clause, and all 25,990 away rows open with "Seen:" and write the half turn [R2]. The opening in turn tracks the object names. The Seen rows use 73 distinct object names, the D rows 1,089 on their 20,344 R0-template questions alone [R2]; R0-dev away items whose three names all occur among the 73 open with D on 0 of 9, items with an unfamiliar name on 43 of 193. The room does not select it: 88 of the 97 R0-dev rooms with several items mix both openings. Mechanism (my belief, supported by the counts above): an unfamiliar name pulls the first line into the D skeleton, which covers 1,089 names and the R0 question template on 20,344 rows; once that opening is written the trace completes the only D continuation it was trained on. It restates the question's own clause ("The question has me face away from the Y") and appends the D tail ("so I keep that heading"). The mode grows with training: 14 away items opened with D at step 100 and 43 at step 200, and 18 of the 31 wrong no-turn items were right at step 100 on the Seen path.

**Q3. Away-hard and "back".** Training away-hard rows state a front forward relation on 5,681 of 6,693 (84.9%), so 84.9% of away-hard training answers are back quadrants; their toward twins share that 85%, and D toward-hard rows are 82.1% front. The twins inherit this prior. Their traces state front on 40 of 50 against 33 front truths (toward frame): front on all 33 front-truth items and on 7 of the 17 back-truth items; the half turn is then applied correctly, giving 40 back answers against 33 truths. R0-dev splits by the turn [R3]. The 47 turned traces state front on 41 and answer back on 41, exactly the 41 back truths among them; the 24 no-turn traces state front on 20 and, without the turn, answer back on only 5 against 20 back truths. R0's shortfall of 15 back answers (46 against 61) therefore comes entirely from the no-turn mode (5 against 20). The turned traces carry the same front prior as the twins, and R0's 86% back truths happen to reward it. Pooled over five hard sets, back-truth items (toward frame) are stated front on 44 of 103 and front-truth items stated back on 11 of 315 [R4].

**Q4. Medium "back".** On toward questions the trace writes "out to my left/right" for a back truth on 7 of 9 dev-S1 items and 11 of 17 R0-dev items ("behind me" on 2 and 6). The boundary error is therefore at 135 degrees, between the lateral band and the behind band. On away questions a back truth needs the forward band "ahead of me, slightly to my ..." (within 45 degrees). The traces state it on 21 of 39 (20 turn to "back", 1 skips the turn), "out to" on 16 (13 turn to a side, 3 skip the turn) and "behind" on 2. That boundary error sits at 45 degrees. The 135-degree rule is written in 0 of 344 step-200 medium traces and in 0 of 93,370 training rows; it lives only in the band words, which the trace applies correctly to its stated band on 344 of 344. Step 544 wrote the rule on 344 of 344 medium traces ("a turn of less than 135 degrees") and applied it consistently, but it stated 81 to 118 degrees on 7 of 9 dev-S1 and 8 of 17 R0 toward back truths, so the explicit rule did not help. Training underrepresents the behind band: it covers 927 of 21,003 toward medium rows (4.4%; the 734 D rows say "behind me" with no side), while back truths make up 6.0% of dev-S1 and 13.2% of R0 toward items.

**Q5. Why R0-dev toward is 15 to 20 points below dev-S1.** None of the four named explanations survives a control; a scene effect remains. Dataset: every R0 toward video is 60 fps, and the 60-fps dev-S1 source (prefix d2) scores 87.1% (203 of 233) against R0's 69.4% (261 of 376). Video length: in each of the three frame-spacing bins that hold 100 or more R0 items, R0 is 14 to 26 points lower. Vocabulary: with all three names in the training vocabulary R0 scores 69.1% (152 of 220), dev-S1 87.9% (350 of 398). Wording: the R0 template is the most-trained wording (20,344 D rows and all 43,469 Seen rows); dev-S1's 20 largest paraphrase openings score 70.0 to 100% (table 2.7). What remains: R0 accuracy clusters by room beyond chance (chi-square 130.8 on 96 df; the worst 19 rooms hold 47 of 115 errors), as dev-S1's does (98.5 on 42 df). The same gap existed at step 544 (67.3% against 88.2%), and the errors are stable across checkpoints (Q1). That R0's rooms differ in content (clutter, object types) is my guess, and I have not established whether dev-S1's rooms appear in training.

**Q6. Step 544 against step 200 on R0-dev toward items.** They disagree on 66 of 376 items; step 200 is right on 37 of them and step 544 on 29 [R5]. By level the split is easy 13 to 7, medium 13 to 8, hard 11 to 14. The angle form is not more often right near the boundaries. Step 544 never states an angle within 10 degrees of a boundary: its smallest is 15, and it uses 16, 17, 20, 21 or 27 degrees on 138 of 376 items. Within 10 to 19 degrees of a boundary (82 items), only 544 is right on 9 and only 200 on 7; farther out, 200 wins 30 to 20.

**Q7. For vehicle N** (section 3): (a) add away twins to the D family so the clause, not the opening, decides the turn (about 12,000 rows; 5.4 category points at stake, +1.7 to +3.4 expected); (b) lower the front prior in hard rows and raise the behind band in medium rows, as pairs (about 8,000 rows; ceilings 7.2 R0 and 4.4 dev-S1 category points); (c) spend no rows on rewording toward relation sentences or frame citations, because those errors are stable across trace forms.

## 2. Evidence

### 2.1 The turn follows the opening (R0-dev away, step 200)
| Level | D opening: no-turn clause | wrong | Seen opening: half turn | wrong |
|---|---|---|---|---|
| Easy | 14 of 14 (of 66 items) | 5 | 52 of 52 | 8 |
| Medium | 5 of 5 (of 65) | 5 | 60 of 60 | 22 |
| Hard | 24 of 24 (of 71) | 21 | 47 of 47 | 14 |

Traces that open with D skip the turn (verbatim):
- `05d90f7d...`, easy. Q: "If I am standing by the book and facing away from the headphones, is the basket to my left or to my right?" Truth left, answer right. "Step 2: I stand at the book facing the headphones; I find the basket to my right. / The question has me face away from the headphones, so I keep that heading. / So I find the basket to my right."
- `12396a66...`, medium. Q: "...by the soap dispenser and facing away from the soap, is the door to my left, right, or back?" Truth left, answer right. "I find the door out to my right. / The question has me face away from the soap, so I keep that heading."
- `10bbc380...`, hard. Q: "...by the sink and facing away from the door, is the toilet brush to my front-left, ...?" Truth front-left, answer back-right. "I find the toilet brush behind me, on my right. / The question has me face away from the door, so I keep that heading."

Traces that open with Seen turn, even with unfamiliar names: `0bb9ba85...` (papers, toaster, postcard; right): "If I stood at the papers facing the toaster, the postcard would be to my left. / ... That is a half turn ... / So I find the position of the postcard to my right." `1e7c6841...` (router, bedframe, rice cooker; right): "...would be in front of me, on my left. / ... half turn ... / So I find the rice cooker at my back-right." `34d79352...` (medium, wrong forward band but turned): "...the window lintel would be out to my right. / ... half turn ... / So I find the window lintel to my left."

### 2.2 Training census (all 93,370 direction rows, store v7, all kept)
| Family group | Rows E / M / H | Opening | Away clause | Away turn | Object names | Hard forward front | Medium behind band |
|---|---|---|---|---|---|---|---|
| W `w1g\|rows_rebuild_d0_v1` (skeleton D) | 12,969 / 15,547 / 21,385 | "Step 1: find/locate" | 0 of 49,901 | none | 1,089 (R0-template questions only) | 17,558 of 21,385 (82.1%) | 734 of 15,547, no side |
| G four `rows_rebuild_d0_*` pools (T/A) | 15,024 / 10,912 / 9,022 | "Seen:" | 17,479 (half of each pool) | half turn on all | 73 (G and O) | 3,838 of 4,511 away (85.1%), same in toward twins | 386 of 10,912 |
| O `r1_away_opp` | 3,664 / 2,665 / 2,182 | "Seen:" | all ("opposite direction of") | half turn on all | (in the 73) | 1,843 of 2,182 (84.5%) | 92 of 2,665 |

Every Seen row cites frames 1 to 32 (0 of 43,469 cite a frame above 32), no row writes "in question", and no D row cites a frame. In every family, the final line equals the answer, and so does the relation implied by the stated forward line and turn. Verbatim rows: `i=6` (W easy, toward) "Step 1: find the bottle and the bucket, then the stair. / Step 2: I stand at the bottle facing the bucket; I find the stair to my right. / The question has me face the bucket, so no turn applies." `i=0` (W hard) "...The question has me facing the file cabinet; I keep that heading. / So I find the position of the books at my back-left." `i=106568/106569` (G medium pair, `vsi590k_122144` and `_away`): "Standing at the printer facing the door, I find the laptop behind me, on my right. / The question has me facing the door; I keep that heading." against "If I stood at the printer facing the door, the laptop would be behind me, on my right. / The question has me face away from the door. That is a half turn: ..."

What selects the opening on R0-dev at step 200 (number of names among the 73 Seen-row names):
| Familiar names | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| Away items opened with D | 20 of 53 | 18 of 90 | 5 of 50 | 0 of 9 |
| Toward items opened with D | 109 of 115 | 156 of 166 | 58 of 80 | 8 of 15 |

The twins use only familiar names, and their away items open with Seen on 150 of 150. dev-S1 uses paraphrased questions that only D rows carry, and it opens with D on 450 of 450.

### 2.3 Consistency
| Source | Linked units | Consistent, right | Consistent, wrong | Inconsistent |
|---|---|---|---|---|
| R0-dev exact repeated triples | 2 triples | 2 | 0 | 0 |
| R0-dev observer-shared role swaps | 6 pairs | 4 (2 lose an answer to the omitted turn) | 2 | 0 |
| Facing twins (toward/away of one triple) | 150 pairs | 132 | 12 | 6 |
| dev-S1 repeated triples (roles from the trace) | 46 triples | 40 | 4 | 2 |
| Same R0 item, step 100 against step 200 | 115 wrong toward items | n/a | 70 same wrong relation | 45 changed |

Consistently wrong (verbatim): twin `vsi590k_093926`, away Q "If I am standing by the trash can and facing away from the telephone, is the keyboard to my front-left, ...?" (truth front-right, answer back-right): "If I stood at the trash can facing the telephone, the keyboard would be in front of me, on my left." Its toward twin (truth back-left, answer front-left): "I find the keyboard in front of me, on my left." Twin `vsi590k_107565`, away Q "...by the ceiling lamp and facing in the opposite direction of the bookshelf, is the heater ...?" (truth front-right, answer back-right): both twins write "the heater ... in front of me, on my left". R0 pair `92ea4361...`, Q "If I am standing by the box and facing the books, is the table to the left or the right of the books?" (truth left, answer right): "I stand at the box facing the books; I find the table to my right." Its partner `ddeb23b9...`, Q "...by the box and facing the table, is the books to the left or the right of the table?" (truth right, answer left): "I stand at the box facing the table; I find the books to my left." The pair is mirrored consistently, and both items are wrong.

### 2.4 Away-hard use of back (step 200)
| Set | Items | Stated forward front | Back answers | Back truths | Right |
|---|---|---|---|---|---|
| Twins, away-hard | 50 | 40 | 40 | 33 | 41 |
| R0-dev away-hard, turned | 47 | 41 | 41 | 41 | 33 |
| R0-dev away-hard, no-turn clause | 24 | 20 | 5 | 20 | 3 |
| Training away-hard rows | 6,693 | 5,681 | 5,681 | (labels) | n/a |

The front prior in verbatim (truth back in the toward frame, stated front): R0 `7836060b...`, Q "If I am standing by the first aid kit and facing the humidifier, is the sink to my front-left, ...?" (truth back-right, answer front-left): "I find the sink in front of me, on my left." R0 `8f5bd97e...`, Q "...by the bean bag and facing the coax outlets, is the trash can ...?" (truth back-left, answer front-left): "I find the trash can in front of me, on my left." R0 `b999da56...`, Q "...by the backpack and facing the books, is the bucket ...?" (truth back-right, answer front-right): "I find the bucket in front of me, on my right." Twin `vsi590k_010414`, Q "...by the towel and facing away from the window, is the washing machine ...?" (truth front-right, answer back-right): "the washing machine would be in front of me, on my left." The prior also appears on toward sets. R0 toward-hard back truths are stated front on 15 of 23 (front truths stated back on 6 of 98), and dev-S1 hard back truths on 13 of 40 (front truths stated back on 2 of 110).

### 2.5 Medium back truths: the band the trace states (step 200)
| Set | Back truths | Answered back | "out to" | "behind me" | "ahead, slightly" |
|---|---|---|---|---|---|
| dev-S1 (toward) | 9 | 2 | 7 | 2 | 0 |
| R0-dev toward | 17 | 6 | 11 | 6 | 0 |
| R0-dev away (right band is "ahead") | 39 | 20 | 16 | 2 | 21 (1 not turned) |

Verbatim: dev-S1 `vsi590k_126954`, Q "Standing alongside the shoes and facing the ceiling light, does the table lamp lie to my left, right, or behind?" (truth back, answer left): "I find the table lamp out to my left." dev-S1 `vsi590k_126980`, Q "Standing alongside the cup and facing the bed, does the table lamp lie to my left, right, or behind?" (truth back, answer right): "I find the table lamp out to my right." dev-S1 `vsi590k_127822`, Q "I'm positioned at the headphones, looking toward the plant; is the computer mouse placed to my left, right, or behind me?" (truth back, answer left): "I find the computer mouse out to my left." R0 `03a29ec1...`, Q "...by the smoke detector and facing the table, is the bookshelf to my left, right, or back?" (truth back, answer left): "I find the bookshelf out to my left." R0 away `e3a540cf...`, Q "...by the bookshelf and facing away from the door frame, is the blinds ...?" (truth back, answer left): "If I stood at the bookshelf facing the door frame, the blinds would be out to my right" (the right band is "ahead"). Step 544 on R0 back truths: `03a29ec1...` "lies 81 degrees left of straight ahead, a turn of less than 135 degrees"; `d3f57b7f...` "91 degrees right ..."; `c1088cd5...` "117 degrees right ..., a turn of less than 135 degrees". In the other direction, side truths are stated "behind" on 1 dev-S1 item and 4 R0 toward items.

### 2.6 544 against 200 by the distance of 544's stated angle to the nearest boundary of its level (R0 toward)
| Distance | Items | 544 right | 200 right | Only 544 right | Only 200 right |
|---|---|---|---|---|---|
| under 10 degrees | 0 | n/a | n/a | n/a | n/a |
| 10 to 19 | 82 | 39 | 37 | 9 | 7 |
| 20 to 29 | 123 | 83 | 89 | 13 | 19 |
| 30 or more | 171 | 131 | 135 | 7 | 11 |

### 2.7 Toward gap controls (step 200 accuracy)
| Control | R0-dev toward | dev-S1 |
|---|---|---|
| All items | 261 of 376 (69.4%) | 396 of 450 (88.0%) |
| Source by fps (R0 is 60 fps) | 60 fps: 69.4% | d1 24 fps 93.2% (88); d2 60 fps 87.1% (233); d3 10 fps 86.0% (129) |
| Frame spacing 2-4 / 4-6 / 6-10 s | 67.2 (131) / 75.8 (124) / 64.0 (100) | 92.8 (138) / 90.1 (91) / 84.0 (150) |
| All three names in the training vocabulary | 69.1% (220) | 87.9% (398) |
| Opening | D 67.4% (331); Seen 84.4% (45) | D 88.0% (450) |
| Step 544, all items | 67.3% | 88.2% |

The largest dev-S1 paraphrase openings score: "Standing next to the X and" 100% (22 items); "If I'm at the X, looking" 92.9% (14); "If located at the X and" 72.7% (11); "I'm positioned at the X, looking" 70.0% (10); "While standing at the X and" 80.0% (10); the remaining 304 items 87.5%. Across the 20 openings with 8 or more items, the chi-square against the pooled rate is 38.8 on 19 df. Seen traces on R0 cite a frame above 32 on 174 of 200, which no training row does, and are right on 135 of those 174. Their accuracy advantage is therefore not evidence of grounding.

## 3. For vehicle N (ranked)

**N1. Give the D skeleton away twins, so the clause decides the turn.** Add rows to `object_rel_direction_{easy,medium,hard}|w1g|rows_rebuild_d0_v1`, about 12,000 (E 3,200, M 3,700, H 5,300; the size is a guess), each the away twin of an existing D row. A twin keeps the Step 1 line, words Step 2 as a condition, writes the half turn, and concludes the turned relation. Easy and hard labels are exact half turns, and the 0, 90 and 180 degree margins map onto themselves. Medium labels come from the stated band (ahead becomes back; out to or behind on one side becomes the other side); skip the 734 "behind me" rows that carry no side, or recompute the side from geometry. Give the toward D rows the single clause line "The question has me face F, so no turn applies." Verbatim skeletons (toward rows are store rows with the canonical clause line; away rows are proposed):
```
E toward (i=6): If I am standing by the bottle and facing the bucket, is the stair to the left or the right of the bucket? (A. right, B. left)
<think>Step 1: find the bottle and the bucket, then the stair. / Step 2: I stand at the bottle facing the bucket; I find the stair to my right. / The question has me face the bucket, so no turn applies. / So I find the stair to my right.</think> A
E away: If I am standing by the bottle and facing away from the bucket, is the stair to my left or to my right? (A. right, B. left)
<think>Step 1: find the bottle and the bucket, then the stair. / Step 2: if I stood at the bottle facing the bucket, I would find the stair to my right. / The question has me face away from the bucket. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap. / So I find the stair to my left.</think> B
M toward (i=43): If I am standing by the closet doors and facing the sink, is the door to my left, right, or back? An object is to my back if ... (A. right, B. left, C. back)
<think>Step 1: find the closet doors, the sink and the door. / Step 2: I stand at the closet doors facing the sink; I find the door ahead of me, slightly to my right. / The question has me face the sink, so no turn applies. / So I find the door to my right.</think> A
M away: ...by the closet doors and facing away from the sink, is the door to my left, right, or back? ... (same options)
<think>Step 1: find the closet doors, the sink and the door. / Step 2: if I stood at the closet doors facing the sink, I would find the door ahead of me, slightly to my right. / The question has me face away from the sink. That is a half turn: ... / So I find the door at my back.</think> C
H toward (i=0): If I am standing by the backpack and facing the file cabinet, is the books to my front-left, ...? (A. back-left, B. front-right, C. back-right, D. front-left)
<think>Step 1: find the backpack, the file cabinet and the books. / Step 2: facing the file cabinet from the backpack, I find the books behind me, on my left. / The question has me face the file cabinet, so no turn applies. / So I find the position of the books at my back-left.</think> A
H away: ...by the backpack and facing away from the file cabinet, is the books to my front-left, ...? (same options)
<think>Step 1: find the backpack, the file cabinet and the books. / Step 2: if I stood at the backpack facing the file cabinet, I would find the books behind me, on my left. / The question has me face away from the file cabinet. That is a half turn: ... / So I find the position of the books at my front-right.</think> B
```
These rows address the 43 R0-dev away items that open with D (31 wrong; ids in `work/ITEM_LISTS.json`), and they protect the 159 Seen-opened ones. dev-S1 has no away items. At stake: 5 easy, 5 medium and 21 hard items, or 5.37 category points. Expected gain (estimates): +1.73 points if these traces keep their forward lines and only add the turn (easy loses 4 items, medium gains 2, hard 12, because 9 of the 14 easy traces are right only by skipping it). The gain is +1.91 points if they behave as at step 100 (23 of 43 right against 12), and +3.44 points if they match the Seen-opened away accuracy at their level. A supporting builder change (N1b): widen the Seen pools' object names beyond 73, so that the opening stops encoding name familiarity. Failure shows at the next read as more than about 10 of 202 R0 away traces pairing "face away from" with "keep that heading" or "no turn applies" (now 43). Failure also shows as any toward trace writing a half turn (now 0 of 376).

**N2. Lower the front prior and raise the behind band, always as toward/away pairs.** In hard rows, raise the share of back forward relations from 15 to 18% to about 30%. The W-hard back rows (3,827) supply D away twins with front answers through N1, and the G pools add about 2,000 back-forward toward/away pairs (4,000 rows; a guess). In medium rows, add about 2,000 "behind me, on my <side>" toward rows with their 2,000 away twins, raising the behind band from 4.4% to about 12%. The verbatim pattern is the G pair `i=106568/106569` above (toward: "behind me, on my right" gives back; away: half turn gives left). Items addressed: back truths stated front, 15 R0 toward-hard, 3 R0 away-hard and 13 dev-S1 hard. Also back truths stated "out to": 7 dev-S1, 11 R0 toward and 13 R0 away (turned). Ceilings are 7.2 R0 category points (3.1 hard, 4.1 medium) and 4.4 dev-S1 points. I expect about a third of those (a guess), because the prior is one-directional (44 of 103 against 11 of 315) and matches the training share. A risk: R0 away-hard truths are 86% back, so a weaker prior can cost the 33 right turned items. Failure shows as back truths stated front staying above about 30 of 103, or front truths stated back rising above about 25 of 315 (the prior merely flips). Medium failure shows as back truths stated "out to" staying at 7 of 9 and 11 of 17, or side truths stated "behind" rising above about 10 (now 5).

**N3. Do not reword the toward relation sentence or add frame citations to buy accuracy.** The toward errors are stable across trace forms: 69 of 115 are wrong at steps 544, 100 and 200. Seen traces on R0 cite out-of-range frames yet score no worse, and the angle form was no better near boundaries. Those 115 items are worth 19.9 R0 category points, partly overlapping N2. My reading of consistency suggests perception limits them, so the levers are the gated hard-direction program read (O3) on R0-dev and more training scenes like R0's (60-fps rooms with uncommon objects, from legal sources). Both are hypotheses. A wording change would show its failure as unchanged consistent-wrong counts at the next read.

## 4. Refuted or corrected
- The no-turn count is 43 of 202 by clause and 42 by behavior. The facing report's "42 of 202" and dir_hard's "23 of 71" count behavior and leave out `9a6a1be6...`, which says "keep that heading but flip forward to backward ... left and right swap" and turns correctly.
- rows_a: blindly applying the turn breaks 11 of the 12 currently correct D-away items, not 12; the twelfth already turns.
- rows_a, facing and dir_hard attribute the omitted turn to the toward template's "keep that heading" clause. The counts narrow it. The 17,479 Seen toward rows end their clause line with the same tails ("I keep that heading" or "no turn applies"), yet Seen-opened away traces never skip the turn (0 of 159). The failure belongs to the D skeleton, which has never seen an away clause, and the opening tracks object familiarity.
- dir_easy change 1, dir_med change 2 and dir_hard change 2 (reword W rows with verified frame and instance evidence to cut toward errors) are not supported, for the reasons in N3.
- dir_med's "toward back-band error" merges two opposite errors: back truths stated "out to" (dev-S1 7, R0 11) and side truths stated "behind" (dev-S1 1, R0 4). They need opposite corrections.
- dir_hard's "why R0-dev is harder remains partly unresolved" narrows to scene content: fps, frame spacing, vocabulary and wording are each controlled in 2.7.

## 5. Not established
- Whether the 69 items wrong at all three checkpoints are perception errors or label errors. Recomputing their labels from source geometry and viewing their frames would settle it.
- Whether name familiarity causes the D opening (the evidence is correlational). A forced-prefix read would settle it: prefill "Seen:" against "Step 1:" on the 202 R0 away items (about 400 generations), plus a name-swap read (for example "power sockets" to "power strip").
- Why medium away items rarely open with D (5 of 65, against 14 of 66 easy and 24 of 71 hard). The D rows' share of R0-template rows (24.7% E, 25.5% M, 46.1% H) explains hard but not easy against medium.
- Whether dev-S1's rooms are training videos. A (fps, total frames) signature matches 6 of 43 dev-S1 rooms, below the 9.5 expected from near-miss shifts, so the test is inconclusive. Matching frame sha256 against the k6tk frame map would settle it. That fps marks the capture source is a guess.
- The size of every effect in section 3; only a controlled continuation with matched row budgets can measure them.

Files: `work/dirparse.py` (parser), `work/census.py` with `census_agg.json` (all-row census), `work/vocab.py` with `vocab_by_group.json`, `work/roomsig.py`, `work/ITEM_LISTS.json` (item ids per mode), `work/reproduce.py`.
