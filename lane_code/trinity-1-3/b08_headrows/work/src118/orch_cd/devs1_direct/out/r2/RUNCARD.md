Both cells are frozen at 1,525 items: 1,375 primary and 150 unavailable routes. The 11 unlabeled rooms are excluded and listed. The label policy permits both cells to bind; real frame and model authentication remain run-host checks. The separate training release-text check is **NO**: relative-distance agreement is 89.2%, with 324 sampled object-name changes. Read `LABEL_AGREEMENT.md` before deciding on the training launch.

The CPU delivery uses these local paths:

```bash
L=/scratch/jjyeung/orch_cd/devs1_direct
P=$L/out/r2
CPU=/scratch/jjyeung/envs/p1cpu/bin/python
CPKIT=$L/work/dry_release_cp1/kit
F17KIT=$L/work/dry_release_f17/kit
FRAMES=/scratch/jjyeung/devs1_frames
```

Validate the delivered CPU payload:

```bash
$CPU -I -s "$P/test_adapter.py"
```

The suite uses `work/r2/dry_release_cp1` and `work/r2/dry_release_f17`. Its temporary fixtures stay in `work/r2` and are not deleted. `TESTS.md` records coverage and results. The item list, tasks, strata, cells, and provenance have SHA256 files; `SHA256SUMS` covers the delivery.

Dry-bind an adopted evaluator kit in a fresh destination. Set `CPKIT` and `F17KIT` to the intended kit copies first:

```bash
$CPU -I -s "$P/adapter.py" bind --dry --cell cp1m200 --kit "$CPKIT" --models "$P/MODELS.reference.json" --frames-root "$FRAMES" --dest "$L/work/r2/operator_dry_cp1"
$CPU -I -s "$P/adapter.py" bind --dry --cell f17 --kit "$F17KIT" --models "$P/MODELS.reference.json" --frames-root "$FRAMES" --dest "$L/work/r2/operator_dry_f17"
```

Dry binds stop before PNG bytes and cannot launch. Both must report 1,525 tasks, zero blocking missing canonical labels, and 150 unavailable released labels. Both prompt inventories must match. Existing bind destinations are not overwritten.

For the operator's separately authorized run, stage the pinned PNG tree and model assets on the compute host. Create `work/r2/MODELS.runhost.json` by changing paths in `MODELS.reference.json` while retaining all model hashes. The CP1 artifact hash is `c1a4258816b3f561c9891f74cc1138780900de5cd890320161d2c94c85a86f67`; the f17 archive hash is `47308d99246bdf253a5d55ce9ec04a38a4fcc355092603a51e8de34604749eae`.

After the operator authorizes the production frame reads, live-bind both cells:

```bash
$CPU -I -s "$P/adapter.py" bind --cell cp1m200 --kit "$CPKIT" --models "$L/work/r2/MODELS.runhost.json" --frames-root "$FRAMES" --dest "$L/work/r2/run_cp1"
$CPU -I -s "$P/adapter.py" bind --cell f17 --kit "$F17KIT" --models "$L/work/r2/MODELS.runhost.json" --frames-root "$FRAMES" --dest "$L/work/r2/run_f17"
```

Live binding verifies PNG existence, byte hashes, dimensions, pixel hashes, and exact frame order. It hard-links frames on the same filesystem. The kit uses 32 duplicate anchors for CP1 and 32 spread anchors for f17, greedy thinking, and a 16,384-token cap. CP1's kit derives B2048 and B4096 with its existing continuation protocol. PLAN fps remains an identity placeholder.

The operator then uses the kit-compatible GPU interpreter and one assigned card to invoke `adapter.py launch --dest ... --attempt ...` for each binding. The required engine version is vLLM 0.32.0. Run the cells sequentially, preserve ON and budget journals, and stop if a job is killed. This CPU task neither allocates a GPU nor launches inference.

After both runs finish, produce the report with the actual attempt names:

```bash
$CPU -I -s "$P/report.py" report --cp1 "$L/work/r2/run_cp1" --f17 "$L/work/r2/run_f17" --cp1-attempt devs1_cp1_a1 --f17-attempt devs1_f17_a1 --output "$L/work/r2/report_devS1" --replicates 10000
```

`REPORT.json` preserves three views: primary, disagreement under each label, and unavailable. Released MC scores use the label mapped into the displayed option order. The unavailable view contains the 150 routes, reports their canonical scores, and leaves released scores null. The report compares CP1 B2048 and ON16k against f17 with paired physical-room bootstrap intervals. It refuses incomplete or conflicting journals, altered bindings, incorrect frame order, and failed kit parity.
