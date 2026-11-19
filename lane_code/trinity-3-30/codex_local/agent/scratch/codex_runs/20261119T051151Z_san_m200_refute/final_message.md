Do not rely on the causal claims, the guarantee that form B cannot loop, or the zero benchmark value assigned to conversion rows. The size-prior comparison mixes truth and scoring conventions, and the ranking mixes ceilings with conditional gains.

Paths below: **D** = `K.direct`; **V** = `K.vsti`; **F** = `K.facing`; **R** = `K.routed`; **S** = read-only SQLite primary-key queries. All classifiers were independently written; author scripts were not executed. “≈” marks an approximate claim.

| Claim / section | Record | Recomputed | Result | Code path |
|---|---:|---:|---|---|
| Answer 1: direction / size / route / VSTI / camera items | 1,028 / 443 / 150 / 900 / 450 | Same | MATCH | D/V/R, type counts |
| Answer 1: wrong-answer departures, those five groups | 0 each | 0 observed; one size trace lacks a conclusion | MATCH, coverage caveat | Conclusion-to-answer parsing |
| Answer 1: relative-distance departures / wrong items | 1 / 131 | 1 / 131 | MATCH | D, conclusion and score |
| Answer 1: routed-distance departures | 15 | 15 fail numeric agreement at 1% tolerance | MATCH, definition caveat | R, converted gap |
| Answer 2: metre head loss; VSI / ReVSI proxy | 39.8; 5.0 / 5.7 | 39.767; 4.971 / 5.681 | MATCH | R, gap counterfactual |
| Answer 2: metre call loss, VSI | 0.4 | 0.407 | MATCH | R, replacement with base gap |
| Answer 2: size loss, VSI / ReVSI | 3.8 / 6.0 | 3.825 / 5.958 | MATCH | D, weighted score deficit |
| Answer 2: appearance / relative-distance losses | 4.7 / 3.3 / 4.7 | 4.726 / 3.333 / 4.724 | MATCH | D, category weights |
| Answer 2: room VSI / ReVSI; camera displacement | 4.1 / 5.1; 3.6 | 4.132 / 5.085; 3.627 | MATCH | R, score deficit |
| Answer 2: size advantage over class median | 1–5 | 4.00 / 3.09 on matched items and scoring | MATCH range | S+D, class median/MRA |
| Answer 3 / §5: multiple-count ceiling | 1.60 | 1.6035 | MATCH | D, non-looping multiple truth-2 loss |
| Answer 3 / §5: turn gain, fixed-forward / conditional / ceiling | 0.39 / 0.87 / 1.33 | 0.3872 / 0.8729 / 1.3266 | MATCH | D, easy/hard away leaves |
| Answer 3 / §5: counting return-to-base, VSI / ReVSI | 0.48 / 0.39 | 0.4833 / 0.3875 | MATCH | D, paired forced-close items |
| Answer 3 / §5: counting ceilings | 2.23 / 2.64 | 2.2333 / 2.6444 | MATCH | D, weighted forced-close loss |
| Answer 3 / §5: back-relation ceilings | 0.56 / 0.59 | 0.5556 / 0.5936 | MATCH | D, back-to-front/side errors |
| Answer 3: conversion gain on dev-S1 | 5.9 | 5.8667 | MATCH | R, faithful caller conversion |
| Answer 4: runaway type losses | 17.9 / 19.5 / 11.5 | 17.8667 / 19.5325 / 11.5108 | MATCH | D, forced-close loss |
| Answer 4: base scores on current runaways | ≈25–27 | 25.00 / 27.23 | MATCH ≈ | D, paired items |
| Answer 4: truth-3 undercounts with two entries | 49/49; base also two | 49/49 single-category; base 14/14 + 37/37 | MATCH | D, inventory parsing |
| Answer 4: truth-3 / truth≥5 scores | ≈46 / ≈15 | 48.46, 44.05 / 17.24, 14.06 | MATCH ≈ | D, truth bands |
| Answer 5: camera calls/use; wordings per type | 450/450 both steps; 1 | Same | MATCH | R, call arguments and response mapping |
| Answer 5: metre calls; current/base scores | 36/43; 57.0/60.7 | 36/43; 56.977/60.698 | MATCH | R, metre subset |
| Answer 6: away / opening / omitted turn / wrong | 202 / 43 / 42 / 31 | Same | MATCH | D, opening and turn clauses |
| Answer 6: vocabulary; unfamiliar/familiar opening rates | 73; 20/53; 0/9 | 73 sampled names; 20/53; 0/9 | MATCH, sample caveat | S+D, name membership |
| Answer 7: any-zero rows; constant margins; changing pairs | 1,112/1,200; 4–13; 18/59 | Same; 4.00–12.67; 18/59 | MATCH | S/V, shares and shared-object ranks |
| Answer 8: citations above 32, appearance/VSTI/away | 100/246; 373/900; 121/150 | Same | MATCH | D/V/F, frame-number regex |
| Answer 8: sampled training citation range | Integers 1–32 | 2,700/2,700 valid in independent 600-row sample | MATCH sample | S, target citations |
| §11: VSI appearance / route / direction losses | 4.73 / 2.42 / 1.50 | Same rounded | MATCH | D, weighted deficits |
| §11: ReVSI size / route / count / relative-distance / direction | 5.96 / 2.76 / 7.12 / 4.72 / 4.62 | Same rounded | MATCH | D, equal subtype means |
| §11: VSTI relative-distance / relative-position | 11.02 / 5.64 | Same rounded | MATCH | V, equal subtype means |
| §10.5: all-zero / all-at-floor rows | 588 / 74 | 588 / 74 | MATCH | S, seed-77 sample |
| §10.8: direction rows | 93,370 | 93,370 | MATCH | S, family index ranges |
| §10.9: dev-S1 baseline/model, common truth and scorer | 63.4 / 67.6 | 63.4 / 67.4 | MISMATCH | S+D, both rescored against `answer` |
| §5/11: ReVSI metre-call gain | 0.46 | 0.465116 → **0.47** | MISMATCH | R, round only after weighting |

**Corrections and inference tests**

- **(a) Opening and names: association supported; deterministic and causal claims unsupported.** One of 43 “Step 1” traces turns correctly; 33 of 53 items with entirely unfamiliar names nevertheless use “Seen:”. Correct: “Opening and vocabulary predict turn omission; these observational counts do not identify what causes the opening.”
- **(b) Visibility: supported for annotated training visibility, unverified for dev RGB.** All 3,000 instance frames equal `first_seen`; 712 objects have positive queried-frame share at a different frame. Thus `frame_n_share` is not merely first-seen visibility. However, 86 positive shares fall below the floor. Correct: “1,112 sampled training rows contain an object with zero GT-raster share at k; dev visibility remains unmeasured.”
- **(c) Size: class parsing and item matching hold; scoring consistency fails.** Independent trace-name parsing agrees on all 5,000 training rows and 443 dev items. But 27/50 supported dev-S1 items have different truth fields. For `vsi590k_053924`, prediction 75.2 scores 0.9 against released truth 83.5, versus 0.8 against `answer` 83.8. Correct: “Using one truth and scorer, the matched advantages are 4.00 and 3.09 points.” The broad 1–5 claim survives.
- **(d) Form B: untested.** Numbered “1 of N” entries occur in **0/535** base traces; **527/535** begin with a visibility list before announcing the count. Base force-closes are **2/150 and 10/385**. Correct: “Step 544 supports a related form; neither numbered entries nor removing the initial visibility list has a measured effect.”
- **(e) Conversion value: cannot decide from the permitted project documents.** None specifies an exclusively metre-based distance distribution. Correct: “The observed conversion counterfactual gains 5.87 dev-S1 type points; its benchmark contribution is undetermined.”
- **“All loss is perception/head accuracy”: too strong.** Agreement between trace and answer locates failure upstream of final answer mapping; it does not separate perception, reasoning, annotation error, and template effects. Likewise, the 15 distance “departures” include three responses without a numeric gap, rather than 15 measured numeric mapping errors.
- The **0.46 → 0.47** mismatch comes from premature rounding. It does not materially change a decision.

**Mapping and ranking**

The documents support task weights **1/8, 1/7, 1/5**, ReVSI counting leaves **1/14**, and its four direction leaves **1/28**, excluding medium. VSTI’s relative subtypes receive **1/15**. The cited excerpts do not establish equal weighting of VSI direction levels.
The metre-only proxy cannot justify assigning conversion rows zero value. No replacement benchmark price or defensible rank movement can be calculated from the permitted documents.
Ranks 1–3 also compare a ceiling with conditional gains. Under the fixed-forward scenario, counting’s **0.38754** narrowly exceeds direction’s **0.38717**: ranks 2 and 3 would swap by only **0.00037 ReVSI points**, far too little to support a substantive ordering.

**Missed finding**

At identical camera frames, **7/34** comparable VSTI pairs reverse shared-object ranks; all seven share identical frame plans. Their **11 wrong items** represent **4.00 v1 type points** and **3.33 v2 type points**, or **0.489 VSTI proxy points**. These are associated losses, not demonstrated recoverable gains. Three item IDs: `34bca0f96670188fc1e078d2`, `b09b58a2be875c7ea8e495fe`, `792db679fcd87aeb5c202455`.

**Limits:** I did not rerun the full direction vocabulary census; 73 names were recovered from 6,000 sampled rows. The alternative 3,000-row size sample and the exact 488/517 counting classifier were not independently validated. Causal training effects, dev RGB visibility, and benchmark unit distributions remain unverified. No files changed.

## CLASSIFIER
```python
import sys,json,re,sqlite3,random,statistics as S,itertools as I,collections as C,resource
resource.setrlimit(resource.RLIMIT_AS,(3*1024**3,3*1024**3))
sys.path.insert(0,'/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
D={s:K.direct('R1',200,s) for s in ('dev-S1','R0-dev')}
th=lambda r:r['text'].split('</think>')[0]
aw=[r for r in D['R0-dev'] if r['type'].startswith('object_rel_direction') and r['subtype']=='away']
nt=[r for r in aw if th(r).startswith('Step 1: find') and 'left and right swap' not in th(r)]
print('1. away/omit/wrong:',len(aw),len(nt),sum(r['score']<1 for r in nt))
P='/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/'
F=json.load(open(P+'FAMILY_INDEX_RANGES.json'))['families']
db=sqlite3.connect('file:'+P+'vqa/rows.sqlite?mode=ro',uri=True)
def sample(f,n,seed):
    ids=sorted(random.Random(seed).sample([i for a,b in F[f] for i in range(a,b+1)],n))
    for j in range(0,n,200):
        b=ids[j:j+200]
        for raw, in db.execute('SELECT row FROM rows WHERE i IN ('+','.join('?'*len(b))+')',b): yield json.loads(raw)
vr=[r for f in F if f.startswith(('camera_obj_rel_dist','obj_obj_relative_pos')) for r in sample(f,200,77)]
print('2. zero-share rows:',sum(any(v==0 for v in r['provenance']['frame_n_share'].values()) for r in vr),len(vr))
def obj(t): return re.search(r'(?:find|locate) (?:the )?([^,.\n]+)',t,re.I)[1].strip().lower()
def unit(q):
    q=q.lower();return 1 if 'centimet' in q else 2.54 if 'inch' in q else 30.48 if 'feet' in q or 'foot' in q else 100
def mra(p,g): return sum(abs(p-g)/g<=1-t/100+1e-12 for t in range(50,100,5))/10
cl=C.defaultdict(list)
for r in sample('object_size_estimation',5000,9):cl[obj(r['target'])].append(float(r['answer'])*unit(r['student_input']['question']))
sz=[r for r in D['dev-S1'] if r['type']=='object_size_estimation' and len(cl.get(obj(r['text']),[]))>=5]
bp=S.mean(mra(S.median(cl[obj(r['text'])])/unit(r['question']),float(r['gt'])) for r in sz)*100
mp=S.mean(mra(float(r['pred']),float(r['gt'])) for r in sz)*100
print('3. matched size n/baseline/model/gain:',len(sz),bp,mp,mp-bp)
for s in D:
    rr=[r for r in D[s] if r['type']=='object_counting'];old={r['id']:r for r in K.direct('S1',544,s,types=['object_counting'])}
    gg=[rr] if s=='dev-S1' else [[r for r in rr if r['subtype']==v] for v in ('single','multiple')]
    gain=S.mean(100*sum(old[r['id']]['score']-r['score'] for r in g if r['forced_close'])/len(g) for g in gg)/(8 if s=='dev-S1' else 7)
    print('4. return-to-base benchmark proxy:',s,gain)
V=[r for r in K.vsti('R1',200) if r['type'].startswith('camera_obj_rel_dist')]
def rank(r):return re.search(r'objects are (.+?)\.\s*So',th(r),re.S)[1].split(', then ')
groups=C.defaultdict(list)
for r in V:groups[(r['room'],re.search(r'frame (\d+)',r['question'])[1])].append(r)
total=bad=0;wrong=set()
for rr in groups.values():
    for x,y in I.combinations(rr,2):
        a,b=rank(x),rank(y);shared=set(a)&set(b)
        if len(shared)<2:continue
        total+=1
        if [v for v in a if v in shared]!=[v for v in b if v in shared]:
            bad+=1;wrong.update(r['id'] for r in (x,y) if r['score']<1)
print('5. same-frame rank conflicts/pairs/wrong items:',bad,total,len(wrong))
db.close()
```