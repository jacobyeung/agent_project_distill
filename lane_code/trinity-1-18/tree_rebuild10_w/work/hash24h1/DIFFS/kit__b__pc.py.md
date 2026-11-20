# kit/b/pc.py

All diffs read launch C as old and the rehearsal as new. Missing files are explicit.

run4: 1 launch lines removed; 1 rehearsal lines added. Functions: launch __init__; rehearsal __init__.

```diff

--- launch/kit/b/pc.py
+++ run4/kit/b/pc.py
@@ -60,7 +60,7 @@
         self.claims = self.target/'o'/'gcs_claims'
         self.checkpoint = self.target/'n_ck'/self.job
         self.spool = self.root/'live_spool'
-        self.train = Path(train) if train else self.root/'p/q/r'
+        self.train = Path(train) if train else self.root/'r'
         self.sessions = Path(sessions) if sessions is not None else (Path(home)/'sess.json' if home is not None else self.target/'n_s/sess.json')
         self.home = self.sessions.parent
         self.writer = Path(writer) if writer else self.kit/'b/gc.py'

```

run5: IDENTICAL to launch.
