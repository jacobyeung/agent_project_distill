The shared reader driver belongs under `tools/orchkit/reader/`. The end-to-end reader core remains in b04. The following mapping keeps the worker focused on orchestration and preserves the imported scoring and binding owners.

| Build N module | Shared destination | Responsibility |
|---|---|---|
| `native_read.py`, `offnative/cli.py` | `tools/orchkit/reader/read.py` | The entry binds parameters and dispatches preparation, fetch, and report operations. |
| `offnative/worker.py` | `tools/orchkit/reader/read.py` | The driver executes phases, records failures, gates official decoding, and constructs arm journals. |
| `offnative/readers.py` | `tools/orchkit/reader/readers.py` | The interface delegates direct mode to build R, harness generation to C8r, and end-to-end generation to b04. |
| `offnative/staging.py` | `tools/orchkit/reader/staging.py` | The staging adapter imports the reviewed archive reader. |
| `offnative/frames.py` | `tools/orchkit/reader/frames.py` | The adapter uses the accepted evaluator sampler and layout function. |
| `offnative/cohort.py` | `tools/orchkit/reader/cohort.py` | The inventory exposes question fields, complete IDs, canary membership, and media requirements. |
| `offnative/scoring.py` | `tools/orchkit/reader/scoring.py` | The adapter passes unchanged model bytes to the official scorer and imports `offkit.adapt_native.unify`. |
| `offnative/reporting.py` | `tools/orchkit/reader/reporting.py` | The reporter imports offkit aggregation, cohort checks, labels, and rendering. |
| `offnative/proof.py`, `offnative/replay.py` | `tools/orchkit/reader/proof.py` | The proof code chooses fixed reference keys and checks the decode protocol. |
| `offnative/io.py`, `offnative/paths.py` | `tools/orchkit/util.py` and dependency injection | The shared integration should replace build-local ownership paths and reuse the common utility owner. |
| `offnative/fixture.py`, `offnative/rehearse.py`, `offnative/census.py` | `tools/orchkit/tests/` | The test helpers provide synthetic boundaries and execution evidence. |

The `read_config.frames` dict in `BINDING.json` comes directly from `offkit.frames.bind_frames`. Its count, layout, and override reason match the `orchkit-read-v1` frames form. The remaining required read-config fields are not assembled into a production packet in this build. That packet must bind export, item, scorer, comparison, and rule logical paths through the shared pin manifest.

The current dependency paths are absolute Trinity paths. The code tar is a review and handoff artifact, not a portable Orchard packet. The shared integration must replace those paths with staged, pinned roots. This limitation is enforced by the launcher's unconditional production refusal.
