The Trinity runner provides stage, frames, need, proof, and read subcommands with operator commands in README.md.
The implementation leaves kit_src and the existing step-544 export unchanged.
Tests: 33 passed; see TESTS.log. No GPU, network, SSH, or Git command ran.
System Python 3.6.8 passed CLI/bootstrap checks and the frame-store test; pytest used the kit Python 3.12.13 environment.
CPU dry-bind checks used the accepted runtime source and kit dependency fakes for all three families.
Main-first-20 produced exactly 576 hashes, byte-identical to work/NEED20.txt; see NEED20.fixture.txt.
Full-set planning covered 1,525 main, 150 away, and 150 forward items; see PLANNING_CHECK.json.
The retained Orchard packet compared identically for all 20 items in each arm; actual/accepted means were 0.65/0.65.
That comparison checks the reporter against retained evidence; it is not a new Trinity token proof.
Real stage and real namespace need did not run: runtime_0.tar, runtime_1.tar, runtime_2.tar, base.tar, and frames20.tar were absent.
Those five inputs had zero-byte .part files; camera.tar and bwrap were present without completion receipts. See LOCAL_INPUTS.json.
DIFF BEYOND: piece completion/refusal and existing-export verification; append-only frame store; direct-only CPU planning and ID filter.
DIFF BEYOND: phase-B-only entry, single-card admission, token job identity, vnice wrapper, memory sampler, exact comparison, and disk reserve.
DIFF BEYOND: network/device isolation, packet/run admission, tests, and documentation; the source ledger lists every added line.
Reader settings and source bytes remain unchanged; no reduced-memory fallback exists.
OPEN: Ada capacity/token parity, staged runtime and host compatibility, bwrap namespace support, and real performance/peak memory need operator validation.
OPEN: staging and frame ingestion require the Trinity heavy-I/O approval; interrupted pieces or store indexes require manual review without automatic retries.
