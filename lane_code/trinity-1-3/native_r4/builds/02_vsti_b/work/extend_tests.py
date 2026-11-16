from pathlib import Path
p=Path('tests/test_v1b.py');s=p.read_text()
s=s.replace("self.assertEqual(old,new);self.assertEqual(diagnostics,other)","""self.assertEqual(old,new);self.assertEqual(diagnostics,other)
        def record(value,diag,path):return dict(native='c0',status=value['status'],error=value['error'],diagnostics=diag,output=pin(path),**value['data'])
        check=proof.compare_geometry({'records':[record(new,other,self.root/'new.npz')]},{'records':[record(old,diagnostics,output)]},self.root/'G.json')
        self.assertEqual(check['identical'],1)""")
s=s.replace("        dump(B/'out/RELEASE_CHECK_SYNTHETIC.json'", """        media=folder/'media.json';pins=folder/'pins.json'
        dump(media,{'scannet:a':{'frame_receipt':pin(selection)}});dump(pins,{'files':{'a':{'sha256':sha(video)}}})
        with patch.object(pixels,'SCENES',('a',)):
            actual=pixels.run(folder,folder.parent,media,pins,folder/'RESULT.json')
        self.assertEqual(actual['status'],'complete');self.assertEqual(actual['compared_frames'],32)
        dump(B/'out/RELEASE_CHECK_SYNTHETIC.json'""")
s=s.replace("self.assertEqual(b.projected('other'),12.5)","self.assertEqual(b.projected('other'),12.5);self.assertEqual(b.remaining(),120)")
s=s.replace("        calls=iter([True]*3+[False])", "        refs=load(B/'work/proof_reference.json');proof.compare(refs,refs,refs,root/'P0.json',True)\n        calls=iter([True]*3+[False])")
s=s.replace("first=engine.run(root/'i/BOUND.json',SPEC,geometry,root/'j0',boundary=Boundary())", "first=engine.run(root/'i/BOUND.json',SPEC,geometry,root/'j0',boundary=Boundary(),proof_path=root/'P0.json')")
pos=s.index('    def test_proof_type_counts')
s=s[:pos]+'''    def test_refused_geometry_is_scored(self):
        import geometry_refusals as GR
        root=self.root/'refused';b=prepare(R/'in/vsti/vstibench_repr_450_v3.json',R/'in/vsti/media.json',R/'in/vsti/frames_sample',root/'i',True)
        raw=engine.synthetic_tower(b,root/'raw');g=engine.prepare_geometry(b,SPEC,raw,root/'g',Boundary())
        manifest=load(g);manifest['videos']={}
        for r in manifest['records']:r.update(status='REFUSED',output=None,error=dict(code=GR.NONFATAL_CODE,message=GR.NONFATAL_CODE,exception='GeometryError'))
        dump(root/'REFUSED.json',manifest)
        result=engine.run(root/'i/BOUND.json',SPEC,root/'REFUSED.json',root/'j',boundary=Boundary())
        self.assertFalse(result['missing']);self.assertTrue(all(r['score']==0 and r['no_final_answer'] for r in rows(root/'j/items.jsonl')))
    def test_relocation_and_production_order(self):
        root=self.root/'relocate'
        b=prepare(R/'in/vsti/vstibench_repr_450_v3.json',R/'in/vsti/media.json',R/'in/vsti/frames_sample',root,True)
        updated=relocate_input(root,'/i');self.assertEqual(updated['frames_root'],'/i/store')
        for p in updated['inputs'].values():self.assertTrue(p['path'].startswith('/i/'))
        # Production validation checks fixed ordering independently of pixel staging.
        tasks=[dict(id='q'+str(t['id']),question_type=t['question_type']) for t in load(R/'in/vsti/vstibench_repr_450_v3.json')]
        target=self.root/'tasks.jsonl';target.write_text(''.join(json.dumps(t)+'\\n' for t in tasks))
        canary,post=order(tasks);b.update(synthetic=False,canary=canary,post_canary=post,keys=canary+post,inputs={'TASKS.jsonl':pin(target)})
        b['binding']=digest({k:v for k,v in b.items() if k!='binding'});dump(self.root/'B.json',b)
        self.assertFalse(validate_bound(self.root/'B.json')['synthetic'])
''' +s[pos:]
p.write_text(s)
p=Path('work/census.py');s=p.read_text().replace("'geometry':{'prepare_capture','prepare'}", "'geometry':{'prepare_capture','prepare'}")
s=s.replace("        if (p,line) in conditions:", """        if p.stem=='engine' and any(isinstance(n,ast.If) and ast.unparse(n.test)=='not boundary.synthetic' and any(c.lineno<=line<=c.end_lineno for c in n.body) for n in ast.walk(trees[p])):
            category='GPU decode';why='The real boundary invokes prompt/cache/head parity before scoring.'
        if p.stem=='entry' and line==6:category='venue staging (Trinity or Orchard)';why='READ_OVERLAY is set by the production namespace before numerical imports.'
        if (p,line) in conditions:""")
s=s.replace("    dead=statements[p]-live", "    guarded={line for n in ast.walk(trees[p]) if isinstance(n,ast.If) and '__name__' in ast.unparse(n.test) for line in range(n.lineno,n.end_lineno+1)} if p.stem not in ('entry','a','p','o','pixels') else set()\n    live-=guarded\n    dead=statements[p]-live")
s=s.replace("# The parity bridge executes", """# Rehearsal-observed owners add dynamic edges missed by static attribute resolution.
observed=set()
for name in sys.argv[1:]:
    if not any(x in name for x in ('rehearsal','cli_')) or not Path(name).is_file():continue
    data=coverage.CoverageData(basename=name);data.read()
    for filename in data.measured_files():
        p=Path(filename)
        if p in trees:
            observed.update(line_owner[p,n] for n in data.lines(filename) or [] if (p,n) in line_owner)
queue=deque(observed-reachable)
while queue:
    key=queue.popleft()
    if key in reachable:continue
    reachable.add(key);queue.extend(edges[key]-reachable)
# The parity bridge executes""")
s=s.replace("coverage=evidence,counts=", "rehearsal_observed_owners=sorted(observed),coverage=evidence,counts=")
p.write_text(s)
