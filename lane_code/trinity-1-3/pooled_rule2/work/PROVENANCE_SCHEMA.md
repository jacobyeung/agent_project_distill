# PROVENANCE_SCHEMA: read manifest of the pooled harm rule (schema `pooled-rule-read-manifest-v1`)

Every read of a set that `pooled_harm_rule_v2.py` scores carries one manifest per set: dev-S1 (family `main`) and R0-dev (family `a7`). `build_manifest.py kit <read-kit build dir> <dev-S1|R0-dev> OUT.json` writes it from the read kit's own receipts; nobody types a manifest by hand.

## Fields

| Block | Field | Source receipt | May differ from the step-544 manifest |
|---|---|---|---|
| `run` | `run_id`, `step`, `artifact_sha256`, `artifact_path` | `fetched/x/SPEC.json` (`artifact.*`, `step`, `export_binding.run`) | yes: this block names the export |
| `run` | `orchard_job`, `read_token`, `plan_sha256` | `SUBMISSION.json`, `fetched/FETCH.json`, `fetched/x/COMPLETE.json` | yes: the read kit's plan hashes the export it reads, so job, token and plan change with run, artifact and step |
| `config` | `arm` | `SPEC.json` `scope` | no |
| `config` | `reader_package` (evaluator source digest, the accepted packet both read kits bind) | `<family>/a0/request.json` `source_sha256` | no |
| `config` | `decoding` (greedy, 32 frames duplicated, 16,384 tokens, thinking on, temperature 0, max_model_len 49,152, engine 0.32.0, budget 2048) | `request.json` | no |
| `config` | `selector_rule`, `scale_rule`, `tower_weights` | fixed text: the direct arm serves no call | no |
| `config` | `item_file_sha256` (dev-S1 `TASKS.jsonl` a2f3fdbd; R0-dev `e52a690b.jsonl` 1d8b29a7) | `request.json` `datasets.0.rows.sha256` or `items_sha256` | no |
| `config` | `rule_population` (items per rule type in the read) | counted from the read file | no |
| — | `type_filter` (`none` or `direct`) | `request.json` `types` | yes, through `rule_population` only: `direct` removes absolute distance and room size, which the rule does not read, so both values leave the same population; the tool checks that a `direct` read holds neither type |
| `read_file` | `path`, `sha256`; `archive` (`fetched/result.tar.gz` sha256, member `ITEMS.jsonl`) | `FETCH.json` `archive.sha256`, `status` | the read itself |
| `receipts` | per receipt: `path`, `sha256`, `binds` = pairs (receipt field, manifest field) | | |

## What the tool checks
1. Both manifests exist, have schema v1 and name their set and family.
2. Internal consistency: the artifact path is `.../runs/<run_id>/m<step>/artifact.json`; every receipt exists with its sha256 and every bound receipt field equals its manifest field; the read file is one of `--read` and, for a kit read, equals the archive's `ITEMS.jsonl` after the kit's identifier decoding (ID map sha256 in `ROOM_CROSSWALK.json` `sources.id_map`; the dev-S1 baseline `A544.jsonl` was assembled from the report rows of evalx read e193c2a3c, has no archive and is pinned by sha256 instead); the read's rows of the family carry the manifest's step and population.
3. Against the registered step-544 manifest of the set (`BASE_MANIFEST_<set>_544.json`, pinned by sha256 in the tool): `config` equal field for field.
4. Both manifests name one export (`run_id`, `artifact_sha256`, `step`), which is not the baseline artifact; a decision read is of run 673bc60f at `--step`.
5. One read per boundary and arm: the decision read appends one line per set to `--ledger` (step, arm, set, run, artifact, read sha256, manifest sha256). A later call for the same step, arm and set with another read file or manifest is refused; the identical read again is accepted and not logged twice.

## The two baseline manifests (from the real receipts)

### `BASE_MANIFEST_dev-S1_544.json` (sha256 e08a1d3427cf2adc31c96544d08913ed5ca173f7a08129a57f2d8759592a584b)
```json
{
 "config": {
  "arm": "direct",
  "decoding": {
   "budget": 2048,
   "decoding": "greedy",
   "engine_version": "0.32.0",
   "frames": 32,
   "layout": "duplicate",
   "max_model_len": 49152,
   "max_tokens": 16384,
   "temperature": 0,
   "thinking": true
  },
  "item_file_sha256": "a2f3fdbdab06ab81942d44044d85090df8ec5b86908cf010cdbcb17e35637f5e",
  "reader_package": "d27804f736545f7ebed6b55124b4bd215991695d96ed9106d82a142e91302aaa",
  "rule_population": {
   "object_counting": 150,
   "object_rel_direction_easy": 150,
   "object_rel_direction_hard": 150,
   "object_rel_direction_medium": 150,
   "object_rel_distance": 150,
   "object_size_estimation": 150,
   "route_planning": 150
  },
  "scale_rule": "none (direct arm)",
  "selector_rule": "none (direct arm: no call is served)",
  "tower_weights": "none (direct arm)"
 },
 "family": "main",
 "read_file": {
  "path": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/readk/evidence/A544.jsonl",
  "sha256": "8347cd843f47fe637e770e47544ad49b03e60909e5312260a305319150edb8be"
 },
 "receipts": [
  {
   "binds": [
    [
     "job",
     "run.orchard_job"
    ],
    [
     "packet",
     "run.read_token"
    ]
   ],
   "path": "/scratch/jjyeung/orch_n30/cont_ops/work/d0/readk/evidence/ACCEPTED.json",
   "sha256": "dc5f510b8d1ec5a44fa55077ed5f3cfb3a48820aa77dd6bf28ccc0b46ed302b5"
  },
  {
   "binds": [
    [
     "artifact.sha256",
     "run.artifact_sha256"
    ],
    [
     "artifact.path",
     "run.artifact_path"
    ],
    [
     "step",
     "run.step"
    ],
    [
     "scope",
     "config.arm"
    ]
   ],
   "path": "/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/SPEC.json",
   "sha256": "cb82e5177f1d03591695dc7b3849256a46c536e375a4c14eaabd599cdbab6760"
  },
  {
   "binds": [
    [
     "plan_sha256",
     "run.plan_sha256"
    ],
    [
     "step",
     "run.step"
    ],
    [
     "scope",
     "config.arm"
    ]
   ],
   "path": "/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/PLAN.json",
   "sha256": "ddcdcde02bf19f2d19d0840dd1aa5a5747b1cb23684ede1ac6679d58e5482a69"
  },
  {
   "binds": [
    [
     "source_sha256",
     "config.reader_package"
    ],
    [
     "datasets.0.rows.sha256",
     "config.item_file_sha256"
    ],
    [
     "max_tokens",
     "config.decoding.max_tokens"
    ],
    [
     "thinking",
     "config.decoding.thinking"
    ],
    [
     "temperature",
     "config.decoding.temperature"
    ],
    [
     "engine_version",
     "config.decoding.engine_version"
    ],
    [
     "cells.0.layout",
     "config.decoding.layout"
    ],
    [
     "cells.0.frames",
     "config.decoding.frames"
    ],
    [
     "legs1.artifact.sha256",
     "run.artifact_sha256"
    ]
   ],
   "path": "/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/main/results/budget_2048/request.json",
   "sha256": "ffb8f1fdb3ccd07b7f416401aab65c1bffa566628f42495a27e0a2470ddefaaf"
  }
 ],
 "run": {
  "artifact_path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/469ddece/m544/artifact.json",
  "artifact_sha256": "1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef",
  "orchard_job": 169526,
  "plan_sha256": "95779a355321c458712b55f5fe729ee90f8c2bde15b901df28ce8f74b6f9e793",
  "read_token": "e193c2a3c",
  "run_id": "469ddece",
  "step": 544
 },
 "schema": "pooled-rule-read-manifest-v1",
 "set": "dev-S1",
 "type_filter": "none"
}
```

### `BASE_MANIFEST_R0-dev_544.json` (sha256 86c8f993b5b799fc29f183bb295db136f2a4cac43c4ce8dbe10deb6656f530a1)
```json
{
 "config": {
  "arm": "direct",
  "decoding": {
   "budget": 2048,
   "decoding": "greedy",
   "engine_version": "0.32.0",
   "frames": 32,
   "layout": "duplicate",
   "max_model_len": 49152,
   "max_tokens": 16384,
   "temperature": 0,
   "thinking": true
  },
  "item_file_sha256": "1d8b29a7f7bb5c4e486f430b1128b9fa249de24ae7a3905b9bb0ccdd778c892b",
  "reader_package": "d27804f736545f7ebed6b55124b4bd215991695d96ed9106d82a142e91302aaa",
  "rule_population": {
   "obj_appearance_order": 246,
   "object_counting": 385,
   "object_rel_direction_easy": 192,
   "object_rel_direction_hard": 192,
   "object_rel_direction_medium": 194,
   "object_rel_distance": 279,
   "object_size_estimation": 293
  },
  "scale_rule": "none (direct arm)",
  "selector_rule": "none (direct arm: no call is served)",
  "tower_weights": "none (direct arm)"
 },
 "family": "a7",
 "read_file": {
  "archive": {
   "decode": "a7 and r0dev ids through ID_MAP.json (sha256 in ROOM_CROSSWALK.json sources.id_map)",
   "member": "ITEMS.jsonl",
   "path": "/scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/build/adff67f7ae9/fetched/result.tar.gz",
   "sha256": "334e1368605e982f5716977cfb89f298638a1799bd57f2e1d318e34848ad7025"
  },
  "fetch_status": "COMPLETE",
  "path": "/scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/build/adff67f7ae9/fetched/x/ITEMS.jsonl",
  "sha256": "a05c2318e038d6e19c368c309d8cba2cd31047fc6fd7ef124a7b8ac943565233"
 },
 "receipts": [
  {
   "binds": [
    [
     "job",
     "run.orchard_job"
    ],
    [
     "token",
     "run.read_token"
    ],
    [
     "status",
     "read_file.fetch_status"
    ],
    [
     "archive.sha256",
     "read_file.archive.sha256"
    ]
   ],
   "path": "/scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/build/adff67f7ae9/fetched/FETCH.json",
   "sha256": "41e77774952b3f5b210ffe6c9318833d41a0c106659d224c75b91e1aa7581a56"
  },
  {
   "binds": [
    [
     "job",
     "run.orchard_job"
    ],
    [
     "token",
     "run.read_token"
    ],
    [
     "plan_sha256",
     "run.plan_sha256"
    ]
   ],
   "path": "/scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/build/adff67f7ae9/SUBMISSION.json",
   "sha256": "bb298a8700934a6d8a6252c78e1bc9f1aecc25f97e7b91457b53eb7efe514cda"
  },
  {
   "binds": [
    [
     "artifact.sha256",
     "run.artifact_sha256"
    ],
    [
     "artifact.path",
     "run.artifact_path"
    ],
    [
     "step",
     "run.step"
    ],
    [
     "scope",
     "config.arm"
    ],
    [
     "export_binding.run",
     "run.run_id"
    ]
   ],
   "path": "/scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/build/adff67f7ae9/fetched/x/SPEC.json",
   "sha256": "ba40449f2c6c1bd25f7e8c84026b220591d72ccd0a1c8ef9e4925395de21eb01"
  },
  {
   "binds": [
    [
     "plan_sha256",
     "run.plan_sha256"
    ],
    [
     "step",
     "run.step"
    ]
   ],
   "path": "/scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/build/adff67f7ae9/fetched/x/COMPLETE.json",
   "sha256": "5959879b8444bac1756b640311801bd6c5f19f890bd8bc6bbeecbe335c6d3846"
  },
  {
   "binds": [
    [
     "source_sha256",
     "config.reader_package"
    ],
    [
     "items_sha256",
     "config.item_file_sha256"
    ],
    [
     "max_tokens",
     "config.decoding.max_tokens"
    ],
    [
     "thinking",
     "config.decoding.thinking"
    ],
    [
     "temperature",
     "config.decoding.temperature"
    ],
    [
     "engine_version",
     "config.decoding.engine_version"
    ],
    [
     "cells.0.layout",
     "config.decoding.layout"
    ],
    [
     "cells.0.frames",
     "config.decoding.frames"
    ]
   ],
   "path": "/scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/build/adff67f7ae9/fetched/x/a7/a0/request.json",
   "sha256": "c0b47c1416fb47026596f70bec3ec7bd54ac56f3118617b085dbceb0e2e240c3"
  }
 ],
 "run": {
  "artifact_path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/469ddece/m544/artifact.json",
  "artifact_sha256": "1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef",
  "orchard_job": 171197,
  "plan_sha256": "fdbb5196f5be35e7f4bdaef743acb0962d93724358d6d7697cc13cf3b160be52",
  "read_token": "adff67f7ae9",
  "run_id": "469ddece",
  "step": 544
 },
 "schema": "pooled-rule-read-manifest-v1",
 "set": "R0-dev",
 "type_filter": "direct"
}
```
