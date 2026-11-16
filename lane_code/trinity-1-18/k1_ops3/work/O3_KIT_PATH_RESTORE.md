# O3_KIT_PATH_RESTORE (k1_ops3, 2026-11-15, ORCH ruling 20:05Z)

Created /scratch/jjyeung/orch_cd/o3_cache/work/kit (did not exist) as a copy of the kit_k1a/native_kit files that DEPENDENCIES.json pins and that the import closure of bindings.py, pipeline.py and vendor_sam/vendor/score_and_aggregate_orchard.py reaches (AST over all import statements, resolved in native_kit, native_kit/vendor_sam, native_kit/vendor_sam/vendor). Each file was verified against its pin before and after the copy; the copies are read-only (0444).
The original folder was lost with trinity-2-18 and could not be compared.

| file (relative to o3_cache/work/kit) | sha256 (= DEPENDENCIES.json pin of kit_k1a/native_kit/<file>) |
|---|---|
| bindings.py | 945ffbb8d0b7d5d9eda36ef7959469b2e222fb9cf758d7c7e4fd2acf55ebc553 |
| pipeline.py | ef68b2cdd96c8b12ba066940552d8d7bbbb059e49ed7958a7e988973113f6544 |
| vendor_sam/cache_masks.py | e1a2730e4566b555a9129fcdce06ff1290d9916fc2d0f9a59cadbf8f1fb0629c |
| vendor_sam/kitlib.py | c377025b67e7bf83da516e110d79566ce937c6806500f62796a937d0da92a244 |
| vendor_sam/variant_cache.py | cb702acdd4e88a47f1ce7d8556ecce0c54936382422e94c031b9d83b5e02a284 |
| vendor_sam/variantlib.py | 10219e028f26caa5d6cf76e42e6739f8ebd68204faf135874974e593d5440198 |
| vendor_sam/vendor/common.py | 3ba40b93d8ff0a8e2715222108ca3abfd2a57f0bf9ec82345a2bcae83038dd90 |
| vendor_sam/vendor/phrase.py | e0f429bfb8fbd013570fea3ede806d051516ad7c6e380561f5061168b756863c |
| vendor_sam/vendor/sam3_tower.py | 617d5c8daa31ee2de62efe5c93ed32f50203805006dce5bb75d9959a16e4decb |
| vendor_sam/vendor/sam_backend.py | 356802c9c86c79975a479fab84227ab14fedd67910239760cb4456e8c9c15d3c |
| vendor_sam/vendor/score_and_aggregate_orchard.py | 0bb536ca2eb60eaee54c2f18ed93103a41ff61db1bcbec1c36e5273f3b1ef2a1 |
| vendor_sam/vendor/stub_backend.py | a311ac4fc353a3948c05db4b6054c8a2652c3e7c9f0b4f4859b80ad3807678b4 |
| vendor_sam/vendor/tplib.py | a33ea2d7278536143167437055790671ddd94a618f8e1da2b885481b25a7e9b2 |

Notes: bindings.source_identity() hashes HERE/*.py of whichever bindings module is imported first in a process; in k1_pipeline.py processes native_kit is imported first (k1_pipeline.py:7), so cache receipts carry native_kit identities. vendor score_and_aggregate_orchard.py looks for canonical_cell_ids.json beside itself; it is absent in native_kit too (the function then returns None), so behaviour is the same at both paths.
