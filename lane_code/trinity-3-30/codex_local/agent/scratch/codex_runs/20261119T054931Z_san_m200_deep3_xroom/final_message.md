**Question and answer**

1. **Do scores cluster by room after controlling for type?** Yes for R0-dev and VSTI: step-200 room variance exceeds the shuffle mean by 78% across 98 rooms and 58% across 68 rooms, respectively; both permutation p-values are ≤.002. Neither dev-S1 direct nor routed items show this effect.
2. **Do different types agree about difficult rooms, and do difficulties persist across checkpoints?** Agreement across types is weak. Same-type room scores persist strongly on R0-dev: correlations range from .57 to .76 for the four types with enough items per room.
3. **Where do lost points concentrate?** Half of the priced loss sits in 36 of 98 R0-dev rooms, 14 of 73 dev-S1 rooms, and 9 of 58 routed rooms. The ten worst R0-dev rooms score below their type means on 3/3, 6/7, 7/7, 6/7, 7/7, 6/7, 5/5, 5/7, 6/7 and 5/7 available types.
4. **Do duration, spacing, fps, object names or item count explain the room effect?** R0-dev duration has a modest negative association with score: Spearman ρ=−.228, p=.024, across 98 rooms. VSTI duration does not; its ρ=.144, p=.242, across 68 rooms.
5. **Do routed failures identify rooms that also fail direct questions?** No positive association appears. Routed distance versus direct relative distance gives r=−.27 across 11 eligible rooms; versus object size, r=−.14 across 12.
6. **What distinguishes the lowest and highest 20 R0-dev rooms?** Hard direction separates them most: .158 on 38 items versus .842 on 38. Object size separates them least: .570 on 60 items versus .724 on 59.
7. **What should vehicle N change?** Test additional frames on frozen room groups before changing heads. The worst fifth contains 8.36 ReVSI proxy points on R0-dev and 8.22 points under the specified dev-S1 arithmetic; these are loss ceilings, not predicted gains.

**Evidence**

Scores below are fractions, with numeric types scored by MRA. A room’s standardized score is its item-average of `score − mean(score for that type)`. Variances weight rooms equally. Tests shuffle scores within type 1,000 times, preserve room/type counts, use seed 42, and report `(1 + exceedances)/1001`. Correlations and bands use step 200; rank calculations round residuals to 12 decimals to preserve ties. P-values are exploratory and unadjusted.
Sources are the files selected by [san_kit.py](/scratch/jjyeung/orch_n30/swarm_an/kit/san_kit.py): `h1read` builds `adff67f7ae9`, `a5d2d909067`, `a8102c3207b`; `h1vsti` builds `acb2faedd41`, `a35f73e87f0`; `h1face/a2e46c0504e`; the step-544 `e193/merged` B2048 returns; and routed `out3/A4/ret` and `out3s/bases/b1` returns. Direct results use B2048; routed results use the loader’s G3T scoring. No official benchmark items were used.
Type abbreviations are A=appearance, C=counting, E/M/H=direction easy/medium/hard, D=relative distance, S=object size, RC=relative count, RS=relative size, P=route planning; CD/CM/CR=camera displacement/movement direction/rotation, AD=absolute distance, Room=room size. V1/V2/V3 and LR/NF/UD retain the VSTI type suffixes.
Per-step type counts are R0-dev A246/C385/E192/H192/M194/D279/S293; dev-S1 has 150 per type except RC139; VSTI has 150 per type; twins have 50 per level; routed has 150 per type except Room36. I excluded the 186 additional distance/room items returned by the step-544 direct dev-S1 loader, leaving the same 1,339 direct items at every checkpoint.

| Set, step; items/rooms | All-type observed variance / shuffle mean / p | Each type: observed / shuffle / p |
|---|---|---|
| R0, 544; 1781/98 | .02000/.01168/.001 | A .10316/.08359/.038; C .05411/.04984/.240; E .11621/.11176/.437; H .15451/.12352/.013; M .12876/.12454/.446; D .07495/.07548/.563; S .04981/.04343/.111 |
| R0, 100; 1781/98 | .01654/.01131/.002 | A .08771/.08254/.323; C .05519/.05326/.378; E .08854/.09341/.794; H .13184/.11265/.076; M .10022/.10623/.779; D .07803/.07621/.450; S .04321/.04434/.589 |
| R0, 200; 1781/98 | .01988/.01119/.001 | A .08942/.08002/.187; C .06001/.05148/.094; E .08200/.08361/.676; H .14754/.12129/.025; M .10910/.11322/.698; D .06685/.07243/.759; S .04490/.04409/.426 |
| dev-S1, 544; 1339/73 | .01933/.02078/.571 | C .08713/.09531/.756; E .02770/.03025/.446; H .05819/.05243/.329; M .04264/.04075/.408; D .09382/.07573/.134; S .08930/.05891/.001; RC .13985/.10033/.007; RS .02001/.04304/.915; P .08476/.06711/.156 |
| dev-S1, 100; 1339/73 | .02252/.02137/.355 | C .08681/.10215/.910; E .03132/.02810/.359; H .04802/.06740/.876; M .04429/.04555/.466; D .11225/.08200/.025; S .08287/.05507/.006; RC .11735/.09716/.142; RS .06828/.05444/.213; P .08726/.06188/.063 |
| dev-S1, 200; 1339/73 | .02045/.02166/.572 | C .09838/.10193/.637; E .03156/.02373/.265; H .04544/.05663/.738; M .06191/.04574/.237; D .09488/.07220/.110; S .09039/.06179/.004; RC .11027/.09702/.252; RS .04895/.04876/.503; P .07894/.06273/.187 |
| VSTI, 544; 900/68 | .02690/.01767/.003 | V1 .08110/.08393/.604; V2 .10240/.09928/.398; V3 .12838/.11427/.174; LR .12857/.11382/.149; NF .11109/.11539/.599; UD .09854/.10991/.768 |
| VSTI, 200; 900/68 | .02584/.01638/.002 | V1 .09248/.10672/.862; V2 .13560/.10693/.018; V3 .13516/.11092/.048; LR .11433/.09666/.080; NF .11752/.10794/.237; UD .05762/.06492/.789 |
| Away, 544; 150/33 | .05727/.05193/.331 | E .13388/.15031/.786; H .02000/.03615/.627; M .10562/.09617/.332 |
| Away, 200; 150/33 | .07143/.03888/.045 | E .04873/.03608/.372; H .10571/.09266/.304; M .03109/.05410/.722 |
| Forward, 544; 150/33 | .01066/.02010/.670 | E .00998/.01266/.497; H .02371/.04637/.734; M .00895/.03347/.966 |
| Forward, 200; 150/33 | .04417/.02604/.107 | E .03993/.01227/.195; H .07403/.07558/.472; M .00691/.02232/.842 |
| Routed, 544; 636/58 | .04691/.04358/.349 | CD .04500/.02611/.050; CM .04243/.01679/.019; CR .03585/.04428/.728; AD .09230/.09314/.518; Room .03198/.02335/.151 |
| Routed, 200; 636/58 | .04251/.04440/.619 | CD .04359/.02660/.066; CM .04243/.01679/.019; CR .03194/.04364/.814; AD .10911/.09365/.087; Room .03404/.01851/.065 |

The following Pearson correlations require at least three items of each type in a room. Each entry is `eligible rooms / r / p`; “constant” means that a correlation cannot be estimated. Same-type comparisons use matching room groups at steps 544 and 200.

| Set | Cross-type correlations at step 200 | Same type, 544 versus 200 |
|---|---|---|
| R0 | A–C 80/.12/.283; A–D 81/−.07/.550; A–S 81/−.12/.272; C–D 92/−.10/.356; C–S 96/.14/.190; D–S 93/.11/.289. All 15 pairs involving E, M or H have zero eligible rooms. | A 81/.58/<.001; C 97/.57/<.001; D 93/.69/<.001; S 97/.76/<.001. E/M/H each have zero eligible rooms. |
| dev-S1 | C–E 7/−.03/.954; C–H 8/.40/.331; C–M 7/−.26/.570; C–D 13/−.07/.826; C–S 8/.26/.540; C–RC 12/.22/.494; C–RS 12/.47/.125; C–P 6/−.58/.226; E–H 15/.78/.001; E–M 17/.70/.002; E–D 13/.21/.484; E–S 12/−.02/.957; E–RC 5/.36/.547; E–RS 11/−.55/.077; E–P 11/−.00/.998; H–M 14/.32/.273; H–D 12/.08/.797; H–S 13/.08/.805; H–RC 4/.20/.800; H–RS 9/−.33/.392; H–P 12/.01/.987; M–D 12/−.01/.963; M–S 11/.47/.142; M–RC 2/undefined; M–RS 10/−.57/.084; M–P 12/−.13/.681; D–S 9/−.16/.687; D–RC 10/−.36/.303; D–RS 11/−.07/.831; D–P 13/−.34/.254; S–RC 4/.20/.803; S–RS 11/.08/.808; S–P 10/.37/.287; RC–RS 7/.11/.822; RC–P 4/−.76/.242; RS–P 8/.52/.189 | C 23/.72/<.001; E 22/.72/<.001; H 22/.93/<.001; M 19/.49/.035; D 25/.59/.002; S 26/.83/<.001; RC 16/.32/.221; RS 24/.41/.046; P 25/.53/.006 |
| VSTI | V1–V2 6/.57/.234; V1–V3 4/.30/.698; V1–LR 6/−.63/.178; V1–NF 4/−.52/.478; V1–UD 6/.70/.121; V2–V3 5/−.08/.898; V2–LR 4/constant; V2–NF 6/−.87/.026; V2–UD 4/.33/.667; V3–LR 3/constant; V3–NF 4/.82/.184; V3–UD 1/undefined; LR–NF 5/−.00/1.000; LR–UD 4/1.00/<.001; NF–UD 3/−.50/.667 | V1 22/.37/.091; V2 16/−.18/.500; V3 14/−.04/.897; LR 14/.60/.024; NF 14/.02/.939; UD 16/−.09/.733 |
| Away | E–H 3/constant; E–M 3/−.50/.667; H–M 2/undefined | E 6/−.52/.292; H 6/.31/.548; M 8/−.54/.165 |
| Forward | E–H 3/constant; E–M 3/constant; H–M 2/undefined | E 6/constant; H 6/1.00/<.001; M 8/.81/.016 |
| Routed | CD–CM 19/.08/.747; CD–CR 20/.42/.067; CD–AD 9/.17/.654; CD–Room 5/.32/.595; CM–CR 22/.37/.092; CM–AD 9/−.80/.010; CM–Room 5/constant; CR–AD 9/−.27/.486; CR–Room 5/−.77/.131; AD–Room 1/undefined | CD 26/.99/<.001; CM 27/1.00/<.001; CR 27/.99/<.001; AD 17/.32/.203; Room 5/−.53/.364 |

All 636 routed items match direct room IDs through unique room suffixes. Routed type score versus the direct standardized room mean gives CD 26/−.02/.912, CM 27/−.15/.453, CR 27/.12/.540, AD 17/−.26/.321 and Room 5/−.14/.825. AD versus D gives 11/−.27/.415; AD versus S gives 12/−.14/.671. These measure final task scores, not isolated head-response correctness.
R0’s pooled effect survives subtype-stratified shuffles: .01998 observed versus .01109 shuffled, p=.001 on 1,781 items. Removing all 84 forced-close items leaves .01911 versus .01140, p=.001 on 1,697 items. Pooling direction levels permits supplementary correlations with A: 81/.29/.010; C: 95/.20/.053; D: 93/.15/.153; S: 96/−.10/.315. Across the 68 shared R0/VSTI rooms, standardized room scores correlate only .04, p=.736.

The worst fifth means the lowest standardized room means, rounded up to whole rooms. “Half-loss rooms” ranks rooms separately by accumulated loss. ReVSI pricing uses subtype weights and assigns medium direction zero weight. dev-S1/routed contributions follow the requested `/8` arithmetic; they are not complete benchmark scores. VSTI has no supplied benchmark conversion, so its six-type macro points are labeled separately.

| Set | Rooms holding half the raw / priced loss | Worst fifth: rooms; items; imperfect items | Lost score units in fifth / all | Priced loss in fifth |
|---|---|---|---|---|
| R0 | 35/98; 36/98 | 20/98; 360/1781; 235/360 | 207.3/674.3 | 8.359 ReVSI proxy points |
| dev-S1 | 14/73; 14/73 | 15/73; 289/1339; 132/289 | 114.1/298.4 | 8.222 specified `/8` points |
| VSTI | 24/68; 24/68 | 14/68; 179/900; 115/179 | 115/375 | 12.778 six-type dev macro points |
| Away | 3/33; 3/33 | 7/33; 24/150; 13/24 | 13/17 | 8.667 direction-task points; 1.083 VSI proxy points |
| Forward | 2/33; 2/33 | 7/33; 28/150; 10/28 | 10/10 | 6.667 direction-task points; .833 VSI proxy points |
| Routed | 12/58; 9/58 | 12/58; 69/636; 47/69 | 37.6/157.3 | 3.133 specified `/8` points |

Worst-fifth **type-point costs**, with item denominators given above, are R0 A13.008/C13.117/E10.417/H16.667/M12.371/D8.244/S8.805; dev-S1 C16.133/E4.667/H8.000/M4.667/D9.333/S9.267/RC17.266/RS4.000/P4.000; VSTI V1 16.667/V2 14.667/V3 12.667/LR10.000/NF14.000/UD8.667; Away E4/H16/M6; Forward E2/H14/M4; routed CD3.467/CM1.333/CR4.267/AD16/Room0.
Counting runaways remain a separately priced known mode: R0 has 83/385 items, 75.2 lost units, 19.532 counting-type points and 2.644 ReVSI points; dev-S1 has 28/150 items, 26.8 lost units, 17.867 counting-type points and 2.233 VSI proxy points. The worst-fifth loss after removing every forced-close item is still 7.570 R0 points on 335 items and 6.496 dev-S1 points on 253 items.

Each worst-room entry below is `room: item count / mean score / duration seconds @ fps`, in standardized-score order. Duration is the sampled video span; dev-S1 and twin entries use the median across that room’s items. Routed timing is inherited from matched direct rooms and is therefore a proxy.

| Set | Ten worst rooms |
|---|---|
| R0 | a9287874d5c17709c2474fd9: 9/.267/304.1@60; 05fd7f365c53d1b40a843342: 19/.321/246.1@60; d3772c127f875f3babdce00d: 19/.342/157.6@60; e9b0ab84a96777d2669da78c: 19/.347/704.7@60; 969d5a2ec50718f071164d01: 19/.363/159.3@60; 16f8a0388c771f96fa6b7603: 19/.384/262.8@60; 599da252bbcf726eeaafa11d: 13/.377/106.6@60; af2e8226a34f622c3916b5bd: 19/.411/101.2@60; 223194fe78766709dbf4042a: 19/.426/188.2@60; 0e4aa362496c1a2f198e34b2: 19/.432/77.2@60 |
| dev-S1 | d1/scene0687: 3/.267/45.1@24; d1/scene0250: 12/.508/135.3@24; d1/scene0475: 7/.400/38.2@24; d2/0c7962bd64: 14/.564/79.5@60; d3/venue383973: 34/.509/245.2@10; d1/scene0401: 8/.562/101.5@24; d3/venue472621: 22/.655/55.0@10; d2/ca3b651c23: 61/.569/229.9@60; d3/venue434911: 5/.600/50.4@10; d2/e35232b92f: 27/.719/205.8@60 |
| VSTI | 467e967b7363fc8b6933c6d8: 13/.154/171.9@60; 8bfe057055ddb8556e3ce2da: 6/.333/178.1@60; 16f8a0388c771f96fa6b7603: 13/.308/262.8@60; 52422ab4e6932aafe88057c3: 13/.308/133.0@60; c06052db36d773b487a4b41c: 12/.333/502.0@60; 0ad34f18c8c81eff3aa54b30: 14/.357/120.3@60; 969d5a2ec50718f071164d01: 14/.357/159.3@60; fdf388fffa8d1698b1b5fc4b: 15/.400/272.6@60; d3772c127f875f3babdce00d: 13/.385/157.6@60; b3aa9ba18677351ca8de5138: 13/.385/106.2@60 |
| Away | d2/80ffca8a48: 1/0/137.4@60; d3/venue383973: 1/0/293.1@10; d3/venue472621: 4/.250/53.6@10; d2/d6bb698875: 8/.500/213.5@60; d1/scene0261: 2/.500/98.0@24; d3/venue382318: 5/.600/116.7@10; d2/6a217fbcb0: 3/.667/140.8@60; d3/venue435364: 3/.667/58.0@10; d1/scene0380: 8/.875/37.1@24; d1/scene0515: 13/.923/96.8@24 |
| Forward | d2/80ffca8a48: 1/0/137.4@60; d3/venue472621: 4/.250/53.6@10; d2/d6bb698875: 8/.625/213.5@60; d3/venue435364: 3/.667/58.0@10; d3/venue382318: 5/.800/116.7@10; d2/e667e09fe6: 6/.833/224.8@60; d3/venue423308: 1/1/143.1@10; d3/venue437168: 1/1/198.3@10; d1/scene0666: 3/1/71.4@24; d2/6a217fbcb0: 3/1/140.8@60 |
| Routed | d2/38fcf02d0b: 1/0/197.7@60; d3/venue382645: 1/0/141.4@10; d3/venue468781: 1/0/58.7@10; d3/venue382147: 2/.100/106.7@10; d2/623c973c56: 13/.538/385.5@60; d3/venue423308: 6/.217/143.1@10; d3/venue402848: 2/.250/68.5@10; d1/scene0666: 6/.500/71.4@24; d2/ca3b651c23: 23/.457/229.9@60; d2/21c5ee0ca5: 11/.700/245.9@60 |

For the covariates below, `range: rooms/items/mean standardized score` describes each band. Bands preserve tied values; consequently some are unequal. Duration and spacing have identical rank correlations because spacing equals duration/31; divide each duration-band boundary by 31 for spacing in seconds. Object-name counts come from complete question-template extraction for R0/VSTI and a longest-match question lexicon for the other sets; the latter are proxies, not annotated inventories.

| Set; rooms | Duration: ρ,p; three bands | Fps: ρ,p; bands | Distinct names: ρ,p; three bands | Item count: ρ,p; three bands |
|---|---|---|---|---|
| R0; 98 | −.228,.024; 61.0–120.35:33/582/+.020; 120.45–178.05:32/590/+.033; 180.13–704.73:33/609/−.048 | Constant 60:98/1781/+.001; three distinct bands impossible | −.024,.816; 6–20:34/572/+.014; 21–28:31/585/−.016; 29–44:33/624/+.004 | −.068,.506; 6–13:5/54/−.037; 14–18:15/245/+.042; 19:78/1482/−.004 |
| dev-S1; 73 | −.114,.338; 27–76.54:25/273/+.034; 79.52–141.4:24/471/+.045; 143.1–385.52:24/595/−.008 | −.252,.031; 10:32/409/+.082; 24:14/304/−.071; 60:27/626/+.004 | −.244,.038; 1–5:31/223/+.067; 6–11:18/374/−.028; 12–27:24/742/+.006 | −.237,.043; 1–9:27/127/+.074; 10–24:24/420/−.011; 25–89:22/792/+.001 |
| VSTI; 68 | .144,.242; 73.18–138:23/306/−.037; 140.58–189.22:22/283/−.014; 189.85–502.03:23/311/+.043 | Constant 60:68/900/−.002; three distinct bands impossible | −.130,.292; 2–10:23/297/+.007; 11–15:25/331/+.016; 16–21:20/272/−.037 | .033,.788; 6–13:41/505/−.014; 14:12/168/+.007; 15–16:15/227/+.021 |
| Away; 33 | .120,.507; 37.13–97.98:11/55/−.038; 112.2–191.45:11/43/−.058; 194.78–370.82:11/52/−.016 | .147,.415; 10:13/38/−.072; 24:5/27/−.032; 60:15/85/−.010 | .088,.626; 3–4:17/41/−.085; 5–6:8/52/−.016; 7–14:8/57/+.042 | .039,.828; 1–3:14/26/−.100; 4–5:8/36/−.029; 6–13:11/88/+.036 |
| Forward; 33 | .044,.807; 37.13–97.98:11/55/−.017; 112.2–191.45:11/43/−.050; 194.78–370.82:11/52/+.025 | .051,.779; 10:13/38/−.024; 24:5/27/+.061; 60:15/85/−.031 | −.002,.991; 3–4:17/41/−.041; 5–6:8/52/+.030; 7–14:8/57/−.001 | −.012,.948; 1–3:14/26/−.013; 4–5:8/36/−.051; 6–13:11/88/+.011 |
| Routed; 58 | −.221,.096; 34.17–97.75:20/211/−.005; 99–168.93:19/216/+.042; 174.2–385.52:19/209/−.049 | −.115,.391; 10:19/47/+.013; 24:14/291/+.003; 60:25/298/−.021 | −.018,.895; 0–2:31/287/−.012; 3–4:15/136/+.017; 5–14:12/213/−.010 | −.029,.826; 1–5:20/40/+.000; 6–12:19/170/−.005; 13–51:19/426/−.007 |

dev-S1 prefix scores below are `mean/item count`. Prefix and fps are confounded. Also, 37 of 73 direct dev-S1 rooms have different video lengths across their items; the largest within-room spacing difference is 6.24 seconds. All 98 R0 rooms and all 68 VSTI rooms have consistent timing within each set.

| Prefix | Overall | C | E | H | M | D | S | RC | RS | P |
|---|---|---|---|---|---|---|---|---|---|---|
| d1 | .752/304 | .498/53 | .946/37 | .929/28 | .913/23 | .707/41 | .566/32 | .676/34 | .927/41 | .800/15 |
| d2 | .771/626 | .584/50 | .931/72 | .811/74 | .874/87 | .747/91 | .650/42 | .632/76 | .918/49 | .729/85 |
| d3 | .806/409 | .615/47 | .927/41 | .792/48 | .875/40 | .722/18 | .772/76 | .655/29 | .867/60 | .940/50 |

The 20 lowest and 20 highest R0 rooms follow. Both score vectors use **A,C,E,H,M,D,S** order; each cell is `score/item count`, and “—” means absent. The highest group is listed best first.

| Low room | Low scores | High room | High scores |
|---|---|---|---|
| a9287874d5c17709c2474fd9 | —,.53/4,—,—,0/2,—,.10/3 | 29601e4b247f4f400e3f5544 | —,.85/4,—,—,—,—,1/2 |
| 05fd7f365c53d1b40a843342 | .67/3,.40/4,0/2,0/2,.50/2,.33/3,.17/3 | 5f5449c6661595320478bacd | 1/3,.78/4,1/2,1/2,1/2,1/3,.90/3 |
| d3772c127f875f3babdce00d | .33/3,.48/4,.50/2,0/2,0/2,.33/3,.53/3 | 2a29012aad5ea26d5650656a | .67/3,1/1,1/2,1/2,1/2,1/3,.80/3 |
| e9b0ab84a96777d2669da78c | .33/3,.25/4,1/2,0/2,0/2,.33/3,.53/3 | 926fca128c0f452a361cdb5c | 1/3,.85/4,1/2,.50/2,1/2,1/3,.70/3 |
| 969d5a2ec50718f071164d01 | 0/3,.35/4,.50/2,0/2,.50/2,.67/3,.50/3 | 1489d04ba06c1ef8a05df3ae | 1/3,1/3,1/2,.50/2,1/2,.67/3,.77/3 |
| 16f8a0388c771f96fa6b7603 | 0/3,.53/4,.50/2,0/2,0/2,.67/3,.73/3 | acc12914017b41fe62d7bfdb | 1/3,.85/4,.50/2,1/2,1/2,.67/3,.87/3 |
| 599da252bbcf726eeaafa11d | —,.35/4,.50/2,0/2,.50/2,—,.50/3 | 600c17330ea857a0d3f6c49c | .67/3,1/4,1/2,1/2,1/2,.67/3,.67/3 |
| af2e8226a34f622c3916b5bd | 1/3,.38/4,1/2,0/2,.50/2,0/3,.10/3 | 16fec6e5e0a69b11db341fb8 | 1/3,.90/4,1/2,.50/2,.50/2,1/3,.70/3 |
| 223194fe78766709dbf4042a | .33/3,.25/4,.50/2,.50/2,0/2,.67/3,.70/3 | d1d02a951cbb00631995d2d0 | .67/3,.68/4,1/2,1/2,1/2,1/3,.63/3 |
| 0e4aa362496c1a2f198e34b2 | 0/3,.38/4,.50/2,0/2,0/2,1/3,.90/3 | 50cc09d6c3213400fb04da08 | —,.65/4,1/2,1/2,1/2,.67/3,.77/3 |
| 52422ab4e6932aafe88057c3 | 0/3,.53/4,0/2,0/2,.50/2,1/3,.73/3 | 86d95d2dbc3ff3f196db6137 | .33/3,.85/4,1/2,1/2,.50/2,1/3,.93/3 |
| f93c5312bc2f3080b0898840 | —,.03/4,.50/2,.50/2,1/2,.33/3,.67/3 | ec3ea16c8befdc4ad1c4ac26 | —,.67/3,1/2,1/2,.50/2,1/3,.67/3 |
| e67eca1c1410abd9d1a22e9e | 0/3,.60/4,.50/2,0/2,1/2,.67/3,.43/3 | 532d5f15e53473fd41de5460 | 1/3,.50/4,.50/2,1/2,1/2,1/3,.60/3 |
| 55cc9808bb74f109d1325a31 | 1/2,.35/4,.50/2,0/2,.50/2,.67/3,.30/3 | 8bfe057055ddb8556e3ce2da | 1/3,.85/4,1/2,.50/2,1/2,.67/3,.43/3 |
| 77877d71e08e3f33d4f35585 | .67/3,.25/4,.50/2,0/2,.50/2,.33/3,.93/3 | c0e9fe3daf574bcd67ab39f7 | .67/3,.30/4,1/2,1/2,1/2,1/3,.80/3 |
| d1d05dfea9ef2dcc357cd5f4 | .67/3,.25/4,.50/2,.50/2,0/2,.67/3,.70/3 | 632365136e8177f64f60bd42 | .67/3,.45/4,1/2,1/2,1/2,1/3,.57/3 |
| 38ddb32f73688e5fe691df14 | .67/3,0/4,.50/2,.50/2,.50/2,.67/3,.73/3 | be5826f02f8c99aac1dbda57 | —,.72/4,1/2,.50/2,.50/2,1/3,.70/3 |
| 21c5ab83b048ff1f1265633b | .33/3,.60/4,.50/2,0/2,.50/2,.67/3,.67/3 | df1068c54ae80d735d4ec2ef | 1/3,.78/4,1/2,.50/2,1/2,.33/3,.70/3 |
| 8b2a12be9f9c14698ff12f4c | .33/3,.40/4,.50/2,.50/2,1/2,.33/3,.60/3 | d5020c7e9b33297f78847c24 | 1/3,.53/4,1/2,1/2,.50/2,.67/3,.70/3 |
| ee9827913a76b9d92e11d177 | 0/3,.50/4,0/2,.50/2,.50/2,1/3,.87/3 | 2a153dcba50b4f55a6d7c6e0 | .67/3,.53/4,1/2,1/2,1/2,.67/3,.67/3 |

The low-group aggregates are A .360/50, C .369/80, E .474/38, H .158/38, M .400/40, D .574/54, S .570/60. The high-group aggregates are A .833/48, C .723/75, E .947/38, H .842/38, M .868/38, D .842/57, S .724/59. These groups were selected by their scores, so their separation is descriptive, not independent evidence of a common cause.

Three complete traces come from room `05fd7f365c53d1b40a843342`, whose 19 items score .321. These are the loader’s full ON16k texts; all three have `forced_close=False`, and the reported answers and zero scores are B2048.
**Size — `3251cbd6acffd7288ec92ac2`.** Question: “What is the length of the longest dimension (length, width, or height) of the mirror, measured in centimeters?” Truth: 18. Answer: 156.
```text
Step 1: find the mirror, first seen in the bathroom.
Step 2: the longest edge of the mirror is 156 cm.
</think>

156
```
**Direction — `946b5f78a9a5797f0f69003e`.** Question: “If I am standing by the refrigerator and facing away from the shower cubicle, is the bananas to my front-left, front-right, back-left, or back-right?\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).” Truth: C, front-right. Answer: A, back-right.
```text
Seen: refrigerator in frame 45; shower cubicle in frame 165; bananas in frame 85.
If I stood at the refrigerator facing the shower cubicle, the bananas would be in front of me, on my left.
The question has me face away from the shower cubicle. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So I find the bananas at my back-right.
</think>

A
```
**Appearance — `ae31ceb655afa19d77d825b0`.** Question: “What will be the first-time appearance order of the following categories in the video: cooking pot, laptop, office chair, refrigerator?” Truth: C, office chair/laptop/refrigerator/cooking pot. Answer: A, laptop/office chair/refrigerator/cooking pot.
```text
Step 1: find the first frame showing each object: cooking pot frame 14; laptop frame 1; office chair frame 6; refrigerator frame 10.
Step 2: order them by first appearance: laptop, office chair, refrigerator, cooking pot.
</think>

A
```
The direction trace applies the half-turn consistently to its stated premise, but that premise produces the wrong answer. Its three frame references exceed 32 and match none of that item’s sampled source indices. The appearance trace sorts its stated frames consistently but reverses the first two truth categories. Neither trace proves that the needed evidence was absent from the input.

**What this changes for vehicle N**

1. **First, isolate the input hypothesis; change zero training rows for this experiment.** Evaluate the same checkpoint with 32 versus 64 frames, retaining the original 32 frames within the 64 and keeping B2048 scoring fixed. Freeze the worst-fifth groups above and evaluate the remaining rooms too. The exposed ceilings are 235 imperfect R0 items carrying 8.359 points and 132 imperfect dev-S1 items carrying 8.222 points. **Hypothesis:** additional views recover some relational evidence; the data do not estimate how many. Measure paired point gains by type, duration band and frozen room group, plus frame-reference validity.
2. **Second, pilot 1,000 evidence-grounded training rows; this quantity is a proposed experiment, not an inferred optimum.** Add 250 each to `object_rel_direction_hard|w1g|rows_rebuild_d0_v1` and `object_rel_direction_hard|r1_away_opp|None`, and 500 to `obj_appearance_order|w1g|rows_rebuild_d0_v1`. These families retain 21,385, 2,182 and 13,622 rows respectively. Render from verified training-frame evidence, with actual sampled-frame numbering. Example wording: “Seen: S in sampled frame 4; F in sampled frame 12; Q in sampled frame 18. Standing at S facing F, Q is behind me, on my left. The question has me face away from F, so Q is in front of me, on my right.” The example is schematic. In the worst R0 fifth, A and H contain 64 wrong items with 3.115 combined ReVSI points; that is a candidate exposure ceiling. The pilot fails if references become valid without improving paired answers.
3. **Third, pilot 500 size rows with verified object-instance anchors.** Use `object_size_estimation|r1g|rows_rebuild_d0_v1`, which retains 9,778 rows. Example trace wording: “Seen: the requested mirror in sampled frame 12. I use that mirror’s longest visible edge and estimate its length in centimeters from the frames.” Put the answer after `</think>`; do not insert an unsupported measurement into the trace. **Hypothesis:** instance anchoring helps a subset of the 47/60 imperfect size items in the worst R0 fifth, whose loss is 8.805 size-type points or 1.258 ReVSI points. Failure means unchanged size MRA despite correct instance anchors.
Watch the three IDs quoted above in room `05fd7f365c53d1b40a843342` (246.1 seconds; 7.94-second spacing). Also watch appearance `51bf2a4467b917883af25094` and hard direction `673e0d733e8ca97a1db21c00` in `e9b0ab84a96777d2669da78c` (704.7 seconds; 22.73-second spacing). Keep `5f5449c6661595320478bacd` as a successful control, including hard-direction item `3d83a400b12b0192439f11ed`. Do not train on these dev items.
Family counts and examples came from [template counts](/scratch/jjyeung/orch_n30/dist_diag/work/q2/STORE_V7_TEMPLATE_COUNTS.json) and [20-row samples](/scratch/jjyeung/orch_n30/dist_diag/work/q2/STORE_V7_SAMPLES20.json). Proposed trace forms follow the [ruling’s Answer and facing sections](/data2/jjyeung/agent_project_data/distill_design/TRACE_RULING_20261115.md:9). None of the 20 sampled away-hard or 20 sampled appearance rows contained a frame reference above 32, so the quoted invalid reference does not establish a defective training template.

**Refuted**

The prompt’s room-versus-item dichotomy is too strong. R0 has a reproducible room effect, but its six estimable cross-type correlations all have |r|≤.14, and R0/VSTI agreement is only .04 across 68 shared rooms. Room-associated loss therefore does not establish a universal failure to perceive those rooms. The supplied counting-runaway observation also cannot explain the entire room effect: removing forced-close items leaves p=.001.

**Not established**

These scores do not establish missing visual evidence, head-only failure, or the benefit of 64 frames. A paired frame-count experiment with verified object visibility would settle those questions. Sparse cells limit cross-type tests; fps is confounded with dataset; dev-S1 name counts and routed timing are proxies. No coordinator line range or specific first-wave report was named for this assignment, so I did not read those records or claim to audit their conclusions. All analysis was read-only.

**Appendix — CLASSIFIER**

Run with `/scratch/jjyeung/envs/planner_local_v1/bin/python`. This reproduces the pooled room tests, priced concentration and worst-fifth losses; VSTI and twin outputs use their explicitly labeled task-macro units above.

```python
import os, sys, math
sys.dont_write_bytecode = True
os.environ['OPENBLAS_NUM_THREADS'] = os.environ['OMP_NUM_THREADS'] = '1'
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit')
import san_kit as K
import numpy as np
from collections import Counter, defaultdict
from scipy.stats import spearmanr

def test(rows):
    rooms = sorted({r['room'] for r in rows})
    ri = {q:i for i,q in enumerate(rooms)}
    g = np.array([ri[r['room']] for r in rows])
    n = np.bincount(g)
    y = np.array([r['score'] for r in rows], float)
    ix = [np.array([i for i,r in enumerate(rows) if r['type']==t])
          for t in sorted({r['type'] for r in rows})]
    for a in ix:
        y[a] -= y[a].mean()
    z = np.bincount(g, weights=y)/n
    observed = np.var(z)
    rng = np.random.default_rng(42)
    null = []
    for _ in range(1000):
        v = y.copy()
        for a in ix:
            v[a] = rng.permutation(y[a])
        null.append(np.var(np.bincount(g, weights=v)/n))
    return rooms, z, (observed, np.mean(null),
                     (1+sum(v>=observed for v in null))/1001)

def weight(r, s):
    t = r['type']
    if s == 'R0-dev':
        if t == 'object_rel_direction_medium':
            return 0
        return (0.25 if 'direction' in t else
                0.5 if t in ('object_counting','object_rel_distance') else 1)/7
    if s in ('dev-S1','routed'):
        return (1/3 if 'object_rel_direction_' in t else 1)/8
    return 1/(6 if s=='vsti' else 3)

for s in ('R0-dev','dev-S1','vsti','away','forward','routed'):
    rows = (K.direct('R1',200,s) if s in ('R0-dev','dev-S1') else
            K.vsti('R1',200) if s=='vsti' else
            K.routed(200) if s=='routed' else K.facing('R1',200,s))
    rooms,z,stat = test(rows)
    ordered = sorted(zip(rooms,z), key=lambda a:(round(a[1],12),a[0]))
    worst = {q for q,_ in ordered[:math.ceil(len(rooms)/5)]}
    leaf = lambda r: (r['type'],r['subtype']) if s=='R0-dev' else r['type']
    den = Counter(leaf(r) for r in rows)
    selected = [r for r in rows if r['room'] in worst]
    costs = defaultdict(float)
    for r in rows:
        costs[r['room']] += 100*(1-r['score'])*weight(r,s)/den[leaf(r)]
    total = sum(costs.values())
    cumulative = np.cumsum(sorted(costs.values(), reverse=True))
    half = next(i+1 for i,v in enumerate(cumulative) if v>=total/2)
    print(s, 'items/rooms',len(rows),len(rooms), 'variance/null/p',stat,
          'half-priced rooms',half, 'worst-fifth items',len(selected),
          'loss',sum(1-r['score'] for r in selected),
          'priced loss',sum(costs[q] for q in worst))
    if s == 'R0-dev':
        timing = K.timing('R1',200,s)
        dur = {r['room']:(timing[r['id']]['total_frames']-1) /
               timing[r['id']]['fps'] for r in rows}
        print('R0 duration Spearman',
              spearmanr(np.round([dur[q] for q in rooms],12),
                        np.round(z,12)))
```