"""card_fix2: build the revised record from RECORD_before_card_fix2.md (sha256 16ed4a71...) and blocks/."""
import hashlib, sys
src=open('RECORD_before_card_fix2.md').read()
assert hashlib.sha256(src.encode()).hexdigest().startswith('16ed4a7107d1fc1b'), 'record changed'
L=src.split('\n'); assert L[-1]=='' and len(L)==299
B=lambda n: open('blocks/'+n).read().rstrip('\n').split('\n')
def rng(a,b,new):            # replace 1-based lines a..b inclusive
    L[a-1:b]=new
assert L[296].startswith('## Status') and L[273].startswith('## What might not work') and L[208].startswith('## 5.') and L[65].startswith('### 2.2')
rng(297,298,B('status.md'))
rng(274,285,B('risks.md')+[''])
rng(209,257,B('s5.md')+[''])
rng(66,103,B('s22.md')+[''])
T='\n'.join(L)
def sub(a,b):
    global T
    assert T.count(a)==1,(T.count(a),a[:70]); T=T.replace(a,b)
def line(prefix,new):
    global T
    ls=T.split('\n'); idx=[i for i,x in enumerate(ls) if x.startswith(prefix)]
    assert len(idx)==1,(len(idx),prefix); ls[idx[0]]=new; T='\n'.join(ls)
def after(prefix,new):
    global T
    ls=T.split('\n'); idx=[i for i,x in enumerate(ls) if x.startswith(prefix)]
    assert len(idx)==1,(len(idx),prefix); ls.insert(idx[0]+1,new); T='\n'.join(ls)
# header
sub("Lanes next_leg and card_fix (Devin, trinity-1-3), design only","Lanes next_leg, card_fix and card_fix2 (Devin, trinity-1-3), design only")
sub("`CF` = trinity-1-3 `/scratch/jjyeung/orch_n30/card_fix`,","`CF` = trinity-1-3 `/scratch/jjyeung/orch_n30/card_fix`, `CF2` = trinity-1-3 `/scratch/jjyeung/orch_n30/card_fix2`,")
# answer
line("2. **Leg R1 takes the four H100","2. **Leg R1 takes the four H100: step 544 plus the repair rows, GT-valued responses, S2 off, 1,000 steps.** Rows: model-written unit conversion (required from launch), recovery after a failed ground (from the boundary at which vehicle N takes over), room rows with a qualitative trace, the six VSTI relative types, facing twins that include ReVSI's away wording, and the verified first-seen repairs (store v7). No object-size row, no GF-1, no own-valued rows, no H1-1 continuation, no H1-2. A harm rule on the seven direct types can stop the leg at steps 200, 400, 600 and 800; object size, toward-facing accuracy, relative size and the capped distance reads of the claimed arm are protected outcomes; each family has an entry boundary and an efficacy gate 200 steps after it; and the leg stops at step 400, at about 83 H100-hours, unless the VSTI and facing gates have passed (2.2). Step 200 costs about 48 H100-hours with its reads (2.4). The effects are upside scenarios with no predictive interval: VSTI primary +0 to +8.9, ReVSI +0 to +5.1 from facing and +0 to +5.6 from room, VSI-Bench +0 to +1.5; object size has no repair in this leg and may drift.")
line("3. **Two vehicles are built in parallel","3. **The leg launches on vehicle P and stays on it; vehicle N takes over only at a boundary where its continuation proof has passed.** Vehicle P is the deployment that runs H1-1 today (Orchard 170710), with the VQA store swapped and own-valued rows off. Vehicle N is the new tree at build 9, which has never run on Orchard and carries 15 named blockers (7 bind a launch without GF-1, by my reading of their names) and 14 missing evidence records. P's sealed tree admits every row of store v6, refuses all 1,532 recovery rows, and admits a unit row only when its answer equals the label at two decimals, so P binds the faithful slice of the 10,945 unit rows that already does: 1,224 rows, feet almost alone (`RP/REPORT.md`; slot UNIT-P, section 5). Recovery rows are not a requirement of the leg: with the best-candidate selector about 4.7% of reads draw `not seen`, and the requirement is that the claimed arm keeps capped distance reads at or below 5 of 150. Five gates hold the launch: the production proof with the loader audit on the final config identity, five bound rows per family read by the orchestrator and shown to the user, slot SIZE-V decided, card v3 registered, and main's release of the slot (3.3, item 9).")
line("5. **The production proof of R1 goes first","5. **The production proof of R1 goes first,** on advanced beside main's jobs or else in the Orchard job place ahead of every read except the two H1-1 m100 reads, and it carries the loader audit (3.3). Step 544's baseline reads, the tower-arm read first, are registered before R1's first export is read (2.2, item 4d).")
# 2.4
sub("Step 544's missing arms are read once at step 200: the VSTI dev set 0.4 and R0-dev's room items 0.4 (guesses). The tower-arm read of step 544 is priced in section 4 (rank 2).","Step 544's baselines are read before R1's first export is read (2.2, item 4d): the VSTI dev set 0.4, R0-dev's room items 0.4 and its direct items about 0.7 (guesses, scaled from 170320), and the tower-arm read 2 to 3 (section 4, rank 2).")
line("| Step 200 | 41.6 |","| Step 200 | 41.6 | 6.0 | 47.6 | T+10.5 h | Harm rule at its first-look level; protected outcomes; gates of every family that trains from step 1 (VSTI, facing, units, and room if store v7 binds at launch) |")
line("| Step 400 | 72.2 |","| Step 400 | 72.2 | 11.2 | 83.4 | T+18 h | Harm rule; protected outcomes; the one further read of a held gate; gates of families that entered at step 200. Spending rule: the leg continues only if the VSTI and facing gates have passed and no protected outcome is on its second failure, and a family not in the leg leaves the claim |")
line("| Step 600 | 102.8 |","| Step 600 | 102.8 | 16.4 | 119.2 | T+26 h | Harm rule; protected outcomes; gates of families that entered at step 400; the one further read of a held gate |")
line("| Step 800 | 133.4 |","| Step 800 | 133.4 | 21.6 | 155.0 | T+33.5 h | Harm rule; protected outcomes; the one further read of a held gate |")
sub("A stop at step 200 therefore costs about 52 H100-hours, and a held gate costs the next boundary, about 36.","A stop at step 200 therefore costs about 52 H100-hours, and a held gate costs the next boundary, about 36. The spending rule ends a leg whose VSTI or facing gate has not passed at the step-400 export, at about 83 H100-hours with that boundary's reads.")
sub("every row allows a loss, and official reads come only for the selected export and decide nothing (section 4).","every row allows a loss, and official reads come only for the selected export and decide nothing (section 4). Object size has no repair in this leg: no size row trains, and dev-S1 size may drift by 0 to -6 points (guess; 2.2, item 4a).")
sub("no traced room row is admitted yet","store v7 holds 431 traced room rows, which locate landmarks and do not derive the area")
# 3.1
sub("Owed: v7 = v6 + traced room rows + 8,740 away rows in ReVSI's wording, with the size family as a parameter; upload; kit binding.","Store v7 = v6 + 431 traced room rows + 8,511 away rows in ReVSI's wording is built and mirrored (204,413 rows, sha256 210b2534), with the size family as a parameter, and its review admits it with conditions (`EV/rows_r1/REVIEW_VERDICT_V7.md`). Owed: the orchestrator's ruling on the conditions, upload and kit binding.")
sub("| rows_r1's build of v7 (due 18:00Z) |","| the ruling on v7's conditions |")
sub("Lane rows_r1 builds traced rows and counts 469 of the 571 traceable before scene exclusions (431 of the 476 pass them on N).","Store v7 holds 431 traced rows (451 of the 571 were traced).")
sub("P: rows whose answer equals the rounded GT, or entry on N; the full source is unbound","P: the faithful slice is built, 1,224 of all 10,945 rows (`units_p_slice_v2`, 40437c8a; ft 1,130, in 94, cm 0; slot UNIT-P); unit rows are required from launch; its box-extent audit is open")
line("| Registration card |","| Registration card | Written: `EV/next_leg/R1_CARD_v3.md`, from sections 2.2 to 2.4, 3.3 and 5, with the line of each amendment in `EV/next_leg/card_fix2_COMPLIANCE.md`. Owed: one compliance check against B1 to B10; the config identity, the admitted counts from the loader audit and the pins per boundary | this record | r1_ops, then orchestrator | 0.5 | the loader audit |")
# 3.2
line("The slot opens when main returns advanced:","The slot opens when main returns advanced, between 23:00Z on 11-17 and 04:00Z on 11-18; main will post a measured estimate and allows the CPU proof on advanced beside its jobs (`EV/r1_ops/20261117T1523Z_ORCH_NOTE_slot_window_proof_on_advanced_sizeV.md`). Plan for 23:00Z.")
line("| 17:30 (09:30) | size_diag fills slot SIZE-V","| 15:20 (07:20) | size_diag's verdict (b) decides slot SIZE-V: R1 draws no size row (5, item 2) | size_diag |")
line("| 18:00 (10:00) | v7 store built and validated","| 15:31 (07:31) | Store v7 and the VSTI relative dev set are built and validated; the faithful unit slice for P follows at 15:39 and v7's review (ADMIT WITH CONDITIONS) at 15:50 | rows_r1, review_v7 |")
line("| 19:30 (11:30) | Production proof 1 of P submitted","| when the packet passes its local gates and its review | Production proof 1 of P, with the loader audit inside, runs on advanced beside main's jobs; 2.6 h per attempt | r1_ops, cont_ops |")
line("| slot - 2 h | Vehicle gate:","| 21:00 (13:00), or two hours before the time main posts | Launch gates (3.3, item 9). The leg launches on P with the families its tree admits, each missing family named on the card with its entry boundary; N takes over only at a boundary where its continuation proof has passed | orchestrator |")
sub("so N can make the late slot and not the early one.","after the slot, so N joins at a boundary and the launch does not wait for it.")
# 3.3
line("5. **The first proof is submitted at least eight hours before the earliest slot,**","5. **The first proof is submitted the moment the packet passes its local gates and its review,** so that fix rounds fit before the slot.")
line("6. **The proof needs the job place.**","6. **The proof runs on advanced beside main's jobs.** Main allows one CPU-only job there (48 cores, 800 GB node-local disk, 4 h limit, at most two repeats). If main writes that its jobs lack CPU or a submit place, the proof moves to general and takes its turn ahead of every read except the two H1-1 m100 reads.")
line("8. **The proof contains a loader audit, and no GO is given without it.**","8. **The proof contains a loader audit on the final config identity, and no GO is given without it.** The production loader and sampler run on the staged files, CPU only, and the receipt prints: (a) the post-filter eligible count of every family and type, beside the store count, with unit rows per unit; (b) the draws the production sampler makes over the planned 1,000 steps, per cell and per type, with distinct rows, the largest repeat of any row, the share of ReVSI-worded rows in the facing cell, the shares per unit and the shares per status; (c) five bound traces per family, printed from the staged bytes. It asserts that every cell is at most 4 x eligible / 1,000 exactly, that no row is drawn more than four times, that no object-size row is bound (slot SIZE-V), that the unit cell is non-zero and binds only rows of the faithful slice, that no one-line room row and no room program is bound, that no row of camera-object absolute distance is bound, and that every family the card names as present has a non-zero count. The card's mix table is filled from this receipt.")
after("8. **The proof contains a loader audit on the final config identity","9. **Launch gates.** Five, and nothing else holds the launch: the production proof with this loader audit, on the final config identity; five bound rows per family, read by the orchestrator and shown to the user; slot SIZE-V decided (section 5: no size row); card v3 registered (`EV/next_leg/R1_CARD_v3.md`); main's release of the slot. The launch does not wait for vehicle N, which takes over only at a boundary where its continuation proof has passed, and it does not wait for step 544's baseline reads, which bind the first read of an R1 export (2.2, item 4d).")
# 4
sub("Once R1 trains, its milestone reads take the place ahead of ranks 3 to 8.","Once R1 trains, its milestone reads take the place ahead of ranks 3 to 8. Step 544's baseline reads (2.2, item 4d: the tower-arm read of rank 2, the VSTI dev read, the R0-dev read and the count on the 49 twins) are registered before R1's first export is read, so they run after the proof and ahead of ranks 3 to 8.")
# options rejected
sub("- **R0-dev as a second stop set:** it doubles the tests, and step 544 has no read on it; it is printed and stops nothing alone.","- **R0-dev as a second, separate stop set:** it doubles the tests. One pooled test per type replaces the dev-S1 test instead, once step 544 is read on R0-dev and the pooled rule is registered before the first export is read (2.2, item 4d).")
after("- **Recovery at 4.00 rows per step:**","\n".join([
"- **Size rows in R1, in v6's form or at a lower dose:** the form caused D0's loss, and D0's switch to it was complete within about 820 rows (size_diag, verdict (b)).",
"- **An efficacy gate on object size:** an unchanged model passes it about 97% of the time, so it shows no repair; size is a protected outcome under H1.",
"- **A gate on the 49 ReVSI-worded twins, or on about 7 status reads:** a population under 60 items cannot carry a gate; both are printed marks.",
"- **A unit gate on the share of gap-valued answers that convert:** the share can rise while fewer reads answer with a gap value; the gate counts conversions over all 107 items.",
"- **Recovery rows as a hard requirement of the leg:** with the best-candidate selector 4.7% of reads draw a status; the requirement is the capped count on the claimed arm.",
"- **Unit answers regenerated to the rounded label, so that P admits every unit row:** the answer would no longer follow from the row's own conversion line.",
"- **Waiting for vehicle N's continuation proof, or for step 544's baseline reads, before launch:** N takes over at a boundary, and the baselines bind the first read of an export, not the launch.",
"- **Binomial bounds on the room call rate:** 36 of the 134 items sit in nine rooms; the bound comes from a bootstrap over rooms.",
"- **A restart from the last passing export under this card:** a restart after a STOP needs a new card.",
"- **A family-wise guarantee read off the simulation:** the rates are estimates on D0's m200 read; the nominal bound, 0.0875 over four looks, is printed beside them.",
]))
# tests
sub("6. `CF/out/unit_none.py` on the scored `items.jsonl` of job 170706 (Orchard): the exact unit baseline on unperturbed reads.","6. The tower-arm read of step 544 with the pinned selector, scored with the rule of `CF/out/unit_none.py`: the claimed arm's exact unit count over the 107 items (the own arm's is 22).")
sub("8. A step-544 read of R0-dev's direct items: it would let R0-dev's 293 size items join the 150 of dev-S1 in one test, the only way to reach both a 5% false stop and 80% power against a loss of D0's size; it needs a ruling, because R0-dev stops nothing today.","8. A step-544 read of R0-dev's direct items (ordered): with it the pooled rule of 2.2 item 4d can be calibrated and registered, and R0-dev's 293 size items, all asked in cm, join dev-S1's 150 in one test.")
after("9. The loader audit on the staged files:","10. R1's own m100 and m200 reads with object size split by metric and imperial items: whether size drifts without size rows, at no extra GPU cost.\n11. The VSTI dev read of step 544: the per-type baselines, and whether back-flips on the type with the highest baseline make the type clause of the VSTI gate bind.")
sub("What must start now: brief 01 (P packet), brief 03 (rows v7), brief 04 (operator), and the request to main in 3.3.","In progress: brief 01 (P packet), brief 03 (rows v7) and brief 04 (operator).")
ls=T.split('\n'); i=[k for k,x in enumerate(ls) if x.startswith('| 15:30 (07:30) | Build 9 ends')]; j=[k for k,x in enumerate(ls) if x.startswith('| 15:20 (07:20) | size_diag')]
assert len(i)==1 and len(j)==1 and j[0]==i[0]+1; ls[i[0]],ls[j[0]]=ls[j[0]],ls[i[0]]; T='\n'.join(ls)
open('../out/NEXT_LEG_DECISION_20261117.md','w').write(T)
print(len(T.split('\n'))-1,'lines',len(T.encode()),'bytes',hashlib.sha256(T.encode()).hexdigest())
