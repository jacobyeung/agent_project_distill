The package omitted all **26 tower vendor files**, causing the source-pin rejection at [tower_read.py:172](/scratch/jjyeung/orch_n30/lever1_c/r1/inspect/p/tree/student_pilot/tower_read.py:172). I reproduced it on CPU. It is the most likely remote failure; the missing traceback prevents certainty. [DEBUG.md](/scratch/jjyeung/orch_n30/lever1_c/r1/DEBUG.md) inventories every TowerError/E98/E99 site.

Fixed opaque source retention, original source hashing, and dynamic imports. The CPU rehearsal now checks them. Failures retain packed tracebacks bounded to 200 lines inside authenticated returns.

**Passed:** 32 CPU tests, two import checks, actual rehearsal deny-list scans, and a capture through real geometry code with CPU neural doubles. GPU numerics remain untested.

- Token: `a784b94c2e6af`
- [Delivery](/scratch/jjyeung/orch_n30/lever1_c/r1/out/delivery.tgz): **3,522,551 bytes**
- SHA256: `b7b0148bb78b2d7ac49a64dd1dfc264cf70ee122c4781293abe35c8235095302`

`PLACE.md`, `REPORT.md`, and `BUILD.json` agree.