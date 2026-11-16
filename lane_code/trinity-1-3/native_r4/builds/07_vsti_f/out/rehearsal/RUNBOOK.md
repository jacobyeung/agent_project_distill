Run the CPU namespace rehearsal outside the Codex sandbox on trinity-1-3:

```bash
cd /scratch/jjyeung/orch_n30/native_r4/builds/07_vsti_f
./work/py out/rehearsal/run_rehearsal.py --fixture-tower
```

The harness uses explicit host bwrap, private shared memory, synthetic tower/head/token boundaries, and the production preparation, decoder, replay and report logic. The optional frame-index fixture is explicitly absent, matching V1c's inherited test conditions. The shared reference list now uses a different schema; this build does not change the production adapter.

The full 311-scene return-size rehearsal already ran on CPU. Its command is:

```bash
./work/py work/rehearse_return_f.py
./work/py work/verify_return_f.py
```

This creates a fresh local fixture and archive; it uses production-shape arrays and the actual return publisher with remote transport calls mocked. See out/RETURN_SIZE.json. No GPU, Orchard namespace, live return channel or remote deadline timing is certified.

Build the named report from an actual returned full archive with:

```bash
./work/py work/report_return.py --archive work/returned.tar.gz --root work/returned_report
```

A diagnostic minimal return may lack the prepared input manifests or MERGED needed for a report. A full return that omits scaled arrays remains reportable but does not contain those arrays for resume. Inspect INVENTORY.json before resuming.
