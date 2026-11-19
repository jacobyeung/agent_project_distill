from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build21'
p=B/'kit.py';s=p.read_text().replace('90a20c41','22c714e1')
s=s.replace("room=file_pin(L/'work/build18/inputs/room_audit.json')", "room=file_pin(B/'inputs/room_audit.json')")
s=s.replace("and path.stat().st_size<30_000_000:","and (path.stat().st_size<30_000_000 or h in ('8ec1efd2c1851fb856caa3631653390d76796f8c31cd8366d54df52916c7de82','15387646fd4ac47b43c107129db3109545a981c1bd45a3910ac038d8c5432022')):")
p.write_text(s)
p=B/'upload.py';p.write_text(p.read_text().replace('work/build20','work/build21').replace('90a20c41','22c714e1'))
p=B/'focused.py';p.write_text(p.read_text().replace('test20.py','test21.py'))
p=B/'jobtest.py';p.write_text(p.read_text().replace('90a20c41','22c714e1'))
