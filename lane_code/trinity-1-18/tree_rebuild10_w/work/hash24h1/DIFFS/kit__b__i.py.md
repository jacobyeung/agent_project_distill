# kit/b/i.py

All diffs read launch C as old and the rehearsal as new. Missing files are explicit.

run4: 5 launch lines removed; 4 rehearsal lines added. Functions: launch refresh; rehearsal refresh.

```diff

--- launch/kit/b/i.py
+++ run4/kit/b/i.py
@@ -17,18 +17,17 @@
     spec=cfg.get('s1_routing')
     if not spec:return request
     original=load(pinned(spec['selection']))
-    if original['implementation']==implementation() and normalized(original['remove_files'])==normalized(cfg['remove_files']):return request
+    if original['implementation']==implementation():return request
     root=Path(root);root.mkdir(parents=True,exist_ok=True)
     moved=relocate(spec['selection'],spec.get('catalog',{}),root/'p')
     before=load(pinned(moved['relocated']))
-    changed=normalized(before['remove_files'])!=normalized(cfg['remove_files'])
-    after=prepare(before['manifest'],root/'s',cfg['remove_files'],before['tokenizer'],before['room_sets'])
+    after=prepare(before['manifest'],root/'s',before['remove_files'],before['tokenizer'],before['room_sets'])
     for key in set(before)|set(after):
-        if key=='implementation' or changed:continue
+        if key=='implementation':continue
         if normalized(before.get(key))!=normalized(after.get(key)):raise ValueError('E86:'+key)
     spec['selection']=file_pin(root/'s/receipt.json')
     write(root/'c.json',cfg)
     pin=file_pin(root/'c.json');result=dict(request,config=pin)
     result['staged_pins']=[*request['staged_pins'],pin,spec['selection']]
-    write(root/'r.json',dict(status='PASS',source=original['implementation'],current=after['implementation'],same_selection=not changed,removals_regenerated=changed,config=pin))
+    write(root/'r.json',dict(status='PASS',source=original['implementation'],current=after['implementation'],same_selection=True,config=pin))
     return result

```

run5: 5 launch lines removed; 4 rehearsal lines added. Functions: launch refresh; rehearsal refresh.

```diff

--- launch/kit/b/i.py
+++ run5/kit/b/i.py
@@ -17,18 +17,17 @@
     spec=cfg.get('s1_routing')
     if not spec:return request
     original=load(pinned(spec['selection']))
-    if original['implementation']==implementation() and normalized(original['remove_files'])==normalized(cfg['remove_files']):return request
+    if original['implementation']==implementation():return request
     root=Path(root);root.mkdir(parents=True,exist_ok=True)
     moved=relocate(spec['selection'],spec.get('catalog',{}),root/'p')
     before=load(pinned(moved['relocated']))
-    changed=normalized(before['remove_files'])!=normalized(cfg['remove_files'])
-    after=prepare(before['manifest'],root/'s',cfg['remove_files'],before['tokenizer'],before['room_sets'])
+    after=prepare(before['manifest'],root/'s',before['remove_files'],before['tokenizer'],before['room_sets'])
     for key in set(before)|set(after):
-        if key=='implementation' or changed:continue
+        if key=='implementation':continue
         if normalized(before.get(key))!=normalized(after.get(key)):raise ValueError('E86:'+key)
     spec['selection']=file_pin(root/'s/receipt.json')
     write(root/'c.json',cfg)
     pin=file_pin(root/'c.json');result=dict(request,config=pin)
     result['staged_pins']=[*request['staged_pins'],pin,spec['selection']]
-    write(root/'r.json',dict(status='PASS',source=original['implementation'],current=after['implementation'],same_selection=not changed,removals_regenerated=changed,config=pin))
+    write(root/'r.json',dict(status='PASS',source=original['implementation'],current=after['implementation'],same_selection=True,config=pin))
     return result

```
