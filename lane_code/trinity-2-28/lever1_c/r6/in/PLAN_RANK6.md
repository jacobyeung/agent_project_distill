### 6. LEDGER: CPU re-analysis of existing captures
- Question: do the 11-20 results split by dataset, what does a no-information constant score beside 58.6, and does the routed answer beat the direct one on the R0-dev twins?
- Changes: nothing is rerun. ARKit against ScanNet/ScanNet++ split of T2, the 64-frame arm and the T1 stages; a per-class constant gap on the 150; the twin ledger at steps 200 and 400, metres first, feet apart.
- Set: 150 dev items; 290 template items and their twins.
- Reading: routed minus direct >= 0 at both steps and no gate above always-route by 2: the route table stays (distance routed with the "not seen" fallback, camera routed, room direct). Below -3 at step 400: one forced-direct diagnostic read of 20 min. A Codex review of the parser is spent only on those two triggers. Dataset splits stay hypotheses until fresh items confirm them.
- Points, cost, gates: about 0.7 ReVSI rides on the route decision. CPU minutes on about 25 MB. Gates fallback rows.

