import re,sys
L=open('RECORD_orig.md').read().split('\n')
assert len(L) in (211,212), len(L)
B=lambda n: open('blocks/'+n).read().rstrip('\n')
def line(i): return L[i-1]
def chk(i,prefix): assert line(i).startswith(prefix), (i,line(i)[:80])
out={}
# --- preamble
chk(3,'Lane next_leg (Devin')
out[3]=line(3).replace('`L` = trinity-1-3 `/scratch/jjyeung/orch_n30/next_leg`.',
  '`L` = trinity-1-3 `/scratch/jjyeung/orch_n30/next_leg`, `CF` = trinity-1-3 `/scratch/jjyeung/orch_n30/card_fix`, `RP` = trinity-1-3 `/scratch/jjyeung/orch_n30/r1_pkt/out`, `H10` = trinity-1-3 `/scratch/jjyeung/orch_n30/h10_score/work/results/170706`.')
assert out[3]!=line(3)
out[3]=out[3].replace('Lane next_leg (Devin, trinity-1-3), design only: no GPU, no Orchard call, no Git, no dispatch.','Lanes next_leg and card_fix (Devin, trinity-1-3), design only: no GPU, no Orchard call, no Git, no dispatch.')
# --- answer 12-18
chk(12,'## Answer'); chk(18,'6. **Four points')
out[(12,18)]=B('answer.md')
# --- 1.1 rows
chk(29,'| `<ground obj=A mode="box">`'); chk(31,'| room |')
out[29]=r'''| `<ground obj=A mode="box">` | frame list with best frame; box centre, size, yaw; or `A: not seen` | SAM 3 tower on the raw name; selector head (b04 `run_iso`, 6d97c524, trained on K1), which returns its best candidate whenever candidates exist once lane reader_r1's check passes (until then its null slot can print `not seen` over candidates); lifting `bestspread` (fixed math) on G3T depth x `tower_scale`; G3T pose x scale into frame 1; own gravity for level and yaw | GT instance masks, GT depth, GT poses (sealed v3.14 rows); recovery rows print `A: not seen` or `box unavailable` on an operand |'''
out[31]=r'''| room | no call; a `<ground mode="room">` from the model is unserved and its rate is printed | none | direct rows with a qualitative trace: Locate lines with verified frames, one Relate line, then the estimate. None is admitted yet (5, item 2) |'''
# --- 1.2 first bullet
chk(34,'- **Own pose head or G3T for camera calls: G3T.**')
out[34]=B('s12_first.md')
# --- 1.3
chk(40,'- **Statuses.**'); chk(41,'- **Own heads train as auxiliaries')
out[(40,41)]=B('s13.md')
# --- 1.4 U4
chk(51,'| U4 |')
out[51]=r'''| U4 | Room rows end in an estimate that no call supports; the qualitative trace before it (Locate lines for the room's landmarks, one Relate line on the layout) is what separates them from an answer-only row | Only traced rows are admitted; one-line rows are in no store. No room tool clears its bar (DA3 +16.67 held-out, 0.5 short; `DD/GEO_TOWERS_K1_PRICING_20261116.md`) |'''
# --- 2.1 small fix: candidate H1-2 row mentions step-200 read; keep
# --- 2.2
chk(66,'### 2.2 The five lines'); chk(71,'5. **Decision it changes.**')
out[(66,71)]=B('s22.md').replace('`CF/a3/`','`CF/work/a3/`').replace('`CF/../out/unit_none.py`','`CF/out/unit_none.py`').replace('`h10_score/work/o/c7.out`','`/scratch/jjyeung/orch_n30/h10_score/work/o/c7.out`')
# --- 2.3
chk(73,'### 2.3 Decision table'); chk(86,'| | Either fails where step 544 passed')
out[(73,86)]=B('s23.md')
# --- 2.4
chk(88,'### 2.4 Cost'); chk(97,'| VSI-Bench, eight tasks')
out[(88,97)]=B('s24.md')
# --- 3.1 rows
def row(i,prefix,new): chk(i,prefix); out[i]=new
row(108,'| Rows store and admission |',r'''| Rows store and admission | v6 admitted and mirrored (0608dd98, 195,471 rows) and uploaded to Orchard (`okh7/s_8805de22/d.db`, sha equal). P's sealed tree admits all 195,471 rows in 16 types under its structural and exclusion predicates; that is a row census, not a production preparation. Owed: v7 = v6 + traced room rows + 8,740 away rows in ReVSI's wording, with the size family as a parameter; upload; kit binding. N: binding D3 missing; the mix table has no cell for VSTI relative or first-seen rows | `RP/ADMISSION_BY_TYPE.json`, `RP/REPORT.md`; `EV/r1_ops/20261117T1429Z_RESULT_admission_partial_and_store_v6_uploaded.md`; `EV/rows_r1/STATUS.md`; `W/out/MIX_A0.md` | rows_r1, r1_ops, tree_rebuild | 3 to 4 | rows_r1's build of v7 (due 18:00Z) |''')
chk(110,'| Five rows per type |')
out[110]=line(110).replace('The full sheet from the bound Orchard files is owed','The loader audit prints the full sheet from the staged files (3.3, item 8)').replace('the room rows are one restating line','the two room rows are one restating line, a form no store admits')
assert out[110]!=line(110)
row(115,'| Recovery rows from real failures |',r'''| Recovery rows from real failures | 1,532 rows, all simulated `not seen`, 1,458 eligible on N; P's sealed tree refuses all of them (`ground_rows.py:82`, the `not_seen` membership rule). The simulated misses sit on the wrong objects (434 rows on five names that fail on 1 of 89 real pairs), and no row misses both operands. Owed: rows redrawn toward the real failures and 383 `box unavailable` rows | `W/work/build9/proofs/row_counts/RESULT.json`; `RP/ROUTING_DIAGNOSIS.json`; `EV/notseen_diag/20261117T1431Z_RESULT_notseen_diagnosis.md` (brief B2) | rows_r1 | 3 | P: a reviewed change of the admission rule, or entry on N |''')
row(116,'| Unit rows |',r'''| Unit rows | The slice holds 2,000 rows of a source population of 10,945; 1,915 are eligible on N (ft 666, in 643, cm 606), at 2.87 per step with one written conversion line. P's sealed tree admits 216 of the 2,000 after native repacking; 1,784 fail its exact two-decimal label test (the trace answers 10.56 feet where GT rounds to 10.58) | `W/work/build9/proofs/row_counts/RESULT.json`; `RP/REPORT.md`, `RP/ROUTING_DIAGNOSIS.json` | rows_r1, r1_ops | 1 to 2 (guess) | the label rounding of the rows, or entry on N; the full source is unbound |''')
row(117,'| Room |',r'''| Room | The 476 + 95 one-line rows are admitted by no store. Lane rows_r1 builds traced rows and counts 469 of the 571 traceable before scene exclusions (431 of the 476 pass them on N). The cell is min(2.00, 4 x eligible / 1,000), 0 while none is admitted. P drops the 581 room programs from its routing selection, a pin change | `EV/rows_r1/STATUS.md`; `RP/ADMISSION_BY_TYPE.json`; `W/work/build9/proofs/row_counts/RESULT.json` | rows_r1; r1_ops | 2 to 4 (guess) | verified first-seen data per scene |''')
chk(118,'| Orchard packaging |')
out[118]=line(118).replace('the change is the VQA binding, `max_own_probability 0`, S2 and the room selection','the change is the VQA binding, `max_own_probability 0`, S2 off and the room selection')
assert out[118]!=line(118)
row(120,'| Registration card |',r'''| Registration card | Written: `EV/next_leg/R1_CARD_v2.md`, one page, from sections 2.2 to 2.4 and 5. Owed: one confirmation review; the config identity, the admitted counts from the loader audit, the pins per boundary and the verdict in slot SIZE-V | this record | r1_ops, then orchestrator | 0.5 | the loader audit; size_diag |''')
# --- 3.2
chk(132,'| 18:00 (10:00) | H1-1 m100 reads land')
out[132]='| 17:30 (09:30) | size_diag fills slot SIZE-V (5, item 2) | size_diag |\n| 18:00 (10:00) | H1-1 m100 reads land and are reported (2.3); S2 stays off | orchestrator |'
chk(136,'| slot - 2 h | Vehicle gate')
out[136]='| slot - 2 h | Vehicle gate: N launches only if its seal, review, records, frame-host job and production proof have all passed; otherwise P with the families its sealed tree admits, each missing family named on the card with its entry boundary (Answer 3); otherwise the slot waits for N. Either vehicle needs the loader audit and the verdict in slot SIZE-V, or the orchestrator\'s choice in its place | orchestrator |'
# --- 3.3
chk(146,'4. **Any change reruns the whole proof.**')
out[146]='4. **Any change reruns the whole proof.** A new store sha, mix table, selection pin or S2 value changes the config identity, and the proof binds that identity.'
chk(149,'7. **No GPU step can be rehearsed')
out[149]=line(149)+'\n'+B('s33_item8.md')
# --- 4
chk(157,'| 2 | Tower-arm read of step 544')
out[157]=r'''| 2 | Tower-arm read of step 544 on the 636 dev-S1 routed items through b04's reader (G3T pose and depth, own-depth scale, own gravity, `bestspread`, and the selector without its null slot once reader_r1's check passes), paired with H1-0's own arm | Fixes section 1 by measurement: own minus tower per camera type, joined by item key on one reader build, and the `not seen` rate under tower lifting. It is also step 544's arm for H3 and for the claimed-arm distance marks of rule 2.2 | 2 to 3 H100 (job 170056 took about 1.3 per arm; SAM 3 in the call adds 2 to 7 s per name) |'''
chk(159,'| 4 | Official ReVSI, VSTI and VSI-Bench reads of step 544')
out[159]=r'''| 4 | Official ReVSI, VSTI and VSI-Bench reads of step 544 through the reader that passed rank 3 | None. The reads are report-only: they give the first claimed seven-category and eight-task numbers, beside which R1's official read is reported. No routing, row or mix decision is taken from an official item; whether distance stays routed is decided at the next seal on dev-S1 and R0-dev reads, under a rule registered before those reads exist | at least 2.3 (ReVSI) and 6.4 (VSI-Bench) H100 (`DD/OFFICIAL_READ_KIT_B07_20261116.md`) |'''
chk(165,'| conditional | D0 m100 evaluator camera read')
out[165]='| conditional | D0 m100 evaluator camera read | None in R1: it holds the schedule restart equal for the H1-1 bundle read and cannot separate S2 from S1 (2.3); only under ORCH 1355Z item 4 | about 1 H100 |'
# --- 5
chk(169,'## 5. Pre-launch checklist'); chk(183,'5. **Cost and readout.**')
out[(169,183)]=B('s5.md').replace('17.42 / 15.15 / 11.96 | 14,020','17.42 / 15.15 / 11.96 | 14,020').replace('| | absolute distance | 15.61 |','| | absolute distance | 15.60 |').replace('5.1% of the 19.48 distance rows per step (absolute distance 15.61,','5.1% of the 19.47 distance rows per step (absolute distance 15.60,')
# --- options rejected: append
chk(192,'- **Stopping the reads to free the job place:**')
out[192]=line(192)+'\n'+r'''- **95% intervals on the seven types without a correction:** they stop an unchanged model 17.9% of the time at one boundary (computed, `CF/work/a3/A3_POWER_PASS2.json`).
- **R0-dev as a second stop set:** it doubles the tests, and step 544 has no read on it; it is printed and stops nothing alone.
- **A stop rule strict enough for a 5% false stop over the whole leg:** at the later-look level the rule already sees a loss of D0's size only 33% to 58% of the time.
- **One-line room rows:** a restated question and a number is an answer-only row.
- **An official read that decides routing:** official items select nothing; the 53.4 threshold on native distance is not used.
- **S2 set from the H1-1 read:** that read moves S1 and S2 together, so it cannot justify S2 alone.
- **Recovery at 4.00 rows per step:** it would print a status on 18% of distance rows where the serving reader prints one on 4.7% of reads.'''
# --- what might not work
chk(195,'- **Size falls again.**'); chk(198,'- **The room call survives 200 steps.**'); chk(201,'- **R0-dev has no VSTI-style or camera item**')
out[195]=line(195).replace('Sign: object size at m100 and m200 against step 544; rule 2.2 stops the leg and size moves to a head route.','Sign: object size at m100 and m200 against step 544. The size gate holds the boundary when the 95% interval is wholly below zero, and H1 stops the leg at its stricter level, after which size moves to a head route; the verdict in slot SIZE-V may take the family out before launch.')
assert out[195]!=line(195)
out[198]='- **The room call survives.** Traced room rows may not exist at launch, and the habit is untrained until they enter. Sign: the room gate, due 200 steps after they enter.\n- **The harm rule misses a real loss.** Against a loss of D0\'s size on one type it stops the leg with probability 0.40 to 0.73 at step 200. Sign: the size gate at the 95% level and the printed intervals; the init rule\'s tests on the final export catch what the boundaries miss.\n- **A gate passes on the wrong arm.** Recovery and units are gated on the own arm, where step 544\'s files exist, while the claim rests on the tower arm. Sign: the claimed arm\'s capped rate and conversion share, printed at every boundary; the tower-arm read of step 544 moves the gates to that arm.\n- **The recovery dose is too small.** 200 draws by the gate may not teach the continuation. Sign: the recovery gate holds; the cell then rises to 2.00.'
out[201]='- **The VSTI relative gate has no items.** R0-dev has no VSTI-style or camera item (`DD/R0_RESERVE_SCENES_20261116.md`), and lane rows_r1 is building 150 items per type on R0-dev rooms. Sign: if the set or its step-544 read is missing at step 200, the gate cannot be evaluated and the boundary holds for that family.'
chk(196,'- **The sealed tree refuses the new families,**')
out[196]='- **The sealed tree refuses families,** so P carries part of R1: all recovery rows fail its `not_seen` membership rule, and 1,784 of 2,000 unit rows fail its two-decimal label test (`RP/ROUTING_DIAGNOSIS.json`). Sign: the loader audit\'s counts per family. Those families enter at step 200 on N, or earlier if a reviewed packet change admits them, and the card names them as missing until then.'
# --- tests
chk(203,'## Tests that would settle it'); chk(208,'5. EAT-1 on GPU after build 10')
out[208]=line(208)+'\n'+r'''6. `CF/out/unit_none.py` on the scored `items.jsonl` of job 170706 (Orchard): the exact unit baseline on unperturbed reads.
7. D0's m100 item file joined with m200: the correlation between looks, which replaces the union bound over boundaries.
8. A step-544 read of R0-dev's direct items: it would let R0-dev's 293 size items join the 150 of dev-S1 in one test, the only way to reach both a 5% false stop and 80% power against a loss of D0's size; it needs a ruling, because R0-dev stops nothing today.
9. The loader audit on the staged files: the eligible counts and sampling shares behind every cell of the mix.'''
chk(207,"4. R1's step-200 read under rule 2.2.")
out[207]="4. R1's boundary reads under rule 2.2: the harm rule at steps 200 to 800 and each family's gate 200 steps after it enters."
# --- status
chk(211,'ACCEPTED by the orchestrator 2026-11-17T14:15Z')
out[211]=r'''Leg and serving table ACCEPTED by the orchestrator 2026-11-17T14:15Z (`EV/next_leg/20261117T1415Z_ORCH_RULING_r1_accepted.md`). The card (sections 2.2 to 2.4, 3.3, 4 and 5) states the adjudication's amendments A1 to A12 (`EV/next_leg/20261117T1423Z_ORCH_ADJUDICATION_r1_card_review.md`) and ORCH NOTE 1432Z; one confirmation review is owed before it is registered. Registration text: `EV/next_leg/R1_CARD_v2.md`, for lane r1_ops to complete with the config identity and the admitted counts. Open slots: SIZE-V (lane size_diag, due about 17:30Z); the unit baseline's exact count (Tests, item 6); the tower-arm read of step 544 (section 4, rank 2); the interval-level parameter of the read tools (cont_ops). Lanes at work: r1_ops (briefs 01, 04), rows_r1 (brief 03), reader_r1, size_diag. Briefs: `EV/next_leg/briefs/`. Open for the user: U1 to U4, each with its default in force. Nothing was launched, dispatched or changed outside `L`, `CF` and this record.'''
# assemble
res=[]; i=1; ranges={k:v for k,v in out.items() if isinstance(k,tuple)}; singles={k:v for k,v in out.items() if isinstance(k,int)}
starts={a:(b,v) for (a,b),v in ranges.items()}
while i<=len(L):
    if i in starts:
        b,v=starts[i]; res.append(v); i=b+1
    elif i in singles: res.append(singles[i]); i+=1
    else: res.append(L[i-1]); i+=1
open('RECORD_new.md','w').write('\n'.join(res))
print('ok',len(res))
