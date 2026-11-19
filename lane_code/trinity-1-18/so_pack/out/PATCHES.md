# Patch bases, switches and validation

Apply both unified diffs with `patch -p1` relative to the mirrored `orch_n30` root containing `cont_ops17/` and `cont_ops18/`. The patches add files only. Never replace native `build_d.py` or `build_r10.py` with the optional copies.

| Patch | Added files | Switch |
|---|---|---|
| `patches/01_pack_gate.diff` | Root `pack.py`, `pack_probes.py`, `test_pack.py`, `test_delivery.py` | Every action requires `--enable`; transport also requires `--execute-remote`, `--yes` and the matching explicit token. Planning submit requires `--yes` and the token too. |
| `patches/02_explicit_builder_tokens.diff` | Root `test_builder_tokens.py`; `cont_ops17/work/so_pack_builders/build_r10.py`; `cont_ops18/dbuild/so_pack_builders/{build_d.py,build_support.py,make_items_d.py}` | Builders retain random-token behavior unless `SO_PACK_EXPLICIT_TOKEN=1`. Pack enables it only with `--token` and `builder.explicit_token_switch: true`. |

Set `builder.path` to the added builder file and pin its SHA256. D's adjacent support files are identical to the native inputs. `gen400b.py`, native builders, `o_build_D.sh` and `check_release_d.py` retain their original bytes, so adding patch 02 does not invalidate embedded-builder equality.

`TOOL_SHA256.json` identifies the one delivered code set. `test_delivery.py` applies both patches to a minimal input fixture and compares all nine delivered files against that set. The final unit and builder suites run from the applied tree. Root sources, the `out/tool` alias and applied sources must agree; output paths are recorded in `REPORT.md`.

D's default full delivery is compared byte for byte under identical deterministic entropy, and its explicit-token path receives a full build. The native release checker runs under real Python 3.6.8 with its scratch fixture redirected inside L. Its asset fixture uses the exact authenticated bytes embedded in `o_build_D.sh`; the supplied mirror's pre-existing `score_d.py` mismatch is reported separately. r10 receives default-loop AST and explicit mint/rejection tests; its absent authenticated source archives prevent a full build.

The exact commands, measured results, complete raw logs and review mapping are in `REPORT.md`. Tests use local stubs for transport and scheduler replies. They never call ssh or Slurm.
