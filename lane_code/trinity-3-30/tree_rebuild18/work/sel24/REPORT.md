UNATTRIBUTED — routing: ROUTE_direct, SCENE_room, T0_room, T1H1_room, U_Faithful in d1e6715a; VQA: relative_distance and raw-reference source split.
[Selection tables](SELECTION_TABLE.md) and [JSON](SELECTION_TABLE.json) cover all four configured streams, their pins, counts, types and named removal/scene rules.
All four moved-to-VQA sources are present after all current N removals: ROUTE_direct=8,562; SCENE_room=294; T0_room=65; T1H1_room=66.
The 109 named-route matches include two K1 matches, so d1454a44 removes 107 additional rows; N's room draw allocation remains zero pending its loader audit.
N's final native counts require Orchard preparation; the tables distinguish these from P receipts and historical list-only counts.
[rdiff.py](orchard/rdiff.py) and [wrapper usage](orchard/RDIFF_USAGE.md) are ready; all 14 synthetic tests passed with the tree's own schema and removal reader.
The production row diff was not run. It requires N's native DB and P's exact reconstructed 4e8e6c04 DB; job 173567's recorded reconstruction has a different hash.
[Provenance](PROVENANCE.md) traces d1e6715a to the inherited kit07 snapshot; its original producer build/lane/time remain UNATTRIBUTED.
Tree C's i.refresh changes only s1_routing.selection; no other stream pin comes from that function.
N's relative_distance card implies 19,827 versus 19,833 list-retained rows; the six-row gap remains UNATTRIBUTED.
