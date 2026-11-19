# Filter coverage

The supplied filter admits ordinary `sb_*`, `so_*`, and `swarm_*` lane directories.
The prefix alone does not guarantee admission: every ancestor must pass the name, substring,
and entry-count checks. No new lane-prefix rule is needed.

| Path/name | Current rule | Consequence |
|---|---|---|
| `in/`, `out/`, `work/tree/`, `kit/` | Eligible directory names | Whitelisted source below these paths is considered. |
| `*_proof/`, names ending in `proof` or `proofs` | `DIRRE` | Entire subtree is skipped, including source. |
| `runs/`, `evidence/` | `DIRRE` | Entire subtree is skipped, including scripts and tests. |
| `clone/`, `tmp*`, `retained_*`, `rows_*`, `results/`, `artifacts/`, mutation/env/cache names | `DIRRE` | Entire subtree is skipped. The exact expression remains in the supplied filter. |
| Any directory containing `frames` | Explicit name test | Entire subtree is skipped. |
| `out/devin_traces`, `/dl/`, `/root/`, `/envs/`, `site-packages`, `__pycache__`, `.cache`, `node_modules` | `SUBSTR` | Matching directory or file paths are skipped. |
| Directory with more than 2000 direct entries | `MAXDIR` | Entire subtree is skipped, including a lane root. The filter does not apply this check to its own working directory. |
| `.py`, `.sh`, `.md`, `.json`, `.jsonl`, `.yaml`, `.yml`, `.toml`, `.cfg`, `.txt`, `.patch`, `.diff`, `.tpl`, `.ini`, `.tsv` | `EXT` | Eligible; other extensions are skipped. |
| Any eligible file above 524288 bytes | `MAXB` | Skipped. Exactly 524288 bytes remains eligible. |
| `.json`/`.jsonl` above 262144 bytes | `DATA_MAXB` | Skipped. Exactly 262144 bytes remains eligible. |
| Symlinked file | Explicit link test | Skipped; directory links are not followed. |
| Identical content | SHA1 deduplication | Hourly snapshots keep one path and a dedup manifest. Kit landing restores all eligible paths. |

These rules come from `in/lane_code_filter.py:6–14`, directory traversal at lines 18–31,
and file selection at lines 32–49. Synthetic tests exercise the requested directory names,
size caps, duplicate paths, and the MAXDIR gate. Names such as `so_proof`, `sb_cache`, and
`swarm_frames` are excluded despite their lane prefixes.

The available mirror is
`/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt`.
Measured: it holds 40 files; the current filter selects 35 files totaling 100853 bytes.
No mirrored `.py` or `.sh` file is excluded by a directory rule or size cap. Three log/output
files are excluded by extension. Two files contain shell source but use an excluded extension:

| File | Measured bytes | Reason |
|---|---:|---|
| `work/prompts/tick.sh.copy` | 5757 | `.sh.copy` is absent from `EXT`. |
| `work/prompts/tick2.sh.copy` | 9812 | `.sh.copy` is absent from `EXT`. |

The smallest filter change is to add only `.sh.copy` to `EXT`. Patch
`03_shell_copy_coverage_optional.diff` does this behind `LCS_INCLUDE_SHELL_COPIES=1`, default OFF.
Measured on this mirror: enabled selection is 37 files / 116422 bytes, adding exactly those two
files. With the switch unset, stdout and stderr match the original filter byte for byte.
No broad directory exception or cap increase is proposed. Publishing an approved snapshot with
a normal `.sh` suffix also needs no filter change.

The owner sets the optional switch in the hourly process environment for local trinity-3-30
selection. The current remote script does not forward that environment variable over SSH;
remote opt-in would need an explicit owner change and has not been implemented. Kit filtering
and dry counting inherit the command's local environment.

The mirror contains no `sb_*` or `so_*` lane folders. Their actual inventories, ancestor entry
counts, and skipped source cannot be measured from the allowed inputs. The owner must run
`dry_count.sh` on explicit authorized folders on the node that holds them before new coverage
is pushed. Running it on an empty or incomplete mirror cannot establish remote coverage.
Per-folder counts are upper bounds on additive hourly totals because hourly content deduplication
spans all lanes. Counts do not scan secrets or prove review acceptance; the landing path does.
