From the build directory, run the audit and CPU namespace rehearsal:

```bash
cd /scratch/jjyeung/orch_n30/native_r4/builds/08_vsti_g
./work/py work/path_audit.py
./work/py -m unittest discover -s tests -v
./work/py work/adapt_legacy.py
./work/py work/legacy_extra.py
./work/py out/rehearsal/run_rehearsal.py --fixture-tower
```

The rehearsal recomputes the real-metadata audit before attempting bwrap and inside the namespace. Any unbound required path aborts the run. The missing-snapshot regression test confirms that the processor path fails without the added mount. The model snapshot bind comes directly from the production binding code, rather than the synthetic fixture.

Inspect PATH_AUDIT.json for exact files, directory coverage, physical sources and read-only targets. The audit authenticates the locally available metadata/model archives and step-544 artifact. The local inputs lack the full-weights/index and depth-head metadata payloads; exact payload-selected filenames, GPU loading and runtime opens require the real staged job.

The CPU pipeline uses synthetic tower/head/token boundaries and the production geometry, decoder, replay and report logic. The optional frame-index fixture is explicitly absent, as in the inherited tests. This does not alter production inputs.

In the Codex sandbox, bwrap exits with a NETLINK_ROUTE permission error. The harness records this in NAMESPACE.json and executes the CPU pipeline without a namespace. RESULT.json therefore reports CPU success and namespace unavailability separately. Run the command outside that sandbox to check namespace creation; this build does not certify an Orchard mount or a real checkpoint load.
