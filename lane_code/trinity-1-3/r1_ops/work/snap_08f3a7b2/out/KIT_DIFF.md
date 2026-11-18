| Archive member | Before SHA256 | After SHA256 | Change |
|---|---|---|---|
| `p_05b8ac69.sh` | `4a304bfd2042c618ddb2bad4e33faaf429ba290480c2bde282149c10af9042db` | `0c065ddefb77dcfe864a3bb3d1f343d3b421d601ba34a0a71abfca43e88c31a5` | Verify trainer before audit import; isolated proof-tail rehearsal. |
| `s.sh` | `5f15c65f0cc1355330314300fe1f269accc642b953eccf7f42bde3851cd500f6` | `83d209076ba2d7502e4dc0dad0770e7509b46e48af8b72da0c71f061050c23dc` | Pinned C canary exception; unchanged PASS branch. |
| `sums.txt` | `ab08a74aef06e152804e5deedbc2ee8664d9a6bdd46974c68179bd33876a070f` | `1d2270924ef7a7397d8fcf9ecd61811b8bfce954929acb5288d4119a4f5e97ae` | Pin the changed script bytes. |

All 37 other archive members retain their bytes and modes. Derived kit: 3/105 members changed.

All derived runtime code, config, staged-input pins and resource authority retain their bytes and modes. The equality record binds a fresh local native-fixture receipt path/hash; SHA256SUMS binds that record, and ANON_OK binds the resulting fixture manifest. These three evidence changes do not change the staged archives or C identity.

ANON_OK.json: {"after": {"mode": "0o600", "sha256": "626d585c63f2d55db348deeb728dea8c30a8dcc65db39952a0d56e8a90c2c7df"}, "before": {"mode": "0o600", "sha256": "f5408fd9b3f1f87aa91316208bf2a09c3b2331f190dc1546e432c525dd354fd0"}}

SHA256SUMS.txt: {"after": {"mode": "0o600", "sha256": "6734189b2bc5bf997d84dbc9ef11480bca1dda6b5a347173585605766d244ac5"}, "before": {"mode": "0o600", "sha256": "fbe67275015226e2ae6b69cb113a32b8afa35db16548b5c896f27fb02a9eff4e"}}

k/selection_equality.json: {"after": {"mode": "0o600", "sha256": "d234bbe5e513552d0228734ac0e5238ff7ecc9839e44e36121936a9b2cd5b807"}, "before": {"mode": "0o600", "sha256": "54d77f55a3ff5914073226abed0c3c910548630eb5228c344c4d3e972313b8ac"}}
