# tree/student_pilot/r1_handover.py

All diffs read launch C as old and the rehearsal as new. Missing files are explicit.

run4: 9 launch lines removed; 1 rehearsal lines added. Functions: launch <module>, _donor, _same_pin_bytes; rehearsal _donor.

```diff

--- launch/tree/student_pilot/r1_handover.py
+++ run4/tree/student_pilot/r1_handover.py
@@ -318,13 +318,6 @@
     return _donor(cfg, artifact)
 
 
-def _same_pin_bytes(recorded, verified):
-    """Compare a recorded pin with a pin whose bytes the caller already verified."""
-    return (isinstance(recorded, dict) and set(recorded) == {'path', 'sha256'}
-            and isinstance(recorded['path'], str) and bool(recorded['path'])
-            and recorded['sha256'] == verified['sha256'])
-
-
 def _donor(cfg, artifact):
     """Read P's config, binding.json and preparation receipt, never a progress assertion."""
     value = cfg['r1_training']
@@ -353,8 +346,7 @@
     if not only and (complete.get('schema') != 'c1-checkpoint-v1' or complete.get('step') != artifact.get('step')
             or complete.get('binding') != bound):
         raise ValueError('P_EXPORT_CHECKPOINT_BINDING_MISMATCH')
-    if (not _same_pin_bytes(source.get('preparation'), pins['preparation'])
-            or not _same_pin_bytes(bound.get('preparation'), pins['preparation'])
+    if (source.get('preparation') != pins['preparation'] or bound.get('preparation') != pins['preparation']
             or bound.get('config_sha256') != identity or preparation.get('config_sha256') != identity
             or preparation.get('schema') != 'c1-preparation-v1'):
         raise ValueError('P_EXPORT_RUN_BINDING_MISMATCH')

```

run5: 9 launch lines removed; 1 rehearsal lines added. Functions: launch <module>, _donor, _same_pin_bytes; rehearsal _donor.

```diff

--- launch/tree/student_pilot/r1_handover.py
+++ run5/tree/student_pilot/r1_handover.py
@@ -318,13 +318,6 @@
     return _donor(cfg, artifact)
 
 
-def _same_pin_bytes(recorded, verified):
-    """Compare a recorded pin with a pin whose bytes the caller already verified."""
-    return (isinstance(recorded, dict) and set(recorded) == {'path', 'sha256'}
-            and isinstance(recorded['path'], str) and bool(recorded['path'])
-            and recorded['sha256'] == verified['sha256'])
-
-
 def _donor(cfg, artifact):
     """Read P's config, binding.json and preparation receipt, never a progress assertion."""
     value = cfg['r1_training']
@@ -353,8 +346,7 @@
     if not only and (complete.get('schema') != 'c1-checkpoint-v1' or complete.get('step') != artifact.get('step')
             or complete.get('binding') != bound):
         raise ValueError('P_EXPORT_CHECKPOINT_BINDING_MISMATCH')
-    if (not _same_pin_bytes(source.get('preparation'), pins['preparation'])
-            or not _same_pin_bytes(bound.get('preparation'), pins['preparation'])
+    if (source.get('preparation') != pins['preparation'] or bound.get('preparation') != pins['preparation']
             or bound.get('config_sha256') != identity or preparation.get('config_sha256') != identity
             or preparation.get('schema') != 'c1-preparation-v1'):
         raise ValueError('P_EXPORT_RUN_BINDING_MISMATCH')

```
