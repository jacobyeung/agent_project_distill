**1. Scope**

The sampled training targets are internally consistent. The main risk is copying a valid form onto the wrong question: step-200 traces reuse toward-facing language on away questions and distance-ranking language on size questions.

I audited **720 of 132,707 rows**, with **60 kept rows per family**, spread across sorted primary keys. The count file reports **132,707 of 132,707 rows kept**. I checked **120 of 720 rows in full**, including their questions and options. Sections 2–5 follow the requested audit format.

Scores below are recomputed B2048 percentages. Each score cell gives **step 544 / step 200**.

| Type | dev-S1 evaluated | Scores | R0-dev evaluated | Scores |
|---|---:|---:|---:|---:|
| Direction easy | 150 of 150 | 91.33 / 93.33 | 192 of 192 | 65.62 / 78.65 |
| Direction medium | 150 of 150 | 89.33 / 88.00 | 194 of 194 | 48.97 / 64.95 |
| Direction hard | 150 of 150 | 84.00 / 82.67 | 192 of 192 | 45.83 / 57.81 |
| Relative distance | 150 of 150 | 70.67 / 73.33 | 279 of 279 | 64.87 / 67.38 |
| Object size | 150 of 150 | 68.73 / 69.40 | 293 of 293 | 59.08 / 58.29 |
| Route planning | 150 of 150 | 78.67 / 80.67 | Not present | — |
| Assigned types combined | 900 of 900 | 80.46 / 81.23 | 1,150 of 1,150 | 57.66 / 64.94 |

The cross-type check also covered relative size: **150 of 150 dev-S1 items**, scoring **91.33 / 90.00**. I did not load VSTI, facing twins, or routed returns.

Training sources were `rows.sqlite`, `FAMILY_INDEX_RANGES.json`, `STORE_V7_TEMPLATE_COUNTS.json`, and the n/z exclusion files named in the brief. I read the ruling’s Answer and relevant type sections.

Trace sources, relative to `/scratch/jjyeung/orch_n30/`, were:
- `evalx27/work/pull/x27/res/e193/merged/main/results/budget_2048/0/items_leg_m544_main.jsonl`.
- `cont_ops16/work/c15/h1read/kit/build/a8102c3207b/fetched/x/{main,a7}/a0/results/{0,budget_2048/0}/items_a0.jsonl`.
- `cont_ops16/work/c15/h1read/kit/build/adff67f7ae9/fetched/x/a7/a0/results/{0,budget_2048/0}/items_a0.jsonl`.

**2. Families and skeleton shares**

Here, E/M/H mean `object_rel_direction_easy/medium/hard`. W means `w1g|rows_rebuild_d0_v1`; G combines the four `rows_rebuild_d0_{ARKIT,T0,T1H1,T1H2}` pools, with `_gaps` for E and `_gen_r2` for M/H; O means `r1_away_opp|None`. Skeletons pool wording paraphrases. The appendix gives one verbatim target per skeleton.

| Family | Kept of total | Skeleton shares in the sample |
|---|---:|---|
| E–W | 12,969 of 12,969 | D: 60 of 60 |
| E–G | 15,024 of 15,024 | T: 30 of 60; A: 30 of 60 |
| E–O | 3,664 of 3,664 | O: 60 of 60 |
| M–W | 15,547 of 15,547 | D: 60 of 60 |
| M–G | 10,912 of 10,912 | T: 30 of 60; A: 30 of 60 |
| M–O | 2,665 of 2,665 | O: 60 of 60 |
| H–W | 21,385 of 21,385 | D: 60 of 60 |
| H–G | 9,022 of 9,022 | T: 30 of 60; A: 30 of 60 |
| H–O | 2,182 of 2,182 | O: 60 of 60 |
| `object_rel_distance|w1g|rows_rebuild_d0_v1` | 20,665 of 20,665 | DF: 42 of 60; DP: 11 of 60; DL: 7 of 60 |
| `object_size_estimation|r1g|rows_rebuild_d0_v1` | 9,778 of 9,778 | SF: 53 of 60; SN: 7 of 60 |
| `route_planning|dose_route_direct|None` | 8,894 of 8,894 | R1: 31 of 60; R2: 17 of 60; R3: 10 of 60; RP3: 2 of 60 |

| Skeleton | Form, with names and numbers replaced |
|---|---|
| D | Locate S, F, Q; state Q’s relation while facing F from S; retain heading; conclude; letter. |
| T | `Seen: S in frame N; F in frame N; Q in frame N.` State forward relation; retain heading; conclude; letter. |
| A / O | Same Seen line; conditional forward relation; explicit half turn for “away” / “opposite”; conclude; letter. |
| DF / DP / DL | Locate anchor using “find … first seen” / “first appearance” / “locate … first appearance”; rank candidates nearest to farthest; select closest; letter. |
| SF / SN | Find object with / without a frame; estimate longest edge in centimeters; numeric answer after `</think>`. |
| R1 / R2 / R3 | State starting position and heading; give one relation and turn per waypoint; finish with the complete turn list; letter. |
| RP3 | R3 with an initial forward movement before the first turn. |

**3. Ruling violations and full checks**

| Check | Result |
|---|---|
| Unsupported non-frame quantity inside the trace | **0 of 60 in each family**. After removing frame indices and step numbers, no digits remain. |
| Answer-only target | **0 of 60 in each family**. |
| Stated relation contradicts answer | **0 of 60 in each family** where a relation/conclusion is present. |
| Object absent from the question | **0 of 60 in each family**. |
| Wrong option letter | **0 of 60 in each choice family**; object-size rows have no options. |
| Wrong arithmetic or half-turn transformation | **0 of 60 in each family**. No numeric arithmetic occurs; all **270 of 270** sampled half turns map consistently. |

The full checks covered **10 of 60 rows per family**. Direction relations mapped to their selected options; relative-distance answers selected the first ranked candidate; route steps matched the requested turns and answer option. Object-size answers matched the row’s answer field, but their physical accuracy cannot be recomputed from text.

The W direction samples omit frames in **180 of 180 rows**. Size omits a frame in **7 of 60 rows**. I did **not** count these as proven violations: the ruling permits omission when the source lacks a frame. These rows do not establish whether that exception applies.

**4. Copy risk and loop risk**

All **720 of 720 sampled targets contain no call**.

| Skeleton | Copy risk: plausible recipient types | Loop rating; longest sampled list |
|---|---|---|
| D | High: other direction levels, relative size, and other questions naming several objects. Its opening does not identify the operation. | Bounded by the question; three objects. |
| T / A / O | Generic Seen opening can transfer to other direction levels and object-relation questions. The following facing clause supplies the type-specific operation. | Bounded by the question; three objects/frames. |
| DF / DP / DL | High: absolute distance, object size, relative size, and appearance order share object-location wording. | Bounded by the question; four candidates, including tied candidates. |
| SF / SN | High: relative distance, absolute distance, and relative size. SF shares DF’s opening exactly. | None; one object. |
| R1 / R2 / R3 / RP3 | Moderate, **HYPOTHESIS**: direction questions also specify a position and heading. The turn instruction distinguishes the route form. | Bounded by the question; three turns. |

I found **0 of 720 sampled targets with an unbounded list**. The route form already ends with “The turns are”; the relative-distance list is bounded by the options.

**5. Step-200 matches and observed cross-type use**

F below matches `Step 1: find the …, first seen in …`, allowing the model’s location wording. “Exact F” requires `frame N.` as in training. Seen matches the shared opening of T/A/O; it cannot identify which pool taught it.

| Set/type | Opening matches |
|---|---|
| dev-S1 direction E/M/H | D: **150 of 150 for each type** |
| R0-dev direction E | D: **117 of 192**; Seen: **74 of 192** |
| R0-dev direction M | D: **119 of 194**; Seen: **72 of 194** |
| R0-dev direction H | D: **138 of 192**; Seen: **53 of 192** |
| dev-S1 relative distance | F: **150 of 150**; exact F: **49 of 150** |
| R0-dev relative distance | F: **279 of 279**; exact F: **122 of 279** |
| dev-S1 object size | F: **143 of 150**; exact F: **42 of 150** |
| R0-dev object size | F: **293 of 293**; exact F: **103 of 293** |
| dev-S1 relative size | F: **14 of 150**; D-shaped opening: **7 of 150**; SN-shaped opening: **30 of 150** |
| dev-S1 route planning | Route opening: **150 of 150** |

DP and DL have **0 of 429 relative-distance matches** across these sets. The model favors DF’s opening. Shared openings establish resemblance, not the originating training family.

| Specific cross-type behavior | Affected items | Wrong items and associated type-score loss |
|---|---:|---:|
| Away-easy keeps heading without a half turn, R0-dev | 14 of 66 away items | 5 of 192 type items; 2.60 points |
| Away-medium keeps heading without a half turn, R0-dev | 5 of 65 away items | 5 of 194 type items; 2.58 points |
| Away-hard keeps heading without a half turn, R0-dev | 24 of 71 away items | 21 of 192 type items; 10.94 points |
| Relative size uses nearest-to-farthest reasoning, dev-S1 | 3 of 150 | 1 of 150; 0.67 points |

For example, R0-dev `05d90f7d09554791b4f0df2f` says: “The question has me face away from the headphones, so I keep that heading.” It answers B; truth is A.

Dev-S1 `vsi590k_186818` asks which has the shorter edge, the ceiling light or bed. Its trace says: “order them from nearest to farthest from the camera: bed, then ceiling light.” It answers A, bed; truth is B, ceiling light. The other distance-order matches are `vsi590k_068356` and `vsi590k_191149`; both score correctly.

**6. Label or scoring defects**

None found in the sampled row text or checked option mappings. I did not validate visual labels or physical sizes against RGB frames.

**7. Three changes for vehicle N**

1. **Reword direction rows to state the requested facing operation first.** Apply this across approximately 93,000 assigned direction rows, preserving paired relations and options. **HYPOTHESIS:** toward-row language overrides the away clause. Applying the stated half turn corrects **21 of 31 wrong keep-heading cases**: **5 of 5 easy**, **2 of 5 medium**, and **14 of 21 hard**. This is a conditional text calculation, not a forecast; blindly flipping all affected answers would break **12 of 43 currently correct cases**.
2. **Reword approximately 20,700 relative-distance rows to open with the comparison being requested**, then locate the anchor and rank only the named candidates. **HYPOTHESIS:** this could prevent the wrong operation in **1 of 150 relative-size items** observed here. The brief’s **62 of 150 routed-distance no-call cases** provide additional motivation, but I did not reprice or re-audit them.
3. **Reword approximately 9,800 object-size rows to identify which visible dimension is longest**, while keeping the measurement after `</think>`. **HYPOTHESIS:** this adds a checkable visual decision to the generic estimate sentence. No specific wrong answer is established as fixable; **105 of 150 dev-S1** and **229 of 293 R0-dev** size items have score below one. These are ceilings, not predicted gains. **I am least sure of this change.**

**8. Not established**

The audit does not establish frame provenance, visual relation correctness, physical measurements, or defect rates outside the sample. Those require source annotations or RGB inspection. It also does not establish that shared openings caused errors; that requires a controlled training comparison. Model text is ON16k where available, while the reported scores are B2048. The audit exception replaces exhaustive wrong-item classification.

**Appendix: CLASSIFIER**

This runnable block reproduces section-2 skeleton counts, prints the sampled indices and full-check subset, and reproduces the opening and cross-type counts. It uses only primary-key SQLite queries.

```python
import sys,json,sqlite3,re
from collections import Counter
sys.dont_write_bytecode=True
P='/scratch/jjyeung/orch_n30/'
sys.path.insert(0,P+'swarm_an/kit'); import san_kit as K
F=json.load(open(P+'r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json'))['families']
bad={json.loads(l)['row_key'] for n in ('n','z') for l in open(P+'r1_ops6/cp/out/records/'+n+'.json')}
db=sqlite3.connect('file:'+P+'r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro',uri=True)
types=['object_rel_direction_'+x for x in ('easy','medium','hard')]
G={}
for t in types+['object_rel_distance','object_size_estimation','route_planning']:
 a=[i for lo,hi in F[t] for i in range(lo,hi+1)]
 if t in types:
  G[t+'|w1g']=[i for i in a if i<106492 or 141450<=i<195000]
  G[t+'|rebuild4']=[i for i in a if 106492<=i<141450]
  G[t+'|r1_away_opp']=[i for i in a if i>=195000]
 else: G[t]=a
def body(s): return s.split('<think>',1)[-1].split('</think>',1)[0].strip()
def skeleton(n,b):
 if b.startswith('Seen:'):
  return 'O' if 'opposite direction' in b else 'A' if 'half turn' in b else 'T'
 if '|w1g' in n: return 'D'
 if n=='object_rel_distance':
  return 'DF' if b.startswith('Step 1: find') else 'DL' if b.startswith('Step 1: locate') else 'DP'
 if n=='object_size_estimation': return 'SF' if 'frame ' in b.splitlines()[0] else 'SN'
 return 'RP3' if 'then go forward' in b else 'R'+str(len(re.findall(r'Step \d+:',b)))
for n,a in G.items():
 ids=[a[round(j*(len(a)-1)/59)] for j in range(60)]
 rows=[json.loads(s) for _,s in db.execute('select i,row from rows where i in ('+','.join('?'*60)+')',ids)]
 assert len(rows)==60 and all(r['qid'] not in bad for r in rows)
 print(n,'kept',len(a),'skeletons',dict(Counter(skeleton(n,body(r['target'])) for r in rows)))
 print('i=',ids,'full-check i=',[ids[round(j*59/9)] for j in range(10)])
pat={
 'D':r'^Step 1: (?:find|locate) the .+(?:, the .+ and the | and the .+, then the ).+\.$',
 'Seen':r'^Seen: .+ in frame \d+; .+ in frame \d+; .+ in frame \d+\.$',
 'F':r'^Step 1: find the .+, first seen in .+',
 'Fexact':r'^Step 1: find the .+, first seen in frame \d+\.$',
 'DP':r'^Step 1: the first appearance of the .+ is in frame \d+\.$',
 'DL':r'^Step 1: locate the .+ at its first appearance in frame \d+\.$',
 'SN':r'^Step 1: find the [^,;.]+\.$',
 'R':r'^Step 1: I stand at the .+ facing the .+'}
for s in ('dev-S1','R0-dev'):
 rows=K.direct('R1',200,s)
 for t in sorted({r['type'] for r in rows}):
  a=[r for r in rows if r['type']==t]
  c=Counter(k for r in a for k,p in pat.items() if re.search(p,body(r['text'] or '').split('\n')[0]))
  print(s,t,'N',len(a),'opening matches',dict(c))
  b=[r for r in a if re.search(r'away|opposite|back to',r['question'],re.I) and re.search(r'no turn applies|keep that heading',r['text'] or '') and 'half turn' not in (r['text'] or '')]
  if b: print('away keep-heading',len(b),'wrong',sum(r['score']<1 for r in b),'cost',100*sum(1-r['score'] for r in b)/len(a))
  b=[r for r in a if t=='relative_size_object' and re.search('nearest.to.farthest',r['text'] or '')]
  if b: print('size distance-order',len(b),'wrong',sum(r['score']<1 for r in b),'ids',[r['id'] for r in b])
```

**Appendix: sampled primary keys**

The full-check subset uses zero-based positions `0, 7, 13, 20, 26, 33, 39, 46, 52, 59` in each list.

```text
E–W:
6,1941,3719,5436,7125,8717,10411,12002,13736,14989,15964,16975,17843,18958,20162,21186,22395,23362,24412,25404,26705,28282,29755,30998,32183,33399,34405,35669,37522,39265,57217,58809,59970,61415,62677,63991,65239,66523,67742,68672,69500,70391,71167,72252,73163,74101,75042,75842,76731,77667,78865,80180,81257,82209,83255,84262,85247,86832,88334,147889
E–G:
106496,107117,107705,108292,108867,109417,110052,110616,111167,111786,112398,113027,113646,114252,114851,115445,116042,116569,117177,117864,118457,119017,119560,120144,120731,121354,121936,122553,123106,123676,124369,124987,125558,126261,126875,127448,128027,128651,129286,129922,130587,131192,131758,132345,132936,133476,134079,134641,135222,135817,136373,136888,137423,138017,138630,139202,139775,140316,140862,141449
E–O:
195905,196041,196179,196315,196439,196604,196765,196910,197080,197227,197361,197519,197666,197797,197918,198075,198206,198337,198467,198629,198795,198940,199107,199252,199402,199556,199717,199870,199992,200142,200309,200449,200586,200735,200869,201003,201175,201319,201484,201644,201776,201907,202078,202231,202368,202518,202686,202822,202947,203095,203239,203373,203514,203670,203816,203949,204093,204214,204312,204409
M–W:
5,1971,4314,6949,9450,11944,14503,16280,17885,19031,20207,21445,22639,23731,24842,26091,27190,28398,30223,31776,33498,34859,36017,37238,38481,39480,40295,41288,42420,43970,57436,59000,61167,63028,65022,66941,68611,70138,71227,72230,73229,74182,75120,76127,77083,78027,78887,80038,81575,82960,84316,85499,86611,87655,88793,89603,90441,91470,92649,94423
M–G:
106492,107065,107670,108263,108844,109483,110066,110651,111351,111930,112467,112978,113455,114036,114687,115286,115879,116540,117153,117678,118261,118870,119489,120045,120644,121297,121830,122377,122964,123593,124116,124673,125270,125859,126402,127101,127614,128218,128759,129268,129815,130342,130879,131482,132019,132648,133285,133976,134581,135236,135897,136572,137208,137805,138368,138925,139596,140183,140782,141447
M–O:
195902,196071,196231,196394,196544,196635,196796,196933,197086,197208,197374,197521,197656,197787,197967,198076,198243,198410,198527,198636,198771,198875,199006,199153,199274,199395,199532,199632,199766,199914,200065,200219,200324,200487,200636,200782,200919,201089,201249,201367,201507,201634,201769,201898,202034,202162,202297,202433,202579,202725,202885,203049,203169,203309,203459,203640,203777,203913,204044,204192
H–W:
0,2496,5081,7693,10430,13925,16532,18621,20467,22380,24518,26647,28408,29991,31383,32645,33805,34823,35889,36838,37823,38841,40402,41761,42950,44022,44854,45591,46214,46818,47474,48148,48996,57808,60123,62395,64813,68031,70627,72560,74589,77025,79142,80742,82260,83604,84772,86090,87226,88399,89934,91464,92785,93946,94813,95506,96170,96857,97577,98846
H–G:
106502,107061,107620,108261,108876,109456,109991,110646,111211,111732,112395,113058,113737,114226,114787,115383,115978,116581,117132,117705,118266,118865,119536,120173,120772,121260,121939,122544,123147,123770,124259,124876,125477,126004,126499,127005,127724,128271,128936,129545,130092,130737,131312,131943,132570,133128,133705,134246,134839,135354,135931,136516,137171,137704,138335,138967,139600,140263,140902,141437
H–O:
195906,196028,196187,196313,196476,196626,196747,196887,197016,197119,197287,197416,197557,197715,197867,198037,198181,198357,198509,198658,198809,198974,199106,199265,199450,199607,199751,199869,200071,200177,200326,200474,200616,200748,200899,201033,201161,201294,201412,201549,201719,201909,202043,202165,202335,202479,202608,202730,202878,203023,203171,203346,203477,203599,203738,203890,204061,204209,204314,204412
Relative distance:
1,852,1737,2608,3487,4340,5229,6078,6902,7728,8606,9431,10304,11175,11980,12807,13563,14665,16826,18526,19881,21243,22548,24031,25437,26695,27966,29099,30356,32387,57084,58489,59796,61158,62411,63709,65077,66349,67719,71148,73383,75647,77813,79788,82262,142950,143303,143656,144007,144358,144708,145059,145410,145764,146121,146473,146828,147180,147533,147886
Object size:
39,9618,17255,20643,24382,27678,30225,32336,34393,36217,37965,39336,40514,41547,42515,43434,44208,44925,45925,47044,48024,48891,49467,49917,50368,50740,51146,51539,51946,52339,59580,67310,71606,74523,77457,79933,82033,83723,85583,87129,88606,89840,90951,91859,92759,93614,94281,94912,96049,97039,97925,98532,99029,99446,99863,100230,100642,101051,101462,101826
Route planning:
101831,101982,102132,102283,102434,102585,102735,102886,103037,103188,103338,103489,103640,103790,103941,104092,104243,104393,104544,104695,104846,104996,105147,105298,105448,105599,105750,105901,106051,106202,106353,147902,148052,148203,148354,148505,148655,148806,148957,149107,149258,149409,149560,149710,149861,150012,150163,150313,150464,150615,150765,150916,151067,151218,151368,151519,151670,151821,151971,152122
```

**Appendix: verbatim targets**

These are JSON strings; `\n` represents an original newline.

```text
D — i=6
"<think>\nStep 1: find the bottle and the bucket, then the stair.\nStep 2: I stand at the bottle facing the bucket; I find the stair to my right.\nThe question has me face the bucket, so no turn applies.\nSo I find the stair to my right.\n</think>\n\nA"

T — i=106496
"<think>\nSeen: refrigerator in frame 17; table in frame 31; door in frame 6.\nStanding at the refrigerator facing the table, I find the door to my right.\nThe question has me face the table, so no turn applies.\nSo I find the door to my right.\n</think>\n\nA"

A — i=107117
"<think>\nSeen: whiteboard in frame 28; telephone in frame 19; laptop in frame 27.\nIf I stood at the whiteboard facing the telephone, the laptop would be to my left.\nThe question has me face away from the telephone. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the position of the laptop to my right.\n</think>\n\nB"

O — i=195905
"<think>\nSeen: couch in frame 13; telephone in frame 32; radiator in frame 6.\nIf I stood at the couch facing the telephone, the radiator would be to my left.\nThe question has me facing in the opposite direction of the telephone. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.\nSo I find the radiator to my right.\n</think>\n\nA"

DF — i=1
"<think>\nStep 1: find the bag, first seen in frame 8.\nStep 2: the candidates ordered nearest to farthest from the bag are: bookshelf, then boxes, then flipchart, then electrical duct.\nThe question asks me to choose the closest, which is the bookshelf.\n</think>\n\nA"

DP — i=1737
"<think>\nStep 1: the first appearance of the backpacks is in frame 7.\nStep 2: the nearest-to-farthest order from the backpacks is: clothes drying rack, then boot, then air diffuser, then air fryer.\nThe question asks which is closest; it is the clothes drying rack.\n</think>\n\nB"

DL — i=6902
"<think>\nStep 1: locate the blinds at its first appearance in frame 2.\nStep 2: from nearest to farthest from the blinds, the order is: monitor, then cabinet, then box, then clothes hanger.\nThe question asks for the closest object, the monitor.\n</think>\n\nD"

SF — i=39
"<think>\nStep 1: find the webcam, first seen in frame 17.\nStep 2: the question asks for the longest edge, in centimeters. I estimate it from the frames.\n</think>\n\n20"

SN — i=49917
"<think>\nStep 1: find the blind.\nStep 2: the question asks for an estimate of the longest edge, in centimeters, from the frames.\n</think>\n\n200"

R1 — i=101831
"<think>\nStep 1: I stand at the blinds facing the heater. I find the air duct behind me: turn back.\nThe turns are: back.\n</think>\n\nC"

R2 — i=147902
"<think>\nStep 1: I stand at the basket facing the water filter. I find the laundry bag behind me: turn back.\nStep 2: I go forward to the laundry bag and keep that heading. I find the mat to my right: turn right.\nThe turns are: back, right.\n</think>\n\nD"

R3 — i=148655
"<think>\nStep 1: I stand at the footstool facing the paper roll. I find the coffee table to my left: turn left.\nStep 2: I go forward to the coffee table and keep that heading. I find the sofa to my left: turn left.\nStep 3: I go forward to the sofa and keep that heading. I find the armchair to my right: turn right.\nThe turns are: left, left, right.\n</think>\n\nD"

RP3 — i=150163
"<think>\nStep 1: I stand at the dumbbell plates facing the telephone, then go forward to the telephone and keep that heading. I find the fan to my right: turn right.\nStep 2: I go forward to the fan and keep that heading. I find the sofa to my right: turn right.\nStep 3: I go forward to the sofa and keep that heading. I find the towel to my left: turn left.\nThe turns are: right, right, left.\n</think>\n\nB"
```