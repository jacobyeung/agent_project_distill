from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build19'
p=B/'native19.py';s=p.read_text()
s=s.replace("prior=load(L/'work/build17/inputs/config.json')","prior=load(B/'inputs/config.json')")
s=s.replace("registry=prior['r1_training']['registry'])","registry=prior['r1_training']['registry'],component_rows=prior['r1_training']['component_rows'])")
s=s.replace("card.update(counting_admission='procedure_only_v1',weight_scale=.04)","card.update(counting_admission='procedure_only_v1',weight_scale=.04,vehicle='N',leg='R1')")
s=s.replace("job_id='fixture'","job_id='6ed2c7aa'")
p.write_text(s)
