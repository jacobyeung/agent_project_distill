VERDICT: GO AFTER FIXES

Review of /scratch/jjyeung/orch_n30/lever10/work/PRICING_C2_C3.md (cited as P:<line>). Reviewer: fresh, trinity-2-28, 2026-11-22. Read-only; no Git, SSH or GPU.
Source keys: DR = distill_design/MASK_SOURCE_AFTER_TRACKER_DESIGN_20261122.md; MQ = distill_design/MASK_QUALITY_DESIGN_20261119.md; OH = distill_design/OWN_GROUNDING_HEAD_K1_20261116.md; SPEC = sb_maskdesign/KIT_SPEC_mask_sam3ft_v2.md; RES = lever/20261122T1214Z_RESULT_...md; RJ = lever8/j1/REPORT_J1.md; kit files are under lever8/j1/kit/.
All J1 numbers quoted in P (h1, h0, k, e - a, ARKit k, 1,098, 0.32/0.61, 52/61/37/24/6, 1,064 box prompt-frames, 339 s, 46 captures/35 rooms) match RES:5-13, RELIFT_J1.md:8-36 and DR:117-119. The findings below list the mismatches.

1. BLOCKING. Training set includes withheld rooms (criterion 3).
   Text: "The 239 captures of sb_kbox4/pinned_train.json (ARKit 127, ScanNet++ 71, ScanNet 41)" (P:37); "trained on all 239 captures under the same exclusions" (P:41); "with the model trained on all 239 captures" (P:49); "7,648 training anchors" (P:43).
   Evidence: six K1 training captures sit in five of the 80 withheld rooms (MQ:79); the eligible K1 train set is 233 captures, with 11 K1 captures in withheld rooms excluded (OH:11). Training on all 239 breaks the room exclusion P:38 itself registers. Otherwise the sb_auditfix2 check stops the kit (SPEC:60), after the build hours are spent.
   Fix: train on the 233 captures outside the 80 withheld rooms (7,456 anchors). Recount the per-dataset numbers from the audit output and write the count into the bars file.

2. BLOCKING. The J1-T decision rule is incoherent and incomplete (criterion 4).
   Text: "Candidate 3's pilot bar rises to the smallest tested IoU whose arm clears 8; if only kB(0.9) clears, or none does, candidate 3 returns" (P:29); "If J1-T shows that no box with IoU of 0.7 or less ... clears the source bar ... returns to the orchestrator ... before any head is trained" (P:12); "Anything else: undecided. Candidate 3's pilot runs" (P:30).
   Problems:
   (a) In the closes branch, 0.9 is the only tested IoU above 0.7, so "rises to the smallest tested IoU" can never set a new bar. The branch always means "return". The rule also never defines "clears 8": a mean >= 8, or the full source bar?
   (b) P:12 conflicts with P:30. When kB(0.7) and kB(0.5) both read undecided, no box at IoU 0.7 or less clears the source bar, so P:12 returns before training, but P:30 trains the pilot (1 to 4 A6000-h).
   (c) The deciding arm is kB(0.7), but the pilot bar it guards is IoU 0.5 for half the objects at their largest anchor (P:26, P:40; DR:62). If kB(0.7) is a source and kB(0.5) is not, a head that passes at 0.5 has no support. The rule does not cover this case.
   Fix: write one table over the verdicts of kB(0.5) and kB(0.7) (source / undecided / closes), with an action in every cell, and use "source bar" in place of "clears 8". Pick the deciding arm that matches the pilot's IoU bar (or raise the pilot bar to 0.7 when only kB(0.7) is a source). Make P:12 match the table.

3. BLOCKING. A training choice is made from dev-S1 (criterion 3).
   Text: "kP-miss and kP-fp do not decide. They say which presence errors the head's loss must weight more." (P:31)
   Evidence: P:3 and the exclusion rule (SPEC:59: "No arm, phrase, threshold or stop is chosen from ... dev-S1") forbid this. kP-miss and kP-fp are read on the 117 dev-S1 items.
   Fix: fix the head's loss weights now, for example unweighted BCE, or a positive weight set from the K1 train presence balance and written into the bars file. Report the kP arms as diagnostics that change no training choice.

4. SHOULD-FIX. J1-T as registered mostly cannot answer its own question (criteria 4 and 7).
   Text: "J1-T measures how far the score falls as the box loosens ... That curve turns candidate 3's pilot bar into a number ... It also says whether any learned box can clear +8." (P:9)
   Evidence: k - a is +11.0 [+0.7, +20.9] (RES:7), a half-width of about 10. For kB(0.7) - a to be a source, it must keep nearly all of k (a mean of roughly 10 or more). To close, its upper bound must fall below 8, which needs a mean of roughly -2. Most plausible outcomes therefore read undecided, and J1-T then changes nothing (P:30). The arms are "paired ... with k" (P:21), but no kB - k contrast is read.
   Fix: register kB(t) - k and kP - k, paired, with a room-bootstrap interval, as the tolerance read. These contrasts are much tighter, because only the box differs. Tell the orchestrator in P that kB - a will most likely read undecided.

5. SHOULD-FIX. The pilot bar is taken from the 117 items, and OWN is then read on the same 117 (criteria 2 and 3).
   Text: "turns candidate 3's pilot bar into a number taken from the 117 items" (P:9); "If J1-T moved the box bar, the moved bar replaces IoU 0.5" (P:40).
   Evidence: P:3 says no bar changes after a score is read. Here a threshold follows a dev-S1 read.
   Fix: state that the mapping is a function fixed now, over the grid {0.5, 0.7, 0.9}, and that it can only raise the bar. Better: keep the pilot bar at IoU 0.5 and let J1-T gate only the full run.

6. SHOULD-FIX. The parity stop is brittle, and the CPU fallback cannot pass it.
   Text: "k itself, recomputed, must equal J1's k on 117 of 117 items" (P:25); "the same job runs on 2-28's CPU" (P:32).
   Evidence: J1's own gates allow bf16 noise (mask IoU >= 0.95 on >= 95% of operand-frames; select_j1.py:20-28, RJ:16-22). CPU fp32 against bf16 matched only 50/64 operand-frames under the strict rule (RJ:19). The J1-T run may also land on a different card from J1's card 0.
   Fix: require mask IoU >= 0.95 between recomputed k and J1's k on >= 95% of the 1,064 k anchors, and require |(k' - a) - (k - a)| <= 0.5. Report exact item equality beside the gate. Drop the CPU fallback, or give it its own parity rule.

7. SHOULD-FIX. The build path is misdescribed and the build is underestimated (criterion 4).
   Text: "an extension of the sealed J1 kit (kit/select_j1.py, kit/detect.py) ... computes boxes from J1's stored GT grids ... relifts each arm with relift_j1.py" (P:20); "Opus high, about 1 h" (P:59).
   Evidence: the box path exists (detect.py:122-149, box_detect), and so do the relift and its gates. However:
   - Boxes are built on 2-28 from the GT npz files by prompts_j1.py (prompts_j1.py:6, 29-47), not by select_j1.py or detect.py.
   - relift_j1.py hard-codes ARMS = ('h1', 'h0', 'k') (relift_j1.py:41).
   - Its Store rejects any k unit whose anchor slots differ from the GT anchors (relift_j1.py:127-129) or whose prompts differ from PROMPTS_J1 (relift_j1.py:110-113). So kP-miss (fewer slots) and kP-fp (non-GT slots) need a new store and arm wiring.
   - kP-fp also needs h1's picks from out/detect.
   - The existing relift test alone takes 1,259 s (RJ:50).
   Fix: list prompts_j1.py, relift_j1.py and the tests as changed files, and name a new PROMPTS file shipped to 0-13 over .ib. Budget 2 to 3 h for the build.

8. SHOULD-FIX. The box-perturbation sampler is not registered.
   Text: "each GT box is moved and rescaled at random until its IoU with the true box equals the target (within 0.02)" (P:22).
   Evidence: kB depends on the unregistered mix of shift and scale, of growing and shrinking, on clipping at the frame edge, and on taking one draw per anchor. The plan itself says real errors are biased (P:75).
   Fix: register the sampler exactly before the seal: the distributions, a magnitude solved by bisection, clipping to [0, 1], a redraw cap, and a count of anchors where the target IoU is unreachable. Consider a second seed.

9. SHOULD-FIX. "Recall binds" is stated as a J1 finding, but the source says J1 cannot tell.
   Text: "Recall binds candidate 2" (P:15); "J1 says recall binds" (P:48); "h0 closes, so recall binds" (P:72).
   Evidence: DR:120 and RES:18 say "J1 cannot say whether pool coverage or picking binds a fine-tune". h0 abstains below IoU 0.5, and 24 of the 61 empty cases have a proposal at IoU 0.1-0.5 (DR:119).
   Fix: write "The table row (DR:87) orders the full adapter; J1 does not separate recall from picking." Delete "One change to that spec", since P:48 changes nothing.

10. SHOULD-FIX. The candidate 2 read on the 117 skips the spec's K1 verdict (criteria 5 and 6).
    Text: "Two added arms on the 117, after ft_failfast passes, with the model trained on all 239 captures" (P:49); "3.0 more for the final fit" (P:53).
    Evidence: the spec runs the final fit only after ft_worth, ft_object and ft_safe pass, with its own GO (SPEC:41). P registers no rule for the case where the K1 bars and the 117 read disagree.
    Fix: no room in the 117 is in either fold, so read FT-h1 and FT-h0 with fold model A, fixed now. This defers the final fit and its 3.0 A6000-h. Also register the rule for a K1/117 disagreement.

11. SHOULD-FIX. The FT and OWN arms on the 117 have no parity stop, and FT's prompt text is unset.
    Text: "relifted inside dump 174135 ... the relift kit already runs it" (P:50); OWN arm (P:41).
    Evidence: relift_j1 reads h1 and h0 only when J1's pool matches dump 174135's pool (RJ:17, 22; relift_j1.py:44-52). A fine-tuned pool cannot pass that gate. J1 prompted "heater", not "radiator" (RJ:5).
    Fix: in the same pass, (a) run the frozen detector with the adapter off and require pick_match agreement with J1's h1 on >= 95% of operand-frames, and (b) recompute k under the rule of finding 6. Replace the dump-pool gate with these two checks. Use J1's prompts (the ground-call name), so that FT-h1 - h1 isolates the adapter.

12. SHOULD-FIX. Candidate 3 departs from registered bars and from the order in the design records (criterion 6).
    Text: "that contrast is reported ... and does not override the source bar" (P:42); "Candidate 3 goes first" (P:10).
    Evidence:
    - DR:62 says OWN "must beat candidate 2's arm".
    - MQ:48 registers a K1 ladder bar for the own head (own-box arm minus A0 >= +3.0, lower bound > 0, two folds) and places it after the fine-tune. P keeps candidate 2's K1 bars and drops candidate 3's, so the two are not comparable on K1.
    - The J1-outcome table row reads "full candidate 2; candidate 3 if it misses" (DR:87).
    Ruling 0438Z item 5 supports pricing candidate 3 but changes no bar.
    Fix: list these three departures under one heading for an explicit orchestrator ruling. Otherwise keep "OWN beats FT" as a bar and add the K1 ladder bar for OWN.

13. SHOULD-FIX. The cost figure of 30 to 60 A6000-h is misapplied (criterion 7).
    Text: "30 to 60 A6000-hours by the 2026-11-19 estimate" (P:43; also P:12, P:69).
    Evidence: MQ:48 prices that full run on the raster stores outside K1 (2,897 scenes, manifests MISSING). P's full fit uses K1 train only, so its cost is unknown and probably near the pilot's scale. The inflated figure overstates the value of J1-T (P:69).
    Fix: price the full fit from the timing receipt and the step count on 233 captures. Attach the 30 to 60 figure only to the expanded data, which stay blocked.

14. SHOULD-FIX. The rule for OWN's presence threshold is not registered.
    Text: "The threshold is fixed on K1 training folds before the read" (P:41).
    Evidence: no selection criterion is given. A threshold fitted on fold models also miscalibrates a model trained on all captures.
    Fix: register the rule, for example the held-out-fold threshold at which frame precision equals a's 0.609 (RELIFT_J1.md:20), or the one that maximizes F1. Read the 117 with the same fold model, as in finding 10.

15. NIT. The own mask-decoder history is misquoted.
    Text: "it failed (matched-POS IoU 0.06-0.12)" (P:36; also P:70).
    Evidence: pilot 1 read 0.062, 0.012 and 0.091 (OH:58). Pilot 2 read 0.119 at update 200 and was killed by vnice, so it is inconclusive (OH:79-81). The CPU diagnosis read 0.24 (OH:89). DR:29 gives 0.09-0.24.
    Fix: write "pilot 1 failed its fail-fast (IoU <= 0.09); pilot 2 was killed at update ~399 (0.12 at update 200)".

16. NIT. The J1-T timing is wrong.
    Text: "the 46 encodes take about 7 minutes, as in J1" and "5 arms" (P:32).
    Evidence: J1's out/detect/EVENTS.jsonl sums to 92 s of encodes, 242 s of text prompts and 47.5 s for 1,064 boxes; 7 minutes was the whole run. J1-T has 6 arms (three kB, two kP, k), and kP-fp adds h1's false-presence anchors.
    Evidence for the CPU fallback: "about 4.5 hours" omits the box decodes at about 1 s each on CPU (RJ:65), roughly 2 h more for about 6,500 boxes.
    Fix: the GPU total of about 10 min stands; correct the breakdown and the CPU figure.

17. NIT. An inference is presented as a finding.
    Text: "h1's failure is mostly presence" (P:16).
    Evidence: the sources give counts only (RES:12). h1's precision of 0.323 also counts wrong-instance masks on GT-present anchors (RELIFT_J1.md:28).
    Fix: label the sentence as an inference.

18. NIT. Builder count, sunk build hours and the cost table.
    Text: "At most two builders run at once" (P:63).
    Evidence: the table starts the J1-T build and the candidate 3 build together (P:59-60). The candidate 2 build waits only for GO (P:61). That makes three builders at once.
    The candidate 3 build (4 to 6 h) starts before J1-T is read, so a J1-T "return" leaves those hours spent. State the trade.
    "1.2 to 7.0 A6000-h" mixes the fail-fast with the cap.
    Fix: sequence the builds, and split the GPU column into fail-fast and cap.

19. NIT. The inherited code may be gone.
    Text: b05_owngrd code on trinity-3-30 /scratch (P:36).
    Evidence: that code dates from 2026-11-16 (OH:22), and /scratch's 7-day cleaner drops untouched files.
    Fix: the builder confirms the code is present, or uses the 1-18 mirror (OH:67, 86), and checks that the mirror holds the tap extraction.

Counts: 3 blocking (1, 2, 3), 11 should-fix (4-14), 5 nit (15-19).
