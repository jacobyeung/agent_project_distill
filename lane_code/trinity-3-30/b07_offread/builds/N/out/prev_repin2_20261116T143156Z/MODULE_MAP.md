The shared read driver belongs under `tools/orchkit/reader/`. Offkit continues to own binding, frame guards, record states, aggregation, labels, and report rendering. The accepted evaluator owns scoring, and b04 owns the end-to-end core.

| Build N modules | Shared destination | Responsibility |
|---|---|---|
| `cli`, `worker`, `bootstrap` | `reader/read.py` and launcher integration | Bind a read, execute ordered phases, gate official decoding, and authenticate completion. |
| `readers`, `c8`, `production`, `freeze` | `reader/readers.py` and `reader/context.py` | Build the native context, apply pinned policy weights, and call the existing reader cores. |
| `staging`, `stage_plan` | `reader/staging.py` | Compose and invoke R's reviewed stage/export gates. |
| `proposals` | `reader/proposals.py` | Run the frozen proposal programs and bind native C8r cache receipts. |
| `frames`, `source`, `media`, `cohort` | `reader/frames.py` and `reader/cohort.py` | Bind frame/source choices and construct question-only inventories. |
| `proof`, `historical`, `replay` | `reader/proof.py` | Select fixed historical items, restore the original context, and check decode and query identities. |
| `transport`, `portable`, `watchdog` | Shared pack/return/watch modules | Pack opaque bytes, preserve deadlines, and reuse governed transfers. |
| `scoring`, `reporting` | `reader/scoring.py` and `reader/reporting.py` | Adapt records without copying scorer or reporting rules. |
| `fixture`, `native_fixture`, `cache_fixture`, `rehearse`, `census` | `tests/` | Supply explicit synthetic boundaries and executed-line evidence. |
| `paths`, `io`, `package`, `vendor`, `admission` | Shared utility, pins, and admission modules | Resolve staged roots, pin files, enforce input checks, and assemble deliverables. |

The `read_config.frames` dictionary is the `frames` dictionary returned by `offkit.bind.bind`. `read_config.g3t` binds source, frame count, report qualification, and any mapping identity. The packed worker receives a minimal read specification and binding digest; the operator's full `BINDING.json` stays local.

`portable.py` supplies relative dependency roots and a pin inventory. Both readers' CPU fixtures pass from isolated source bundles with the pinned offkit package supplied externally. Offkit is not copied into the bundle. The production runtime uses R's staged namespace and still requires a complete production-CONFIG rehearsal. This build does not claim that its build-local input manifest is already the final shared orchkit pin/config integration.
