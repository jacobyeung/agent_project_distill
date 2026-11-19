from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build23'
s=(B/'native21.py').read_text().replace("O=B/'proofs/capacity'", "O=L/'work/build23/proofs/capacity'")
s=s.replace("str(T),str(B)", "str(L/'work/build23'),str(T),str(B)")
s=s.replace("from capacity_tools import", "from capacity23 import")
s=s.replace("import tempfile\ntempfile.tempdir", "import portable21c\nos.environ['B21C_PORTABLE']='1'\nportable21c.install()\nimport tempfile\ntempfile.tempdir")
s=s.replace("cfg['r1_training']['mix']=write(O/'card.json',card);cfg['r2_sampling']=binding", """card['cells'][2]['type']='routing_base'
    card['cells'].extend(dict(type=k,stream='routing',rows_per_step=0) for k in
        ('recovery','absolute_distance','units','coverage','coverage_distance','coverage_units','camera_wording'))
    cfg['r1_training']['mix']=write(O/'card.json',card)
    cfg['r1_training']['routing_slices']='deferred_first_boundary'
    cfg['r1_training'].pop('routing_inputs')
    pending=write(O/'pending_population.json',dict(schema='r1-population-v1',complete=False,
        after_all_filters=False,card_sha256=cfg['r1_training']['mix']['sha256'],
        counts={c['type']:0 for c in card['cells']},evidence=[cfg['r1_training']['mix']]))
    cfg['r2_sampling']=dict(schema='r1-sampling-v1',card=cfg['r1_training']['mix'],population=pending,
        indices=write(O/'pending_indices.json',dict(population_sha256=pending['sha256'],cells={c['type']:[] for c in card['cells']})))""")
s=s.replace("stack.enter_context(patch.dict(os.environ,STUDENT_R2_FRAME_HOST='1'))\n            guard('host');cfg,model,mp,camera,depth,room=host()", """guard('host')
            with patch.dict(os.environ,STUDENT_R2_FRAME_HOST='1'):
                cfg,model,mp,camera,depth,room=host()
            assert 'STUDENT_R2_FRAME_HOST' not in os.environ
            assert 'Q_E7' not in os.environ""")
s=s.replace("request=dict(config=config,staged_pins=staged,", "request=dict(config=config,routing_base=n['streams']['routing'],staged_pins=staged,")
s=s.replace("if os.environ.get('CAPACITY_TWINS')=='1':", "if os.environ.get('CAPACITY_TWINS')=='1':")
(D/'native23.py').write_text(s)
s=(B/'capacity_tools.py').read_text().replace("O=B/'proofs/capacity'", "O=L/'work/build23/proofs/capacity'")
s=s.replace("start=json.loads((B/'STORAGE_START.json').read_text())['workspace']", "start=json.loads((L/'work/build23/START.json').read_text())['workspace']")
s=s.replace("current-start>3_500_000_000", "current>2_900_000_000")
(D/'capacity23.py').write_text(s)
print('MINIMAL capacity harness ready; native host flag only produces the synthetic pose fixture.')
