# kit/b/z.py

All diffs read launch C as old and the rehearsal as new. Missing files are explicit.

run4: 13 launch lines removed; 13 rehearsal lines added. Functions: launch <module>, bootstrap, copy_resolved_payload, stage_payload; rehearsal bootstrap, stage_payload.

```diff

--- launch/kit/b/z.py
+++ run4/kit/b/z.py
@@ -446,7 +446,7 @@
             out.extend(b);self.digest.update(b);self.n+=len(b)
         return bytes(out)
 
-def copy_resolved_payload(kit,resolved,root):
+def stage_payload(kit,resolved,root):
     kit=Path(kit);root=Path(root);spec=load(kit/'k/p.json')
     if resolved['kit_sha256']!=seal(kit):raise ValueError('E32')
     if spec.get('step',400)==400:
@@ -477,8 +477,8 @@
         source=checked(entry['path'],entry['sha256'],entry['bytes'])
         with source.open('rb') as a,(u/entry['sha256']).open('wb') as b:shutil.copyfileobj(a,b,8<<20)
     source=load(kit/'k/a.json')['source'];shutil.copyfile(kit/source['path'],root/'t.tar')
-    (root/'source_code.json').write_bytes(base64.b64decode(load_raw(kit/'k/c0.json')['payload']))
-    if sha(root/'source_code.json')!=spec['code_sha256']:raise ValueError('E34')
+    (root/'c.json').write_bytes(base64.b64decode(load_raw(kit/'k/c0.json')['payload']))
+    if sha(root/'c.json')!=spec['code_sha256']:raise ValueError('E34')
     for part in resolved['parts']:checked(part['path'],part['sha256'],part['bytes'])
     stream=Joined(resolved['parts']);export=root/'e';export.mkdir(exist_ok=True)
     with tarfile.open(fileobj=stream,mode='r|*') as t:
@@ -500,7 +500,7 @@
         if h not in resolved['small_files']:
             if h not in byhash:raise ValueError('E37:'+label)
             os.link(byhash[h],u/h) if not (u/h).exists() else checked(u/h,h)
-    ns=resolved['_namespace']
+    ns=spec['namespace']
     # The native reader opens the manifest and its siblings by their export names.
     mp=receipt['pins']['full_weights'];manifest=load(checked(u/mp['sha256'],mp['sha256']))
     native=root/'w';native.mkdir(exist_ok=True)
@@ -512,14 +512,14 @@
         source=checked(u/h,h);target=inside(native,name)
         if target.exists():checked(target,h)
         else:os.link(source,target)
-    return None
-
-# Compatibility entry for resolver refusal tests; production uses pl.plan_payload.
-def stage_payload(kit,resolved,root):
-    for item in resolved['small_files'].values():
-        selected400(item.get('original',item.get('member','')))
-        selected400(item.get('member',''))
-    raise ValueError('R1_NATIVE_STAGING_HOOK_REQUIRED')
+        resolved['paths'][h]=ns+'/w/'+name
+        resolved['config']['r1_training']['persisted_files'][h]=ns+'/w/'+name
+    cfgpin=write(root/'n.json',resolved['config'])
+    request=resolved['request'];request['config']=dict(cfgpin,path=ns+'/n.json')
+    request['staged_pins'].append(request['config']);request['_paths']=resolved['paths']
+    request['_paths'].update(resolved['config']['r1_training']['persisted_files'])
+    write(root/'r.json',request)
+    return request
 
 def load_raw(path):return json.loads(Path(path).read_text())
 
@@ -599,7 +599,7 @@
     boot_code=base64.b64decode(load_raw(boot_kit/'k/j.json')['payload'])
     if hashlib.sha256(boot_code).hexdigest()!=load_raw(boot_kit/'k/j.json')['sha256']:raise ValueError('E38')
     (boot_node/'j.sh').write_bytes(boot_code)
-    write(boot_node/'r.json',dict(_resolved=boot_resolved))
+    stage_payload(boot_kit,boot_resolved,boot_node)
     return launch_shell(str(boot_node/'j.sh'),str(boot_node),str(boot_kit),boot_spec['namespace'],str(boot_hx),str(boot_node/'j'))
 
 def launch_shell(shell_file,env_node,env_kit,env_namespace,env_home,env_directory):

```

run5: IDENTICAL to launch.
