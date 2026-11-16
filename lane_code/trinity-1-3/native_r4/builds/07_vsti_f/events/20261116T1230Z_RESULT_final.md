RESULT: V1f built and CPU-verified; no job submitted. Evidence: out/FINAL_RESULT.json.
Code SHA256 063e09f8e786080c61720825a5a5d8e1c5e48ea1e209a1e21ee3ba56763c4d68 (out/c.tar).
Family SHA256 c6ad8e73aa80de875ea90bc318821a51907cb0ce28c492ed79308b5b58924b71 (out/FAMILY.json).
Reference SHA256 9a1de8608ea0e75e2f2436259b81f0e991b2007002a59de11d85062e8384d08f (out/d.tar); byte-identical to V1c.
Tests: 67 kit + 30 inherited pass (out/TESTS.json; work/kit_verified.log).
CPU prepare return: 311 scenes; 117763898 expanded bytes; 94088926 archive bytes; 326 members (out/RETURN_SIZE.json).
Caps: 536870912 expanded bytes, 299983616 archive bytes, 10000 members; no scaled arrays omitted in the size rehearsal (out/RETURN_SIZE.json).
Token mismatch reproduced: digit-leading packet tokens failed before both channels; admission now matches existing packet tokens (out/TOKEN_REPRO.json).
Full return failures trigger a diagnostic return with both tracebacks, inventory, protected evidence and log tails (code/o.py; tests/test_v1f.py).
All four input tar roles reject hard links and symlinks before packet creation (tests/test_v1f.py).
Execution phase body, budgets, batch directives and all other code remain unchanged except inherited token admission (out/PACKAGE_VERIFY.json).
Diff and ranked diagnosis: out/DIFF_vs_V1c.patch; out/DIAGNOSIS.md. Operator namespace command: out/rehearsal/RUNBOOK.md.
Unique-file footprint 3359287691 bytes; allocated 1222656000 bytes, under 4000000000 (out/PACKAGE_VERIFY.json).
Unchecked: failed-job token/logs/disk, GPU/real weights, completed decoded-return size, Orchard namespace, live channels and return timing (out/FINAL_RESULT.json).
Physical failures can still prevent delivery; fixed caps cannot hold arbitrarily large protected journals (out/DIAGNOSIS.md).
