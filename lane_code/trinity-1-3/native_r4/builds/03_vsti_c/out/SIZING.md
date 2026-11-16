These projections use the job-170056 rates supplied in the build brief. They are not measurements of this build.

| Phase | Projected seconds | Basis |
|---|---:|---|
| Staging and one load | about 1,800 | Supplied rate, excluding geometry |
| Tower | 1,181.8 | 311 scenes × 3.8; about 10 GB peak GPU memory |
| Checkpoint scale/gravity | 311 × g | g is unmeasured |
| Historical proof geometry | p × g | p distinct selected captures |
| Proof decode and repeat | 159.8–879.8 | Two repeats of 3 displacement, 3 direction and 4 rotation items; rotation assumed 10–100 seconds |
| Canary | 86.6–626.6 | 4 camera and 6 other items |
| Remaining camera items | 638.4 | 48 × 6.0 + 48 × 7.3 |
| Remaining other items | 3,440–34,400 | 344 × assumed 10–100 seconds |
| Additional restoration | L | Unmeasured; processes load separately |
| Return reserve | 600 | Scheduling allowance, not measured transfer time |

The subtotal excluding scale/gravity, proof, additional restoration and return is 7,146.8–38,646.8 seconds. A full first job is not promised under the 21,600-second GPU-phase cap. The fixed canary membership is recorded in `out/CANARY_KEYS.json` and checked against the complete input in `out/FULL_ADAPT.json`.

The canary projects remaining work using 1.25 times each type's maximum observed item-pair duration, with the inherited camera floors and 100 seconds for unseen other types. Deadline admission uses the maximum across all observed complete item pairs, with an initial 100-second floor. These serve different purposes: the first estimates remaining work; the second reserves room for a slow item to finish before merge.

`code/budget.py` sets the item-start cutoff to deadline − 600 − 1.25 × maximum item time. The outer wrapper kills the subprocess at deadline − 600. At the initial floor, those times differ by 125 seconds. `tests/test_v1c.py:test_s7_distinct_deadlines` checks the separation after a measured 200-second item. An unseen slower item can still exceed the margin; committed journals survive a timeout.

The 600-second return reserve exceeds the documented sequential channel timeout allowance of 540 seconds, but archive creation and transfers can vary. No Orchard return duration is certified here. Reporting runs later on Trinity, so the allocation's read phase finishes with merge and completion rather than a named report.

The build uses less than its 6 GB local limit; `out/FINAL_RESULT.json` records the final byte inventory. Real tower weights and runtime environments remain external read-only assets. The full adapted frame store is local to this build.

When the sealed GPU-phase cap expires before the absolute deadline, the wrapper passes an earlier effective deadline to the worker. The item-start margin is therefore preserved relative to either subprocess kill boundary.
