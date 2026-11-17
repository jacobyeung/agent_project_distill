The terminator pin is updated for token `b01ec87a6f29b`. Paths below are relative to `k330`.
The terminator SHA256 changed from `cbb91ba7455d15007bd3affeb358dc5693f3845949ee0abacf892a4402748b94` to `19727987d5517c0e2549e1205e55f4bcc87f34dafe66c96bdf90233305942e5d`.
Old `0.tgz`: `4847ad12194edae7f3d573baef4bff8120db89b4495e7e54bcf474d5caf90676`, 5,292,625 bytes.
New `0.tgz`: `ecfad90f13e75b7d5f978575b199ecd3b2fc77c7fefe7508688af111efb3100f`, 5,292,624 bytes.
Old plan SHA256: `b6440cf4665a4a7c6f70cbb11b769149df32da9257696966a2e4457152e920a0`.
New plan SHA256: `5ef2094e61aa2471244ce23c28cead29a9be5f7221fd6bdb5a2e520985a87c77`.
Old `PACKAGE.json` SHA256: `52165d5d67419176ab0a29c03d8521f3d352545b5cca41aeca0fc53c7547a370`.
New `PACKAGE.json` SHA256: `ba178d46c90325fb93c681b90fccaebe770f7a6c7fb05d12cd300691e4d88e1b`.

`PACKAGE.json` file hashes:

| File | Old SHA256 | New SHA256 |
|---|---|---|
| `0.json` | `594b15a26997e85a7b9916468360f314eb08a85a8488db558009eb9c55643794` | `244a4b395dc03fb214a6cbf3bf1e7acaad68f9239607b542d0f25c03d98e6c88` |
| `0.tgz` | `4847ad12194edae7f3d573baef4bff8120db89b4495e7e54bcf474d5caf90676` | `ecfad90f13e75b7d5f978575b199ecd3b2fc77c7fefe7508688af111efb3100f` |
| `3.py` | `a5c94551f263e30bc05579a40e84f1f146e9a67dc2e21c8834ed62bd680b73e0` | `a5c94551f263e30bc05579a40e84f1f146e9a67dc2e21c8834ed62bd680b73e0` |
| `BATCH.sh` | `9c25be9b0a1d99dede838ca1d2eeac14c70898c5b27a129230343f5c49f15376` | `09213517010bdfa178b6fe5ae6abe9b9a1890b540429bb5301414b35b0a3ee08` |
| `CONFIG.json` | `1cb25428614be9712d9393fc9eb74ee41bd84f67802ef0268fed429e44b80f38` | `c54dc5ffc77b0fcd2554b10a87e56ada20f9a63c34a6ebf0967c090241b8983e` |

The no-replacement self-test reproduced all eight original package files byte-for-byte, including the required archive hash and `PACKAGE.json`.
All 920 archive names match. Exactly `9.json` and `orchard_h10/vendor/ORCHARD_ASSETS.json` differ; the other 918 payload members are byte-identical.
The asset differs by one exact old-to-new terminator byte replacement. `9.json` differs only in that asset’s payload pin. All 919 payload pins verify; token and template pins are unchanged.
Canonical plan, `3.py` loading → `load_helpers` → `verify_config`, receipt hashes, public-file opacity, and shell syntax checks passed.
The prescribed full-suite command recorded 0 passed / 0 failed / 0 skipped / 4 collection errors: `test_build4`, `test_h10`, `test_cli`, and `test_eval` require missing B04 `tests/test_tiny_e2e.py`. No test bodies ran; see `kit/logs/t10/full.log`.
The focused package/opacity/process checks recorded 4 passed / 0 failed / 0 skipped; see `kit/logs/t10/package_checks.log`.
The original reviewer scripts recorded 2 passed / 4 failed / 0 skipped. `t_modes` and `t_modes_tilt` passed with `BAD []`.
`t_map` and `t_score` failed at B04 reader setup; `t_merge_types` lacks the external `h1_headsft` rehearsal journal; `t_cached_modes` lacks external `h1_headsft/kit/items/devs1_routed.json`. These node fixture failures were not repaired.
Every probe used `bash cpu.sh`; the tilt probe received `tests/t_modes.py`. The harness redirected only the two hard-coded scratch destinations into `kit/tmp/t10/reviewer`; test files were not edited. Commands and per-probe logs are in `kit/logs/t10/reviewer_results.json`.
No test hard-coded the old package or plan digest, so no test-pin edits were needed. `TOKENS.json` and the transport source copy are byte-unchanged.

The changed package files are `kit/orchard_h10/package/0.tgz`, `kit/orchard_h10/package/0.json`, `kit/orchard_h10/package/CONFIG.json`, `kit/orchard_h10/package/BATCH.sh`, and `kit/orchard_h10/package/PACKAGE.json`.
The rebuild also re-emitted byte-identical `kit/orchard_h10/package/3.py`, `kit/orchard_h10/package/SUBMIT.cmd`, and `kit/orchard_h10/package/INPUTS.example.json`.
The new source/report files are `kit/orchard_h10/repin_terminator.py` and `REPORT_terminator.md`.
The backup directory `kit/orchard_h10/package_cbb91ba7/` contains exact copies of `0.tgz`, `0.json`, `CONFIG.json`, `BATCH.sh`, `PACKAGE.json`, `3.py`, `SUBMIT.cmd`, and `INPUTS.example.json`.
All generated proof, harness, scratch, and log files are listed individually in [the exact file inventory](kit/logs/t10/changed_files.json); no other existing files changed.
The rebuild entry point is `LANE_TEST_OUTPUT="$PWD/tmp/t10" bash cpu.sh -m orchard_h10.repin_terminator` from `kit`; it refuses to overwrite an existing backup or proof directory.

**Operator submit PATH fix**
New `0.tgz`: `5f9898505dd3e0857d8b97bf24336a783a2dddc0c240c3fa5dbfc0dd9ac84e3c`, 5,292,659 bytes.
Plan SHA256: `1f506aafcdd09ccbe7a9f0b80d871bea9c3a5d81df3973782e691c461a410823`.
`PACKAGE.json` SHA256: `512c5c7b5f27b4cdee1259159bcc757dc876432b47b79c6d34e5e052f41e8fd5`; its five file hashes follow.
`0.json`: `4981735262b44c63b69f8d6b28ba7c9a44c1f853ab3ba9cfc7dc54c4969e5058`.
`0.tgz`: `5f9898505dd3e0857d8b97bf24336a783a2dddc0c240c3fa5dbfc0dd9ac84e3c`.
`3.py`: `a5c94551f263e30bc05579a40e84f1f146e9a67dc2e21c8834ed62bd680b73e0`.
`BATCH.sh`: `f756457a36d0e4128491ee01fed631dd429e7792b93b914b8452b0bf2955fad0`.
`CONFIG.json`: `2e986133202a088ce8a3ecc2b360abe84b9236e9d68a271be3d86578a9092a51`.
The no-change rebuild reproduces all eight files. Both source and `8.py` contain exactly one PATH replacement and match byte-for-byte; compilation, load_helpers, verify_config, canonical plan, receipt hashes, opacity, bootstrap and shell syntax pass.
The archive has 920 members: only `8.py` and `9.json` differ, leaving 918 byte-identical members; all 919 payload pins verify. `9.json` changes only `payload_pins['8.py']`; the terminator and template pins remain unchanged.
The four package checks returned 3 passed / 1 failed / 0 skipped: `test_package_pins_and_embedded_bootstrap` expects archived `orchard_h10/operator.py` to match the edited source, but that member remains byte-identical as instructed. Its later bootstrap assertions pass independently. Tests were not edited.
Changed files: `kit/orchard_h10/operator.py`, new `kit/orchard_h10/repin_operator.py`, `kit/orchard_h10/package/{0.tgz,0.json,CONFIG.json,BATCH.sh,PACKAGE.json}`, and `REPORT_terminator.md`. The other three package files reproduce unchanged; `TOKENS.json` remains unchanged.
The exact eight-file backup is `kit/orchard_h10/package_ecfad90f/`. Proofs are in `kit/tmp/t11/repin/`; logs are in `kit/logs/t11/`. See [the exact file inventory](kit/logs/t11/changed_files.json) and [package checks](kit/logs/t11/package_checks.log).

The consistent operator package has `0.tgz` SHA256 `2dd91b3b3476c3e9d01370d4956c5b1edfbee6e870671b5c3ed52f5e13fcfa82` and 5,292,645 bytes.
Plan SHA256: `8b89141f9e2728487d3d874ade2451394e43f979d88aaaa96ca19bb856634817`.
`PACKAGE.json` SHA256: `e37b3d07943436fb49322d66feb46bdca98f4a29725e266124cb51fb247acbab`; its five file hashes are the `0.tgz` hash above and the four below.
`0.json` SHA256: `f3688b2cf3d95946897447c079f71768bf798a7c6771a7c0bc4605aa40407fff`.
`3.py` SHA256: `a5c94551f263e30bc05579a40e84f1f146e9a67dc2e21c8834ed62bd680b73e0`.
`BATCH.sh` SHA256: `45684d3659f779443295381cf98ea92a317166ac6c4a8316d8051a3bcc019b9f`.
`CONFIG.json` SHA256: `2d1cfdf0c80fabafbe49ec5cf13d403bca18dd5b37d6d61755eed73974f8bcbc`.
All eight files reproduce in the no-change self-test; 918 members remain byte-identical. Both operator members match the source; `9.json` differs only in `payload_pins['orchard_h10/operator.py']`. All 919 pins, load_helpers, verify_config, opacity, compilation, and receipt hashes pass.
The four package checks pass (4 passed, 0 failed, 0 skipped); see `kit/logs/t12/package_checks.log`. The eight-file backup is `kit/orchard_h10/package_5f989850/`; rebuild: `kit/orchard_h10/repin_operator_member.py`; proof: `kit/tmp/t12/repin/verification.json`.

The namespace bind fix has `0.tgz` SHA256 `e82ac3295fe0ae83cb62f08a62f63017dc55fbfdf828211db10575bb49feea96` and 5,292,661 bytes.
Plan SHA256: `1de19b86d81f2bf9a5b254270e61496e45d454893fe893cbbd325739f74764c8`.
`PACKAGE.json` SHA256: `27b287a9ef2952436ad1cdc54bc0ba00a9076c48638c9da605feb4eba862601f`; its five file hashes are the `0.tgz` hash above and the four below.
`0.json` SHA256: `80dfa7df26075330756ea4052b78d1491cb9bd69e0a233e1475b409941748eba`.
`3.py` SHA256: `a5c94551f263e30bc05579a40e84f1f146e9a67dc2e21c8834ed62bd680b73e0`.
`BATCH.sh` SHA256: `231f278b5f843a92e61f946e9c5965a5f835ee442c13cf78cf9fe0a389caea55`.
`CONFIG.json` SHA256: `3a766c4e3489c9ca02d618dd9f94eebbc93047733e4d25cbba8354a2ad7bd696`.
The one-line fix matches source and payload. All eight files reproduce in the no-change self-test; 918 members remain byte-identical. `9.json` changes only `payload_pins['orchard_h10/job.py']`; all 919 pins, canonical plan, load_helpers via `3.py`, verify_config, compilation, receipt hashes, and opacity pass.
The four package checks pass (4 passed). The focused bind-source test fails on both unfixed source and payload because `fsw` is absent (2 expected failures), and passes on both fixed versions (2 passed); its fixture includes runtime group 0's Python directory. Logs: `kit/logs/t13/{package_checks,fsw_old,fsw_new}.log`.
The eight-file backup is `kit/orchard_h10/package_2dd91b3b/`; rebuild: `kit/orchard_h10/repin_fsw.py`; test: `kit/tests/test_fsw_bind.py`; proof: `kit/tmp/t13/repin/verification.json`. Token, template pins, and all other payload bytes remain unchanged.
