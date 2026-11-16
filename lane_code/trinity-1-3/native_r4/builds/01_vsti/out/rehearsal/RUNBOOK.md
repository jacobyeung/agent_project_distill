Nested bwrap was denied by the build sandbox; see `out/rehearsal/NAMESPACE.json`. The failure occurred while creating a network socket. No host shared-memory directory is bound.

The exact attempted namespace command is the `command` array in that file. To run the full CPU rehearsal outside the sandbox on the same compute node, use the same interpreter and overlays:

```bash
cd /scratch/jjyeung/orch_n30/native_r4/builds/01_vsti
./work/py out/rehearsal/run_rehearsal.py --inner --dest /scratch/jjyeung/orch_n30/native_r4/builds/01_vsti/work/rh_operator
```

Use a fresh destination. The script checks for the complete tower receipt. When present it attempts the real tower on CPU; otherwise it uses a pinned synthetic tower. Model loading, checkpoint depth/gravity predictions and sampled token logits remain CPU fixtures. Scale conversion, gravity guard, tool dispatch, error-response injection, replay, scoring, merge and reporting execute their production implementations.

The item source contains fewer sample-scene items than the brief states; `out/rehearsal/RESULT.json` and its bound input list record the actual membership. No synthetic benchmark item is added.

Unchecked: GPU restoration, prompt/pixel/cache parity, GPU generation and historical repeat equality. `out/UNEXECUTED.md` gives the executable-line census.

The command-line rehearsal is independently runnable with a fresh destination:

```bash
./work/py work/rehearse_cli.py work/rh_cli_operator
```

It executes adaptation, the integrated job, merge, report and official scorer checks through `entry.main`, with explicitly synthetic tower, checkpoint heads and token generation.

The build also runs the real tower separately when its receipt is present. After that run writes its raw receipt, this command reuses the unchanged real arrays with synthetic checkpoint heads and token generation:

```bash
./work/py work/rehearse_real.py work/rh_real_operator
```

That command writes a separate rehearsal receipt pointing at the original raw receipt. It does not run the tower again. Its mixed result remains labelled synthetic.
