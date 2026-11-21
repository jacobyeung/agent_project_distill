C″ has seal `de202f58b31793608f886360a9fdfb5f58c24932e35976efcf74acead62e3cfe` and 945 files, computed by the tree's own `source_seal.inventory` and `p3_provenance.digest`.

C′ has seal `4648e6b3e66c1c08db091dc3104455d6011000fb9d961aa1f78eee03e38ec43d`. The exact Cursor test patch has SHA256 `ff3c78fe5d84ca68688c2dee5fc4970ee7b20525bc5dd8858f7ec2b7179ebd28`; it applies without fuzz or offsets. Only `tests/test_host24j.py` differs from C′. The fixture uses null pixel fields and explicitly tests refusal of non-null legacy pixel fields.

The four differences from tree C (`0c7614c8eff74201db275489af9c3fa11f3b418693a0239b793e6322685298de`) are `launch_r1/entry.py`, `student_pilot/carrier_c1_run.py`, `tests/test_host24j.py` and `tests/test_r1_processor_compat.py`. The original processor patch has SHA256 `a0d9cef403712f2636ac4a1eb8d72eedd7251df7ed95cb1c0ef8d377bb5d8762`. No other tree file changed.

The native host suite passes 15/15, including its untouched-tree comparison; processor compatibility passes 3/3. There are no skips or errors in the final runs. `work/build24m4m/TREE_TESTS.json` records results; `TREE_CPRIME.json` records the inventory and `TREE_DIFF.patch` records the sole change from C′. The untouched comparison tree is available at `work/tree_r1_base`.

Each kit changes exactly nine tree-dependent files: its archive, `k/7.json`, `k/c0.json`, `k/p.json`, `k/c.json`, `k/n.json`, `k/a.json`, `SHA256SUMS.txt` and `BUILD.json`. `EXACT_KIT_DELTA.json` verifies all other decoded fields and files are unchanged; `DEPENDENT_PINS.json` and `PIN_AUDIT.json` verify the dependent identities and archives. The runtime source record is `u/92493d10ec22cc089aac5bbd98a45f4e6d39ac271bd4970488b4831c016247b9`.

The independent review's verdict is GO AFTER FIXES; its required fixture edit and recommended refusal test are both applied. These CPU fixtures do not establish production-row equivalence or a real processor/GPU forward pass.
