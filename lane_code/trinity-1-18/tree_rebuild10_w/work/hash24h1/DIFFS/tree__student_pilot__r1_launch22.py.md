# tree/student_pilot/r1_launch22.py

All diffs read launch C as old and the rehearsal as new. Missing files are explicit.

run4: 3 launch lines removed; 1 rehearsal lines added. Functions: launch <module>, validate_removals; rehearsal <module>, validate_removals.

```diff

--- launch/tree/student_pilot/r1_launch22.py
+++ run4/tree/student_pilot/r1_launch22.py
@@ -1,6 +1,5 @@
 """Pinned launch inputs for vehicle N; no inference behavior."""
 NAMING_REMOVE = 'd1454a4461e96fda9e0db27eb75fe0080a555d77a4d05f8e036d49530626db29'
-POINTING_K1_REMOVE = 'd21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1'
 REMOVAL_ORDER = (
     '62113ff38f918528341d3c38c6cce372736f2b44ca932c3b706be29397798dc3',
     '4701e195ffc04fe256b916a05eb0a669df6cf3f97d73c9986bfe5de3170b089c',
@@ -28,8 +27,7 @@
     if not isinstance(spec, dict):
         raise ValueError('R1_NAMING_REMOVAL_BINDING_REQUIRED')
     actual = [p['sha256'] for p in cfg.get('remove_files', [])]
-    if (tuple(actual) not in (REMOVAL_ORDER, REMOVAL_ORDER[:-1] + (POINTING_K1_REMOVE, NAMING_REMOVE))
-            or actual != spec.get('removal_order') or not actual or actual[-1] != NAMING_REMOVE
+    if (tuple(actual) != REMOVAL_ORDER or actual != spec.get('removal_order') or not actual or actual[-1] != NAMING_REMOVE
             or actual.count(NAMING_REMOVE) != 1):
         raise ValueError('R1_NAMING_REMOVAL_ORDER')
     from .p3_provenance import pinned

```

run5: 3 launch lines removed; 1 rehearsal lines added. Functions: launch <module>, validate_removals; rehearsal <module>, validate_removals.

```diff

--- launch/tree/student_pilot/r1_launch22.py
+++ run5/tree/student_pilot/r1_launch22.py
@@ -1,6 +1,5 @@
 """Pinned launch inputs for vehicle N; no inference behavior."""
 NAMING_REMOVE = 'd1454a4461e96fda9e0db27eb75fe0080a555d77a4d05f8e036d49530626db29'
-POINTING_K1_REMOVE = 'd21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1'
 REMOVAL_ORDER = (
     '62113ff38f918528341d3c38c6cce372736f2b44ca932c3b706be29397798dc3',
     '4701e195ffc04fe256b916a05eb0a669df6cf3f97d73c9986bfe5de3170b089c',
@@ -28,8 +27,7 @@
     if not isinstance(spec, dict):
         raise ValueError('R1_NAMING_REMOVAL_BINDING_REQUIRED')
     actual = [p['sha256'] for p in cfg.get('remove_files', [])]
-    if (tuple(actual) not in (REMOVAL_ORDER, REMOVAL_ORDER[:-1] + (POINTING_K1_REMOVE, NAMING_REMOVE))
-            or actual != spec.get('removal_order') or not actual or actual[-1] != NAMING_REMOVE
+    if (tuple(actual) != REMOVAL_ORDER or actual != spec.get('removal_order') or not actual or actual[-1] != NAMING_REMOVE
             or actual.count(NAMING_REMOVE) != 1):
         raise ValueError('R1_NAMING_REMOVAL_ORDER')
     from .p3_provenance import pinned

```
