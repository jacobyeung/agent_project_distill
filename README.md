# SPLIT distillation

This repository contains the SPLIT distillation code for REQ-20260917-232: teacher collection, ground-truth adapters, materialization wrappers, conversion, dataset packaging, student pilot training, and RGB-only evaluation. Data, model weights, traces, targets, checkpoints, and run outputs stay under `/data2/jjyeung/agent_project_data/`, outside Git.

Remote: `git@github.com:jacobyeung/agent_project_distill.git`.

## Development and provenance

The user ruling of 2026-09-18 makes this a conventional, frequently committed code repository. Fix code in place and commit each logical change. Every run, trace, and target must record the repository commit and exact config SHA-256. Launches must refuse a dirty tree, and code changes take effect only at a run-epoch boundary. Require one independent review only for changes to admission, legality, or scoring; operational glue needs a smoke test.

The main repository at `/home/jjyeung/agent_project` remains authoritative for experiment requests and benchmark scoring. Its immutable-round rule still governs benchmark-scored packages there. The sealed source packages are preserved history, not editable working copies.

## Layout

| Path | Contents |
|---|---|
| `collector/` | The r1315 tolerant-pool and sparse-grounding candidate, copied verbatim and explicitly pre-remediation. |
| `gt_adapters/scannetpp_multilabel/` | ScanNet++ multilabel changes and tests relative to the r1313 baseline. |
| `gt_adapters/scannet_v1/`, `gt_adapters/scannet_v2/` | ScanNet adapter changes and tests. These are delta directories, not complete sealed packages. |
| `gt_adapters/arkit/` | Available ARKit adapter source and tests. |
| `gt_adapters/adt/` | A placeholder; no ADT implementation is included. |
| `materialize/` | Three config-matched wrapper variants, without runtime artifacts. Read its README before use. |
| `student/landing/` | The converter and clean-source branch, plus the dataset-builder patch and its required audit support module. |
| `student/eval-harness/` | The evaluation branch with its launcher and DSI option-formatting fixes. |
| `student/shakedown/` | The diagnostic shakedown snapshot and its preserved history. |
| `tools/provenance.py` | Prints commit/config provenance and returns nonzero for dirty or invalid checkouts. |
| `docs/` | Design, feasibility, and handoff references. |
| `PROVENANCE.md` | Exact import sources, pins, exclusions, validation results, and missing inputs. |

The student directories are separate Python module roots. Run a component from its own directory; do not put all three `student_pilot` packages on one Python path.

## Validation

Use Python 3.12, disable bytecode and GPUs, and keep test fixtures in a fresh directory under `/data2`. The available student environment is `/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/venv/bin/python`; the imported requirements files record its dependencies.

From the repository root:

```sh
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=""
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
TEST_ROOT="/data2/jjyeung/agent_project_data/distillation_checks/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$TEST_ROOT"
export PROVENANCE_TEST_OUTPUT="$TEST_ROOT/provenance"
python -B -m unittest tools/test_provenance.py
python -B -m unittest discover -s collector -p 'test_*.py'
```

The baseline collector command reports missing `pytest` and `SPARSE_FIXTURE_ROOT` requirements. It is not a full pytest run or evidence that the review findings are fixed. `PROVENANCE.md` records the exact result.

Portable student checks:

```sh
STUDENT_PYTHON=/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918/venv/bin/python
export STUDENT_CONVERTER_TEST_OUTPUT="$TEST_ROOT/converter"
export STUDENT_DATASET_TEST_OUTPUT="$TEST_ROOT/datasets"
(cd student/landing && "$STUDENT_PYTHON" -B -m unittest discover -s tests -p 'test_conversion_v2*.py' -v)
(cd student/landing && "$STUDENT_PYTHON" -B -m unittest discover -s tests -p 'test_dataset_builder.py' -v)
(cd student/landing && "$STUDENT_PYTHON" -B -m unittest discover -s tests -p 'test_dataset_loader.py' -v)
(cd student/eval-harness && PYTHONPATH=tests "$STUDENT_PYTHON" -B -m unittest test_benchmark_eval.ParserTests test_benchmark_eval.SamplingTests -v)
```

The native dataset integration fixture requires both its runtime code and outputs beneath one explicitly admitted workspace. Validate it from a Git archive staged under `/data2`; do not widen the admission boundary to `/` or relax the checker. Full student and materialization suites also depend on external source artifacts and model libraries. The assembly's validation record distinguishes completed checks from incomplete ones.

## Launch boundary

Run `python -B tools/provenance.py /absolute/path/to/config.json` and require exit 0 before launching. Persist its JSON in the new run root and propagate `repo_commit` and `config_sha256` to every trace and target. See `CONTRIBUTING.md` for the full contract.

The imported entry points retain source-deployment paths and sealed-contract assumptions; the provenance helper does not automatically wrap them. This baseline is not production launch approval. Collector remediation remains separate, ADT is a placeholder, and the dedicated Qwen3.5 and full-scale trainer patches were unavailable. Do not infer benchmark eligibility or training success from an import, a syntax check, or a CPU test.
