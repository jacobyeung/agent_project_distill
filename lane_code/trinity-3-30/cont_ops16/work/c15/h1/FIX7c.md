Cause: q.sh authenticated production k/0.json with the reconstructed build/fx pin (516d215e…/1663919), so production metadata refused; evidence/fix7_selection/orchard_q_run2.txt:12–13.
Change: tools/selection_stage.py:159 verifies SHA256SUMS.txt against the sealed production manifest before trusting its k/0.json line; :187 requires the complete package entry to equal the embedded expectation before extraction.
Manifest source: tools/derive_kit_h1.py:140,645 pins de6e7e0fac4036889fb4112792fbaa2d6f362a0cde09722ba6e93a6a39e7f32b; tools/package_selection.py:12 reads that authority.
Package source: tools/package_selection.py:6 verifies retained production metadata 620a7ed162cd2f9722724be13ef09bae4123b2aba70ea3147fcc25ce91eced83 / 1664013 bytes against orchard_q_run2.txt:12 before embedding source, bytes, sha256, members, inventory and destination.
Pin audit: evidence/fix7_selection/PIN_AUDIT7c.md and pin_audit7c.json cover every authority; all 38 inputs use production receipt/manifest pins, while H1 code uses upload pins and transport/output checks use generated digests.
Tests: all four test_fix7_*.py scripts PASS; retained production metadata and synthetic staging pass with fixture manifest authority; fixture/metadata mismatches and changes to each package field refuse; archive/member guards, mounts and 7 patch cases pass.
Build: deterministic and bash -n PASS; build/q.sh is 120584 bytes, SHA256 fe632d041de1ff6de0a65587381ddf6094fb597af8c250ed85c2adca2c056c18.
Output: BUN/q_91f06d2e/o/; q_7b62108a and q_c492e8d1 remain untouched, and existing outputs refuse.
Scope: local CPU only; no SSH, network, Orchard, GPU, Git or deletion. Production manifest acceptance and selection equality remain unverified on Orchard.
