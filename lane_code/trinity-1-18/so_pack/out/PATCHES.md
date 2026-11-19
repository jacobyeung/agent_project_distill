# Patch bases and switches

Apply both diffs with `patch -p1` relative to the mirrored `orch_n30` root, which contains `cont_ops17/` and `cont_ops18/`. This dispatch never modifies that read-only root. Tested working copies live under `so_pack/work`.

| Patch | Effect | Default |
|---|---|---|
| `patches/01_pack_gate.diff` | Adds `pack.py`, `pack_probes.py`, and mutation/integration tests at the root. Existing builders are called as subprocesses. `all` preflights every phase before transfer; execution streams through `pv -L 8m`. | No action without `--enable`. Remote phases only print commands unless `--execute-remote`; submit also needs `--yes` and an explicit matching token. Fixed-token operational adaptation requires each source pin's `parameterize: true`. |
| `patches/02_explicit_builder_tokens.diff` | Adds the optional token branch to `cont_ops17/work/build_r10.py` and `cont_ops18/dbuild/build_d.py`, plus `test_builder_tokens.py`. | Original random-token behavior unless `SO_PACK_EXPLICIT_TOKEN=1`; token then comes from `SO_PACK_TOKEN`. The wrapper sets these only with an explicit token and `builder.explicit_token_switch: true`. r10 accepts exactly one of A/B in this mode. |

The D default-path test compares complete delivery bytes under identical deterministic fixture entropy. Both outputs match. The explicit D case runs a full build and validates all package descriptors. r10's unchanged default mint loop is compared as an AST, and its explicit mint branch is exercised with valid, invalid, and multi-package cases. A full r10 build is not claimed because the original SHA-pinned deliveries are absent.

Local receipts bind both package bytes and the checker sources. The `all` command validates all remote scripts before starting any transport, then executes exactly those planned bytes. A bad later script prevents every transfer; each attempted phase retains a no-retry marker. The copy-only transport test uses a local stub and does not contact Orchard.

Local builder copies are `work/builders/routed/build_r10.py` and `work/builders/d/build_d.py`. D's adjacent support files are byte-identical copies. `TOOL_SHA256.json` identifies delivered code. `work/patch_verified` contains a minimal input-tree copy on which both patches are applied and compared with the tested files.

Tests use Python 3.12 here. Production wrapper, probe and optional builder sources pass Python 3.6 grammar checks; no actual Python 3.6 runtime was invoked. The generated login script uses the Python 3.6 standard library. Remote scripts receive `bash -n` checks. A local copy-only transport stub tests stream integrity and the no-retry marker without SSH or remote execution.
