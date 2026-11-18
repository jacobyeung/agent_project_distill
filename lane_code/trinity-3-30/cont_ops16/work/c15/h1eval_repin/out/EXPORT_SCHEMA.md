`a/export.json` uses schema `h1-export-pins-v1`. The operator owns this declaration. The package authenticates its exact bytes through `a/1.json`:

```json
"export_pin": {"path": "a/export.json", "sha256": "64 lowercase hex digits", "bytes": 1234}
```

The pin file contains these fields:

| Field | Contract |
|---|---|
| `schema` | Exactly `h1-export-pins-v1`. |
| `member_directory` | The observed relative export directory inside the archive. Absolute paths, `..`, and noncanonical paths refuse. |
| `lineage` | `SFT` or `RL`, carried unchanged into journal bindings and curves. |
| `step` | A nonnegative JSON integer; booleans refuse. |
| `artifact`, `heads`, `full_weights` | Each contains a full lowercase `sha256` and a positive integer `bytes`. They identify `artifact.json`, `heads.pt`, and `full_weights/full_weights.json` beneath `member_directory`. |
| `preparation` | Exactly three entries: `config`, `receipt`, and `data_receipt`. Each has `path`, `source_path`, `sha256`, and `bytes`. |

Preparation `path` is relative to `/scratch/jjyeung/b01ec87a6f29b/d`. The helper uses `p0/config.json`, `p0/receipt.json`, and `p0/data_receipt.json`. These paths are distinct and canonical. `source_path` preserves the original absolute identity: the config entry comes from `data_receipt.config.path`; the receipt entry comes from `config.preparation.path`. The data receipt's source path records its location beside the preparation directory and is informational. The data receipt's content hash remains mandatory.

Admission compares the three export hashes, byte counts, and resolved member paths with `a/1.json` before staging. Check, submit, and job admission all authenticate the pin file. The job authenticates actual export bytes while staging and preparation bytes during CPU restore. The pin file is operator input, not a signature or proof that an export is registered elsewhere.

The prepared config file's SHA256 differs from the training config identity in a receipt or artifact. For 544, the prepared file hashes to `78341acb…`, while `receipt.config_sha256` is `84ea03af…`. For H1-1, the prepared file hashes to `65519f6f…`; the supplied run binding reports `26a60a5c…`. The admission request's `9385cc71…` config is a separate input and must not replace the prepared config.

Restore retains the production data-receipt status/schema/flags and full config/preparation equality checks, receipt/artifact config identity, base identity, duplicate frame layout, geometry-online guard, original model authentication, full-weights schema/dtype, index membership, depth overwrite proof, and every weight hash. It additionally checks the three preparation byte counts and the receipt pin against `config.preparation`. Production treats absent `synthetic` as false and checks `geometry_online` with its existing truthiness guard; these semantics remain unchanged.

`export_544.json` contains the production export and preparation hashes and sizes. The package can populate its three preparation files from the sealed D0 metadata only when their hashes and sizes match exactly. Thus the production 544 input archives and policy paths work unchanged, with only the new `export_pin` reference added to `a/1.json`.

`export_TEMPLATE.json` deliberately contains invalid placeholders. Use `fill_export.py` to fill it from authenticated data. The helper requires the real preparation receipt; it cannot substitute `binding.json` for that receipt. It hashes the ordered archive stream and each part, checks `.done`, discovers the member directory, hashes the export metadata and weights, and checks preparation compatibility. It writes only the pin file, adapted inputs, and a small preparation tar. It never joins the large parts into a second archive on disk.
