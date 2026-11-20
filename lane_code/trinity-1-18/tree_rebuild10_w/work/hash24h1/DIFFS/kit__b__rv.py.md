# kit/b/rv.py

All diffs read launch C as old and the rehearsal as new. Missing files are explicit.

run4: 60 launch lines removed; 6 rehearsal lines added. Functions: launch <module>, evidence, keys, matches, protected_rooms, run, strip_frames; rehearsal evidence, run, strip_frames.

```diff

--- launch/kit/b/rv.py
+++ run4/kit/b/rv.py
@@ -99,9 +99,8 @@
 
 def strip_frames(value):
     if isinstance(value, dict):
-        return {k: strip_frames(v) for k, v in value.items()
-                if not (k in {'frame', 'frames', 'frame_index', 'frame_indices', 'frame_id',
-                              'timestamp', 'timestamps'} or '_frame' in k)}
+        return {k: strip_frames(v) for k, v in value.items() if k not in
+                {"frames", "partner_frames", "frame_indices", "frame_index", "timestamps", "timestamp", "partner_frame_indices", "partner_timestamps"}}
     if isinstance(value, list):
         return [strip_frames(v) for v in value]
     return value
@@ -125,40 +124,6 @@
         if value is not None:
             return field, str(value)
     return "not_recorded", "not_recorded"
-
-
-def protected_rooms(cfg):
-    from student_pilot.r1_rooms import Rooms
-    from student_pilot.s1_exclusions import dev_names, benchmark_names, Exclusions
-    from student_pilot.p3_provenance import pinned
-    authority=Rooms(cfg['r1_training']['room_authority'])
-    rule=Exclusions(cfg['dev_scene_exclusions'],cfg['benchmark_scene_exclusions'])
-    def keys(name):
-        ds,scene=name.split('/',1)
-        ds={'d1':'scannet','d2':'scannetpp','d3':'arkitscenes'}.get(ds,ds)
-        canonical,_=authority.canonical({'canonical':ds+'/'+scene})
-        found={rule.key(name),rule.key(canonical)}
-        try:found.add(rule.key(authority.room(canonical)))
-        except ValueError:pass
-        return found
-    lists={};payloads={}
-    for label,field,reader,name in (
-        ('bench_v2','benchmark_scene_exclusions',benchmark_names,'e6.json'),
-        ('dev_s1','dev_scene_exclusions',dev_names,'e7.json')):
-        pin=cfg[field];raw=pinned(pin).read_bytes()
-        lists[label]=dict(names=set().union(*(keys(n) for n in reader(pin))),sha256=pin['sha256'],file=name)
-        payloads[name]=raw
-    from sv import classifier
-    classify=classifier(cfg)
-    def matches(row,stream):
-        try:flags=classify(row,stream)
-        except ValueError as error:
-            from student_pilot.s1_scene_census import SceneCoverageError
-            if not isinstance(error,SceneCoverageError) and not str(error).startswith(('R1_CENSUS_ROOM_UNRESOLVED:', 'R1_TWIN_ROOM_UNRESOLVED', 'R1_ROOM_CANONICAL_UNRESOLVED')):
-                raise
-            raise ValueError('R1_PROTECTED_ROOM_UNRESOLVED') from error
-        return dict(bench_v2=flags['benchmark'],dev_s1=flags['dev'])
-    return lists,payloads,matches
 
 
 def evidence(cfg, rooms, live):
@@ -170,7 +135,7 @@
         torch.set_num_interop_threads(1)
     receipt = load(pinned(cfg["preparation"]))
     reader = Rows(receipt, None)
-    protected, payloads, room_matches = protected_rooms(cfg)
+    payloads = {}
     counts = {}
     started = time.monotonic()
     try:
@@ -190,25 +155,21 @@
             types = Counter()
             forms = Counter()
             empty = 0
-            room_counts = dict.fromkeys(protected,0)
             databases = []
             for key, connection in connections.items():
                 database = Path(next(r[2] for r in connection.execute("PRAGMA database_list") if r[1] == "main"))
                 databases.append(dict(source=key, path=str(database), sha256=sha(database), bytes=database.stat().st_size))
             for offset, row_id in enumerate(ids):
                 row, _ = reader.row(stream, offset)
-                for label,hit in room_matches(row,stream).items():room_counts[label] += int(hit)
                 types[str(row.get("routing", {}).get("question_type", row.get("question_type", "not_recorded")))] += 1
                 field, value = form(row)
                 forms[(field, value)] += 1
                 empty += not bool(reasoning(row).strip())
                 if row_id in wanted:
                     examples[row_id] = dict(row_id=row_id, row=strip_frames(row))
-            counts[stream] = dict(rows=total, answer_only=empty, protected_rooms=room_counts)
+            counts[stream] = dict(rows=total, answer_only=empty)
             payloads[NAMES[stream]] = encoded(dict(stream=stream, databases=databases, admitted_rows=total,
                 question_types=dict(sorted(types.items())), answer_only=empty,
-                protected_rooms={label:dict(rows=room_counts[label],sha256=v["sha256"],file=v["file"]) for label,v in protected.items()},
-                canonical_room_reader="sv.classifier: native stream room authority and exclusion-list readers",
                 reasoning_field="reasoning when present; otherwise target/suffix <think> body; missing body counts empty",
                 trace_forms=[dict(field=f, value=v, rows=n) for (f, v), n in sorted(forms.items())],
                 trace_form_basis="routing.form is canonical producer form; form is the stored trace form; answer_form selects native encoding; absent fields are not_recorded",
@@ -222,9 +183,7 @@
         raise ValueError("R1_REVIEW_EVIDENCE_TOO_LARGE")
     for name, raw in payloads.items():
         put(live / name, raw)
-    if any(any(v["protected_rooms"].values()) for v in counts.values()):
-        raise ValueError("R1_PROTECTED_ROOM_ROWS")
-    if any(counts[stream]["answer_only"] for stream in ("vqa","routing")):
+    if any(v["answer_only"] for v in counts.values()):
         raise ValueError("R1_ANSWER_ONLY_ROWS")
     return dict(counts=counts, bytes=sum(map(len, payloads.values())), seconds=time.monotonic() - started)
 
@@ -255,20 +214,7 @@
             raise ValueError("R1_REVIEW_CONFIG_TOO_LARGE")
         put(live / "v.json", raw)
         put(live / "identity.txt", (value + "\n").encode())
-        try:
-            evidence(cfg, root / "rooms.json", live)
-        except ValueError as error:
-            from cs import discovery
-            if not discovery(kit) or not str(error).startswith(('R1_PROTECTED_ROOM','R1_SCENE_PROTECTED')):
-                raise
-            put(live/'d5.json',encoded(dict(status='WOULD_REFUSE',refusal=str(error),config_identity=value)))
-        if cfg.get('remove_files'):
-            from cs import verify as verify_census
-            pin=verify_census(kit,root,cfg)
-            from z import checked
-            checked(live/'h0.json',cfg['r1_training']['host_receipt']['sha256'])
-            if load(cfg['r1_training']['host_receipt']['path']).get('protected_census')!=pin:
-                raise ValueError('R1_CENSUS_RECEIPT_PIN_DIFFERS')
+        evidence(cfg, root / "rooms.json", live)
         bound = load(kit / "k/a.json")["review_wait_seconds"]
         if type(bound) is not int or not 0 < bound <= 7200:
             raise ValueError("R1_REVIEW_FILE_UNUSABLE")

```

run5: 29 launch lines removed; 10 rehearsal lines added. Functions: launch evidence, matches, protected_rooms, run, strip_frames; rehearsal evidence, matches, run, strip_frames.

```diff

--- launch/kit/b/rv.py
+++ run5/kit/b/rv.py
@@ -99,9 +99,8 @@
 
 def strip_frames(value):
     if isinstance(value, dict):
-        return {k: strip_frames(v) for k, v in value.items()
-                if not (k in {'frame', 'frames', 'frame_index', 'frame_indices', 'frame_id',
-                              'timestamp', 'timestamps'} or '_frame' in k)}
+        return {k: strip_frames(v) for k, v in value.items() if k not in
+                {"frames", "partner_frames", "frame_indices", "frame_index", "timestamps", "timestamp", "partner_frame_indices", "partner_timestamps"}}
     if isinstance(value, list):
         return [strip_frames(v) for v in value]
     return value
@@ -148,16 +147,11 @@
         pin=cfg[field];raw=pinned(pin).read_bytes()
         lists[label]=dict(names=set().union(*(keys(n) for n in reader(pin))),sha256=pin['sha256'],file=name)
         payloads[name]=raw
-    from sv import classifier
-    classify=classifier(cfg)
-    def matches(row,stream):
-        try:flags=classify(row,stream)
-        except ValueError as error:
-            from student_pilot.s1_scene_census import SceneCoverageError
-            if not isinstance(error,SceneCoverageError) and not str(error).startswith(('R1_CENSUS_ROOM_UNRESOLVED:', 'R1_TWIN_ROOM_UNRESOLVED', 'R1_ROOM_CANONICAL_UNRESOLVED')):
-                raise
-            raise ValueError('R1_PROTECTED_ROOM_UNRESOLVED') from error
-        return dict(bench_v2=flags['benchmark'],dev_s1=flags['dev'])
+    def matches(row):
+        canonical,_=authority.canonical(row)
+        if not canonical:raise ValueError('R1_PROTECTED_ROOM_UNRESOLVED')
+        values=keys(canonical)
+        return {label:bool(values & item['names']) for label,item in lists.items()}
     return lists,payloads,matches
 
 
@@ -197,7 +191,7 @@
                 databases.append(dict(source=key, path=str(database), sha256=sha(database), bytes=database.stat().st_size))
             for offset, row_id in enumerate(ids):
                 row, _ = reader.row(stream, offset)
-                for label,hit in room_matches(row,stream).items():room_counts[label] += int(hit)
+                for label,hit in room_matches(row).items():room_counts[label] += int(hit)
                 types[str(row.get("routing", {}).get("question_type", row.get("question_type", "not_recorded")))] += 1
                 field, value = form(row)
                 forms[(field, value)] += 1
@@ -208,7 +202,7 @@
             payloads[NAMES[stream]] = encoded(dict(stream=stream, databases=databases, admitted_rows=total,
                 question_types=dict(sorted(types.items())), answer_only=empty,
                 protected_rooms={label:dict(rows=room_counts[label],sha256=v["sha256"],file=v["file"]) for label,v in protected.items()},
-                canonical_room_reader="sv.classifier: native stream room authority and exclusion-list readers",
+                canonical_room_reader="student_pilot.r1_rooms.Rooms.canonical and Rooms.room; native exclusion-list readers",
                 reasoning_field="reasoning when present; otherwise target/suffix <think> body; missing body counts empty",
                 trace_forms=[dict(field=f, value=v, rows=n) for (f, v), n in sorted(forms.items())],
                 trace_form_basis="routing.form is canonical producer form; form is the stored trace form; answer_form selects native encoding; absent fields are not_recorded",
@@ -255,20 +249,7 @@
             raise ValueError("R1_REVIEW_CONFIG_TOO_LARGE")
         put(live / "v.json", raw)
         put(live / "identity.txt", (value + "\n").encode())
-        try:
-            evidence(cfg, root / "rooms.json", live)
-        except ValueError as error:
-            from cs import discovery
-            if not discovery(kit) or not str(error).startswith(('R1_PROTECTED_ROOM','R1_SCENE_PROTECTED')):
-                raise
-            put(live/'d5.json',encoded(dict(status='WOULD_REFUSE',refusal=str(error),config_identity=value)))
-        if cfg.get('remove_files'):
-            from cs import verify as verify_census
-            pin=verify_census(kit,root,cfg)
-            from z import checked
-            checked(live/'h0.json',cfg['r1_training']['host_receipt']['sha256'])
-            if load(cfg['r1_training']['host_receipt']['path']).get('protected_census')!=pin:
-                raise ValueError('R1_CENSUS_RECEIPT_PIN_DIFFERS')
+        evidence(cfg, root / "rooms.json", live)
         bound = load(kit / "k/a.json")["review_wait_seconds"]
         if type(bound) is not int or not 0 < bound <= 7200:
             raise ValueError("R1_REVIEW_FILE_UNUSABLE")

```
