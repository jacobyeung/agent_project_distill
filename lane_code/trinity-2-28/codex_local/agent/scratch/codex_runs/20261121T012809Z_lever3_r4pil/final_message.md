Fixed and validated.

- Cause: `PIL._typing` executes an unconditional `_IntegralLike` import at [PIL/_typing.py:8](/scratch/jjyeung/orch_n30/lever1_c/r4kit/tmp/pinned/m/ap/19252904/e/lib/python3.12/site-packages/PIL/_typing.py:8). Production PIL avoids this typing-only helper.
- Real pinned-environment CPU replay passed: **3,228 imports, 14.9 seconds, zero bulk bytes**, no package doubles.
- Closure: CPU **3,338 → 3,228**; GPU **3,341 → 3,231**. All **110 drops** have [individual reasons](/scratch/jjyeung/orch_n30/lever1_c/r4kit/tests/pinned_exclusions.json).
- Failure reports preserve the entry and full exception. **All 45 tests passed**, including the regression.
- New token: **`87f4ae5c2f44f`**; `f68a2d7c903be` is superseded.
- Delivery: [out/delivery.tgz](/scratch/jjyeung/orch_n30/lever1_c/r4kit/out/delivery.tgz), **4,309,485 bytes**.

SHA-256: `3998032470651ac870851f39990f638ead7efc6647e2a9c607508ecbe1400cbd`

All four delivery documents agree. `FROZEN.json` is unchanged; workspace: **36.67 GB**.