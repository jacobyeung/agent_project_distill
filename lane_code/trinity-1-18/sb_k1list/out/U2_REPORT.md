Vehicle N: u2 contains 2322 additional K1 rows; u contains 2637; their union contains 4959.
All 4,959 audit K1 identities and every marginal/joint count were reproduced from the pinned 204,413-row store.
Identity: row_key = store qid; ordering: ascending row_key; keys: canonical, reason, row_key; reason: k1_heldout_v7.
Schema constraint: u.json is headerless JSON Lines. Both outputs preserve it; U2_METADATA.json records all input SHA-256 hashes and binds each output hash.
Overlap: u subset of audit K1 = True; u outside K1 = 0; u/u2 intersection = 0; union equals audit K1 = True.
u rows outside K1, with scenes: none.
Count columns below are audit / u / u2 / union. MISSING denotes a missing row.pool field, not missing proof.

| Stream | Counts | Family | Counts |
|---|---|---|---|
| MISSING | 69 / 0 / 69 / 69 | box_3d | 69 / 0 / 69 / 69 |
| dose_route_direct | 225 / 136 / 89 / 225 | obj_appearance_order | 336 / 0 / 336 / 336 |
| r1g | 430 / 0 / 430 / 430 | object_counting | 277 / 22 / 255 / 277 |
| rows_rebuild_d0_ARKIT_gaps | 262 / 262 / 0 / 262 | object_rel_direction_easy | 950 / 646 / 304 / 950 |
| rows_rebuild_d0_ARKIT_gen_r2 | 354 / 354 / 0 / 354 | object_rel_direction_hard | 1185 / 801 / 384 / 1185 |
| rows_rebuild_d0_T0_gaps | 32 / 0 / 32 / 32 | object_rel_direction_medium | 891 / 608 / 283 / 891 |
| rows_rebuild_d0_T0_gen_r2 | 46 / 0 / 46 / 46 | object_rel_distance | 832 / 424 / 408 / 832 |
| rows_rebuild_d0_T1H1_gaps | 59 / 0 / 59 / 59 | object_size_estimation | 194 / 0 / 194 / 194 |
| rows_rebuild_d0_T1H1_gen_r2 | 80 / 0 / 80 / 80 | route_planning | 225 / 136 / 89 / 225 |
| rows_rebuild_d0_T1H2_gaps | 76 / 0 / 76 / 76 |  |  |
| rows_rebuild_d0_T1H2_gen_r2 | 94 / 0 / 94 / 94 |  |  |
| w1g | 3232 / 1885 / 1347 / 3232 |  |  |

Proof tiers (audit / u / u2 / union): A: 110 / 0 / 110 / 110; B: 4770 / 2558 / 2212 / 4770; C: 79 / 79 / 0 / 79.
Audit archive SHA-256: `c7743a8b0c282b6aafd89b4b00bd41a29dba8735390f1f6947a2076ff4dd08ea` (verified).
Store SHA-256: `210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443` (verified).
K1 source SHA-256: `4d4736cf64e496a184d36d74d710e76d1673429e28790613794867ac077048a9` (verified).
u SHA-256: `43853165f921d077eab92baaf83f29a69cd4f3efef789249bb8db99893853cf6` (verified).
u2 SHA-256: `d2fd6208d7df49ab872b9536a1748d80c392f91a59135b099bc0bc38fff13a8f`.
Union SHA-256: `1c7c930d1a533a3b18b08486bc2c2a9b49086b0809492963498b369ac8be45a2`.
All counts, overlaps, identity/schema/order checks and input hashes: `/usr/bin/python3 out/build_lists.py`.
Package: `tar --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner --exclude=out/sb_k1list.tar --exclude=out/sb_k1list.tar.sha256 -cf out/sb_k1list.tar out`.
Archive digest: `sha256sum out/sb_k1list.tar > out/sb_k1list.tar.sha256`; verify: `sha256sum -c out/sb_k1list.tar.sha256`.
Archive excludes itself and its checksum sidecar. Borderline historical wording retained: none.
