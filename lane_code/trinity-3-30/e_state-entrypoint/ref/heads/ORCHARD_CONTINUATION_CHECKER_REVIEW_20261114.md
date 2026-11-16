# Orchard continuation checker: containment, fixture and native loss compatibility

Updated 2026-11-14. Owner: orchard_cp2.

## Question and answer

Does the confirmed checker preserve containment and accept native loss metadata?

**The confirmed bundle is `026cb696`, binding `f544dd1b`; all 58 bound files verify.** The executable diff is confined to `loss_alarm.py:normalize()`. The containment, restore and state-comparison code, binding resource fields and loss-alarm policy are unchanged. The resource record explicitly grants no new fixture submission.

**The two local refusal cases pass for the unchanged containment code.** A results parent equal to either the protected persistent root or the kit produces an overlap error, exits 1 and leaves no files or directories inside that test input. That receipt binds the fixture package `aee5221e`, binding `7b152ff2`.

**Orchard job 169409 passes the synthetic CPU fixture.** All four ranks match across 756 tensors at zero tolerance; all thirteen phases, the sampler plan and the read-only checks pass. Slurm reports exit 0:0 and 76 seconds elapsed. The profile uses eight CPUs, 32 GiB and no GPU.

These results cover startup containment and a synthetic CPU round trip, not a restored production checkpoint, CUDA, a resumed loss or an optimizer update. No real continuation check or production continuation is authorized.

**The secondary loss utility accepts the sealed producer's native representation.** The author's bound evidence records **42 passing unit tests** and a replay of **eight production rows, covering 32 rank records**. The independent receipt accepts the normalization diff against the sealed producer. Cp2 verified the bundle, diff and regression evidence without rerunning a fixture or executing the checker.

## Native loss-schema compatibility

The confirmed `loss_alarm.py` has SHA256 **02b45209d1c50ea778e109b89f8ff9e0bcaaec11399a59ce6e586afa950f53d2**. A row must contain a positive integer step and exactly ranks 0–3. Each rank must carry that same integer step, the exact stream set and finite numeric losses.

`skipped_microsteps` must be a list of `{microstep, stream}` objects. Microstep integers must increase strictly and streams must be known. `skip_totals` must contain nonnegative integer `skipped` and `total` counts, with `skipped <= total`; a listed event requires a nonzero skipped count. Physical skipped slices and cumulative nominal-group counters are distinct quantities.

The normalized event count is metadata only; no loss alarm, resume gate or threshold reads it. The independent reviewer checked that this representation matches the sealed producer's event ordering and counter updates. Its receipt has SHA256 **f6af6e497b980e3b38fe5108dd78c8b31aec2de352e3b97914838e65d7a79c88** and grants no job, fixture rerun or continuation.

The bound test logs report **31 loss tests, seven comparator tests and four sampler tests**, all passing. Cp2 verified the logs, their pinned test sources and the exact eight-row input against its own delivery. It also verified AST equality outside `normalize()` and byte equality of the loss policy. These are evidence checks, not a local rerun of those tests or proof of a production restore.

The review receipt is `out/CONTINUATION_LOSS_REVIEW_026cb696_20261114T094658Z/REVIEW.json`, SHA256 **cd020b9d747af14262b887a2532001b9f7f10ba2f3f13be44715c7c1200ea13b**. Production, the installed wrapper and the frozen stop contract are unchanged.

