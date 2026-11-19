from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build21'
p=B/'native21.py';s=p.read_text().replace('from native_assets20 import','from native_assets21 import')
s=s.replace("O=B/'proofs/native'", "O=B/'proofs/capacity'")
s=s.replace("from monitor9 import Monitor", "from capacity_tools import guard, population, pose_manifests\nfrom monitor9 import Monitor")
s=s.replace("fp=file_pin(O/'f.png')", "(O/'data2root').mkdir(exist_ok=True);im.save(O/'data2root/f.png')\n    fp=dict(file_pin(O/'data2root/f.png'),path='/data2/f.png')")
s=s.replace("src=O/(stream+'.jsonl');src.write_text(json.dumps(r)+'\\n')", "src=O/(stream+'.jsonl');population(src,r,stream,guard)")
s=s.replace("pose_manifest=manifest_for_rows(O/'pose_source',[pose],'pose')\n    if not (O/'pose_store/receipt.json').exists():materialize([pose_manifest['path']],O/'pose_store',dense=False)", "pose_inputs=pose_manifests(O,pose,manifest_for_rows)\n    if not (O/'pose_store/receipt.json').exists():\n        guard('pose producer');materialize([p['path'] for p in pose_inputs],O/'pose_store',dense=False)")
s=s.replace("(O/'routing.jsonl').write_text(json.dumps(rr)+'\\n')", "population(O/'routing.jsonl',rr,'routing',guard)")
s=s.replace("R.build_routing_stream(file_pin(O/'routing.jsonl')", "guard('routing producer');R.build_routing_stream(file_pin(O/'routing.jsonl')")
s=s.replace("D.build_stream(file_pin(src)", "guard(stream+' producer');D.build_stream(file_pin(src)")
s=s.replace("for (encoded,) in db.execute('SELECT row FROM rows')", "for (encoded,) in db.execute('SELECT row FROM rows LIMIT 2000')")
# The fixture owns one fixed output tree. Repeated runs replace only its bytes.
s=s.replace("            cfg,model,mp,camera,depth,room=host()\n", "")
s=s.replace("            stack.enter_context(patch.dict(os.environ,STUDENT_R2_FRAME_HOST='1'))", "            stack.enter_context(patch.dict(os.environ,STUDENT_R2_FRAME_HOST='1'))\n            guard('host');cfg,model,mp,camera,depth,room=host()")
s=s.replace("                n=produce(cfg,model,mp,camera,depth,step)", "                guard('milestone '+str(step));n=produce(cfg,model,mp,camera,depth,step)")
s=s.replace("                summary.setdefault('twins',{})[str(step)]=twins(request,n,mp,root)", "                if os.environ.get('CAPACITY_TWINS')=='1':summary.setdefault('twins',{})[str(step)]=twins(request,n,mp,root)")
p.write_text(s)
