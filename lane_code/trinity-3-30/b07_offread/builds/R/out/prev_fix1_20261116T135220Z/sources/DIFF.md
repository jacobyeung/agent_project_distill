# Changes against the accepted packages

The two tables cover every changed source line. The packet payloads, item inventories, step544 stager and scoring sources retain their accepted bytes. The new bootstrap checks authenticate the binding and require prompt parity before decoding. The D0 dispatcher stages media before the unchanged full checker needs its namespace bindings.

PATH/ENV identifies only return-path substitutions and the Trinity package prefix. BEYOND identifies every other addition or removal. The complete line text appears in `out/SOURCE_vsi.patch` and `out/SOURCE_revsi.patch`; `out/SOURCE_DIFF.json` records the ranges and hashes. The new `RUN.md`, test files and this diff document are BEYOND in their entirety. This document excludes its own text from the patch to avoid self-reference.

## VSI-Bench

| File | Accepted lines | Shipped lines | Class |
|---|---:|---:|---|
| The Trinity package prefix moves to `kit/vsi/`. | All paths. | All paths. | PATH/ENV |
| `launcher/export_stage.py` | None. | 1–224 | BEYOND |
| `launcher/gate.py` | None. | 1–120 | BEYOND |
| `launcher/orchard_job.py` | 188–188 | 188–191 | BEYOND |
| `launcher/orchard_job.py` | 197–197 | 200–200 | BEYOND |
| `launcher/orchard_job.py` | None. | 229–229 | BEYOND |
| `launcher/orchard_launcher.py` | 23–23 | 23–23 | BEYOND |
| `launcher/orchard_launcher.py` | 285–285 | 285–285 | BEYOND |
| `launcher/orchard_launcher.py` | 325–325 | 325–325 | BEYOND |
| `launcher/orchard_launcher.py` | 330–330 | 330–333 | BEYOND |
| `launcher/orchard_results.py` | 14–15 | 14–15 | PATH/ENV |
| `launcher/return_io.py` | 1–1 | 1–1 | BEYOND |
| `launcher/return_io.py` | 48–49 | 48–48 | BEYOND |
| `launcher/s1.py` | None. | 1–338 | BEYOND |
| `launcher/trace_runtime.py` | 84–84 | 84–84 | BEYOND |
| `kit/rebind.py` is new on Trinity. | None. | 1–322 | BEYOND |
| `RUN.md` is new on Trinity. | None. | 1–81 | BEYOND |
| `tests/checker_fixture.py` is new on Trinity. | None. | 1–10 | BEYOND |
| `tests/line_capture.py` is new on Trinity. | None. | 1–22 | BEYOND |
| `tests/parity_fixture.py` is new on Trinity. | None. | 1–18 | BEYOND |
| `tests/rehearse.py` is new on Trinity. | None. | 1–130 | BEYOND |
| `tests/test_admission.py` is new on Trinity. | None. | 1–89 | BEYOND |
| `tests/test_rebind.py` is new on Trinity. | None. | 1–201 | BEYOND |


## ReVSI

| File | Accepted lines | Shipped lines | Class |
|---|---:|---:|---|
| The Trinity package prefix moves to `kit/revsi/`. | All paths. | All paths. | PATH/ENV |
| `launcher/export_stage.py` | None. | 1–224 | BEYOND |
| `launcher/gate.py` | None. | 1–120 | BEYOND |
| `launcher/orchard_job.py` | 188–188 | 188–191 | BEYOND |
| `launcher/orchard_job.py` | 197–197 | 200–200 | BEYOND |
| `launcher/orchard_job.py` | None. | 229–229 | BEYOND |
| `launcher/orchard_launcher.py` | 23–23 | 23–23 | BEYOND |
| `launcher/orchard_launcher.py` | 287–287 | 287–287 | BEYOND |
| `launcher/orchard_launcher.py` | 327–327 | 327–327 | BEYOND |
| `launcher/orchard_launcher.py` | 332–332 | 332–335 | BEYOND |
| `launcher/orchard_results.py` | 14–15 | 14–15 | PATH/ENV |
| `launcher/return_io.py` | 1–1 | 1–1 | BEYOND |
| `launcher/return_io.py` | 48–49 | 48–48 | BEYOND |
| `launcher/s1.py` | None. | 1–335 | BEYOND |
| `launcher/trace_runtime.py` | 84–84 | 84–84 | BEYOND |
| `kit/rebind.py` is new on Trinity. | None. | 1–322 | BEYOND |
| `RUN.md` is new on Trinity. | None. | 1–81 | BEYOND |
| `tests/checker_fixture.py` is new on Trinity. | None. | 1–10 | BEYOND |
| `tests/line_capture.py` is new on Trinity. | None. | 1–22 | BEYOND |
| `tests/parity_fixture.py` is new on Trinity. | None. | 1–18 | BEYOND |
| `tests/rehearse.py` is new on Trinity. | None. | 1–130 | BEYOND |
| `tests/test_admission.py` is new on Trinity. | None. | 1–89 | BEYOND |
| `tests/test_rebind.py` is new on Trinity. | None. | 1–201 | BEYOND |

