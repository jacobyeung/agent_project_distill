Built rh2.sh and pr4.sh; both are standalone operator drivers. Copy only those two to the operator directory.
rh2 stages pinned startup inputs in its own allocation, invokes the sealed child, and preserves the normal rehearsal markers and receipts.
pr4 requires --hold and --waive-rehearsal SHA FILE, records the event and failed-receipt SHA values, and preserves the other proof guards.
All 44 local fixture checks pass. The real authority sealer, real kit inventory validator, Bash syntax, and shipped-text scan pass.
The existing canary wrapper accepts pr4 markers and a held general proof in stubs; the sealed gate retains every admission and GO requirement.
No sealed batch-script or stage-provenance check blocks child invocation. Live source availability and namespaces remain untested.
Refusal points include occupied rename targets, existing attempts, queue conflicts, bad pins, invalid waivers, insufficient space, and uncertain submission output.
Staging reads about 10.04 GB plus two small startup files; estimate 2–5 minutes after allocation, with a 45-minute limit.
Packet archive SHA256 remains 08f3a7b2ef2e1923ba77b464afcedbbe668a77a1915b4c32c0a815044ff7d9fd.
Only c5 received writes. CPU only; no SSH, Orchard, Git, deletion, or GPU use. The workspace occupies less than 76 MB.
README_C5.md contains exact commands, source mappings, expected outputs, limits, and fallback conditions.
MANIFEST_C5.json records SHA256 for every other generated file and target-text SHA256 for symlinks, including retained fixtures.
The table authenticates the manifest. RESULT_C5.md cannot include its own SHA256; that digest is supplied in the final handoff.
Kept 172467 references because they identify the required evidence and no-replace destinations.

| New deliverable or support file | SHA256 |
|---|---|
| rh2.sh | `5f2ce861a740b79947dc1f67327a576cfbc5f741289a2c43591876e03cf458ca` |
| pr4.sh | `df1d17ef29a3bc50533370888296e3e372beb9826113486afbcc41f370051658` |
| rh2_job.sh | `884150e790e3f8dc27955d9b8f1341a3a2985bc414fc2b1662e4862dad40eadf` |
| rh2_stage.py | `b2ac7036494f98b32399aa5526f46cd63b8c8a2451c3bd4edac0e658270b1e40` |
| build_c5.py | `4f81823987ce25cabff899c9515435541beb5ff1ab0090dc66c24f63081c0d5b` |
| test_c5.py | `bbdd88c6178caecb45c198af4ec30d477b54ec712a9bbc23880b2410dd724dce` |
| test_stage_c5.py | `f819b92c2a3a8924ac05ee177653d4244d9d03b133f63613f16e021978fe8b83` |
| README_C5.md | `515e0206c8cd1d75fe45c6c4a429ab59451c510ec144d5d1afe9df3e87c40c1b` |
| test_c5.out | `060376a7cdbb062e1f712a876637dcfa91780d07a8e714fd3359ac7dd92ae1db` |
| test_stage_c5.out | `08d76a8c9ac1edaebe8374ac043ccd23e6ec892dc9b5d98db74ba8dd9a895158` |
| sealer_fixture.json | `b0bbc36fc5cc184a721f0e409eb7b3285e9ae3250aa27d8d614fa1bafbc6b7a1` |
| inventory_check.json | `b4acc8e2c5035d22a0c843df7401cd234a5a233697fc0662404e3717b36be800` |
| VALIDATION_C5.json | `415e7f8918b275c4f31736ad3b2f7cbfab8bde9e779f1d6248aeab8da6888305` |
| MANIFEST_C5.json | `274ba09e9727981f5a07480181ad6d81c599ad474be79d4e006f547b18fa9954` |
